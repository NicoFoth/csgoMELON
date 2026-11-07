"""Reads a finished match out of a CS2 or CS:GO demo: teams, score, winner and player stats.

Parsers by LaihoE: demoparser2 for CS2, demoparser 0.4.0 for CS:GO (Python <= 3.11 only).
Teams are named after the side they finished the match on: a player is on team "T" if
their team played the last round as terrorists, even if they started as CTs.
"""
from __future__ import annotations

import bz2
import hashlib
import importlib
import logging
import math
import os
import shutil
import sys
import tempfile
from collections import namedtuple
from dataclasses import dataclass, replace

log = logging.getLogger("melon")

GAMES = ("cs2", "csgo")
MAGIC = {b"PBDEMS2\x00": "cs2", b"HL2DEMO\x00": "csgo"}  # first bytes of an uncompressed demo
SIDES = {2: "T", 3: "CT"}  # team_num -> side
OTHER = {"T": "CT", "CT": "T"}
# round end reasons; older demos give their numbers, newer CS2 demos their names
DRAW, GAME_COMMENCING = 10, 16  # GAME_COMMENCING ends the warmup
SURRENDER_WINNER = {17: "CT", 18: "T"}  # "T surrendered" and "CT surrendered"
REASONS = {"draw": DRAW, "game_start": GAME_COMMENCING, "t_surrender": 17, "ct_surrender": 18}
# The final scoreboard is read up to END_DELAY ticks after the win panel, but before the first
# death after the win panel and the first disconnect after the last round, because CS2 still
# counts those deaths (and one for a player who leaves alive). CS:GO only updates the score
# and the last kill up to 4 ticks after the win panel.
END_DELAY = 64
STATS_DELAY = {"cs2": 0, "csgo": 4}
TICK_WINDOW = 8  # CS:GO demos only contain every 2nd tick or fewer: use the closest earlier one
EVENTS = ("cs_win_panel_match", "round_end", "player_death", "player_disconnect")
STATS = ("kills", "assists", "deaths", "damage", "utility_damage", "enemies_flashed")
# parser props for side and STATS
PROPS = {
    "cs2": ["team_num", "kills_total", "assists_total", "deaths_total", "damage_total",
            "utility_damage_total", "enemies_flashed_total"],
    "csgo": ["team_num", "kills", "assists", "deaths", "total_damage", "total_util_damage",
             "total_enemies_flashed"],
}

RoundEnd = namedtuple("RoundEnd", "tick winner reason")  # winner: "T", "CT" or None for a draw


class DemoError(Exception):
    """The demo can't be used for a rating update."""


@dataclass
class Player:
    steamid: str
    name: str
    side: str | None  # "T", "CT" or None (spectator, disconnected, ...) at the parsed tick
    kills: int
    assists: int
    deaths: int
    damage: int  # to enemies, capped at their health; includes utility_damage
    utility_damage: int
    enemies_flashed: int
    team: str = ""  # "T" or "CT": the side the player's team finished the match on
    rounds: int = 0  # round ends the player was on their team for


@dataclass
class MatchResult:
    match_id: str  # sha256 of the uncompressed demo
    demo: str  # file name
    game: str
    map_name: str
    rounds: int
    score_t: int
    score_ct: int
    winner: str | None  # "T", "CT" or None for a draw
    players: list

    def team(self, name):
        return [p for p in self.players if p.team == name]


def _num(value):
    """A parser value as int; missing values (None, NaN) become 0."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0
    return 0 if math.isnan(value) else int(value)


def _steamid(value):
    """The SteamID64 as a string; None for bots and for floats, which have lost precision."""
    try:
        return str(int(value)) if not isinstance(value, float) and int(value) > 0 else None
    except (TypeError, ValueError):
        return None


def read_demo(path, game, recorded=lambda match_id: False):
    """Reads the match of a .dem or .dem.bz2 file, or returns None if recorded(match_id) says
    it's known already. The match id is the sha256 of the uncompressed demo, so the same
    match is recognised whichever of the two is imported."""
    with open(path, "rb") as f:
        compressed = f.read(3) == b"BZh"
    if not compressed:
        return _read(path, path, game, recorded)
    fd, tmp = tempfile.mkstemp(suffix=".dem")
    try:
        with os.fdopen(fd, "wb") as out, bz2.open(path) as src:
            shutil.copyfileobj(src, out, 1 << 20)
        return _read(tmp, path, game, recorded)
    finally:
        os.remove(tmp)


def _round_end(event):
    winner, reason = event.get("winner"), event.get("reason")
    return RoundEnd(_num(event.get("tick")), winner if winner in OTHER else SIDES.get(_num(winner)),
                    REASONS.get(reason, _num(reason)))


def _read(file, path, game, recorded):
    sha256 = hashlib.sha256()
    with open(file, "rb") as f:
        found = MAGIC.get(f.read(8))
        f.seek(0)
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256.update(chunk)
        f.seek(max(f.tell() - 6, 0))
        stopped = f.read(1) == b"\x07"  # a finished CS:GO recording ends with a 6 byte stop frame
    if found is None:
        raise DemoError(f"{path} is not a CS:GO or CS2 demo")
    if recorded(sha256.hexdigest()):
        return None
    label = "CS2" if game == "cs2" else "CS:GO"
    if found != game:
        raise DemoError(f"this is a {'CS2' if found == 'cs2' else 'CS:GO'} demo but GAME is set to {game!r}")
    if game == "csgo" and sys.version_info >= (3, 12):
        raise DemoError("reading CS:GO demos needs the demoparser package, which only supports "
                        f"Python 3.11 or older (this is Python {sys.version_info.major}.{sys.version_info.minor})")
    if game == "csgo" and not stopped:  # the CS:GO parser crashes the whole program on those
        raise DemoError("the demo is cut off or damaged (it doesn't end like a finished recording)")
    package, pip = ("demoparser2", "demoparser2") if game == "cs2" else ("demoparser", "demoparser==0.4.0")
    try:
        parser = importlib.import_module(package).DemoParser(file)
    except ImportError as e:
        raise DemoError(f"reading {label} demos needs {package}: pip install {pip}") from e
    try:
        map_name = str(parser.parse_header().get("map_name", "")).strip("\x00")
        if game == "cs2":
            events = {name: df.to_dict("records") for name, df in parser.parse_events(list(EVENTS))}
        else:  # every call parses the whole demo
            events = {name: parser.parse_events(name) or [] for name in EVENTS}
        ticks = {name: [_num(e.get("tick")) for e in events.get(name, [])] for name in EVENTS}
        if not ticks["cs_win_panel_match"]:
            raise DemoError("the match never finished (no win panel in the demo)")
        win_tick = min(ticks["cs_win_panel_match"])
        all_rounds = sorted(map(_round_end, events.get("round_end", [])), key=lambda r: r.tick)
        candidates = [r for r in all_rounds if r.tick <= win_tick and r.reason != GAME_COMMENCING]
        last_end = max([r.tick for r in candidates], default=win_tick)
        disconnects = [_num(e.get("tick")) for e in events.get("player_disconnect", [])
                       if _steamid(e.get("user_steamid" if game == "cs2" else "player_steamid"))]
        post_match = ([t - 1 for t in disconnects if t > last_end]
                      + [t - 1 for t in ticks["player_death"] if t > win_tick])
        first = last_end + STATS_DELAY[game]  # the stats are final from here on
        end_tick = max(first, min([win_tick + END_DELAY] + post_match))

        # player rows at the end, around every round end and right before every disconnect
        targets = {r.tick for r in candidates} | {t - 1 for t in disconnects if t <= last_end}
        wanted = {t for target in targets for t in range(max(0, target - TICK_WINDOW), target + 1)}
        wanted |= set(range(first, end_tick + 1))
        df = parser.parse_ticks(PROPS[game] + ["total_rounds_played"], ticks=sorted(wanted))
    finally:
        del parser  # demoparser2 keeps the demo mapped while it exists, and Windows can't delete a mapped file
    if df is not None and len(df) and game == "csgo" and "steamid" in df.columns:
        df = df.drop_duplicates(["tick", "steamid"])  # this parser can return a player twice for a tick
    rows, rounds_played = {}, {}  # {tick: {steamid: Player}}, {tick: rounds played}
    for rec in df.to_dict("records") if df is not None and len(df) else []:
        tick = _num(rec.get("tick"))
        rounds_played[tick] = max(rounds_played.get(tick, 0), _num(rec.get("total_rounds_played")))
        steamid, name = _steamid(rec.get("steamid")), rec.get("name")
        if steamid:
            rows.setdefault(tick, {})[steamid] = Player(
                steamid, name if isinstance(name, str) else steamid, SIDES.get(_num(rec.get(PROPS[game][0]))),
                *(_num(rec.get(prop)) for prop in PROPS[game][1:]))

    def closest(available, target):
        return max((t for t in available if target - TICK_WINDOW <= t <= target), default=None)

    # the last scoreboard, which may be a little before end_tick if the recording stops early
    end = max((t for t in rounds_played if first <= t <= end_tick), default=None)
    if end is None:
        raise DemoError("the demo stops before the final scoreboard")
    if rounds_played[end] <= 0:
        raise DemoError("no rounds were played")
    # Going back from the end, round n is the last round end with n - 1 rounds played before it.
    # That skips warmup, knife and restarted rounds, and rounds undone by loading a backup.
    rounds, count = [], rounds_played[end]
    for r in reversed(candidates):
        if count and rounds_played.get(closest(rounds_played, r.tick - 1)) == count - 1:
            rounds.insert(0, r)
            count -= 1
    if count:
        raise DemoError(f"the demo reports {rounds_played[end]} rounds but only {len(rounds)} of them were found")
    # anything before the end of the previous phase (warmup, restart) is not part of the match
    match_start = max([r.tick for r in all_rounds if r.tick < rounds[0].tick], default=-1)
    snapshot_ticks = {r.tick for r in rounds} | {t - 1 for t in disconnects if match_start < t <= last_end}
    snapshots = {t: rows.get(closest(rows, t), {}) for t in sorted(snapshot_ticks)}
    return _build_match(rounds, snapshots, end, rows.get(end, {}), match_id=sha256.hexdigest(),
                        demo=os.path.basename(path), game=game, map_name=map_name)

def _build_match(rounds, snapshots, end_tick, end, **info):
    """Works out teams, score and winner from the round ends, the players at every round end
    and before every disconnect ({tick: {steamid: Player}}) and the players at the end."""
    anchors = {sid: p.side for sid, p in end.items() if p.side}
    if not anchors:
        raise DemoError("no players are on a team at the end of the match")
    timeline = {**snapshots, end_tick: end}
    # 1 if the teams were on the same sides as at the end, -1 if swapped, 0 if unknown
    orientation = {}
    for tick, snap in timeline.items():
        same = [snap[sid].side == side for sid, side in anchors.items() if sid in snap and snap[sid].side]
        orientation[tick] = (2 * sum(same) > len(same)) - (2 * sum(same) < len(same))

    def team_at(tick, sid):
        """The end side of the team sid was on at tick, or None."""
        p = timeline[tick].get(sid)
        if p and p.side and orientation[tick]:
            return p.side if orientation[tick] > 0 else OTHER[p.side]
        return None

    players = []
    for sid in sorted({sid for snap in timeline.values() for sid in snap}):
        last = timeline[max(t for t in timeline if sid in timeline[t])][sid]  # at the end, or when they left
        teams = [team_at(r.tick, sid) for r in rounds]
        team = next(filter(None, reversed(teams)), None)  # their team at the last round end they had one
        if team is None:
            if any(getattr(timeline[r.tick].get(sid), "side", None) for r in rounds):
                log.warning(f"can't tell which team {last.name} ({sid}) played for, ignoring them")
            continue  # otherwise a spectator, coach or someone who wasn't on a team when a round ended
        # a player who switched teams is only rated for their rounds with the last one (in CS2 the damage
        # of their last round before the switch is only added after that round, so it stays with them)
        start = max((i + 1 for i, t in enumerate(teams) if t == OTHER[team]), default=0)
        on_team = teams[start:].count(team)
        if start:
            before = timeline[rounds[start - 1].tick][sid]
            last = replace(last, **{k: max(getattr(last, k) - getattr(before, k), 0) for k in STATS})
            log.warning(f"{last.name} ({sid}) switched teams, only their {on_team} rounds with team {team} are rated")
        players.append(replace(last, team=team, rounds=on_team))
    for side in ("T", "CT"):
        if not any(p.team == side for p in players):
            raise DemoError(f"team {side} has no players")

    score = {"T": 0, "CT": 0}
    for r in rounds:
        if r.winner is None and r.reason != DRAW:
            raise DemoError(f"can't tell who won the round ending at tick {r.tick}")
        if r.winner:
            if not orientation[r.tick]:
                raise DemoError(f"can't tell which team won the round ending at tick {r.tick}")
            score[r.winner if orientation[r.tick] > 0 else OTHER[r.winner]] += 1
    winner = None if score["T"] == score["CT"] else max(score, key=score.get)
    if rounds[-1].reason in SURRENDER_WINNER:  # the other team wins regardless of the score
        winner = SURRENDER_WINNER[rounds[-1].reason]
        winner = winner if orientation[rounds[-1].tick] > 0 else OTHER[winner]
    return MatchResult(rounds=len(rounds), score_t=score["T"], score_ct=score["CT"], winner=winner,
                       players=players, **info)
