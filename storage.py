"""Rating storage: an Excel workbook or an SQLite database with the same layout.

Both have a players table (steamid | elo | name) and a matches table with one row per
player per match (MATCH_HEADER). SteamIDs are stored as text, because 17 digit numbers
don't survive being stored as numbers in Excel.
"""
import logging
import os
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

try:
    import openpyxl
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
except ImportError:
    openpyxl = None

log = logging.getLogger("melon")

PLAYER_HEADER = ["steamid", "elo", "name"]
MATCH_HEADER = ["match_id", "processed_at", "game", "map", "demo", "steamid", "name", "team",
                "team_score", "opponent_score", "result", "rounds", "kills", "assists", "deaths",
                "damage", "utility_damage", "enemies_flashed", "performance", "elo_before", "elo_after"]


def _outdated():
    return RuntimeError("it was made by an older version of csgoMELON. Rename or delete it and rate the demos again.")


def _ratings(path, found):
    """{steamid: elo} from (where, steamid, elo); elos that aren't numbers are left out."""
    ratings = {}
    for where, sid, elo in found:
        try:
            ratings[sid] = int(elo)
        except (TypeError, ValueError):
            log.warning(f"{path}: {where} has no valid elo ({elo!r}), treating {sid} as new")
    return ratings


def _match_rows(match, changes):
    processed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for p in match.players:
        c = changes[p.steamid]
        own, opponent = (match.score_t, match.score_ct) if p.team == "T" else (match.score_ct, match.score_t)
        result = "draw" if match.winner is None else "win" if match.winner == p.team else "loss"
        yield [match.match_id, processed_at, match.game, match.map_name, match.demo, p.steamid, p.name, p.team,
               own, opponent, result, p.rounds, p.kills, p.assists, p.deaths, p.damage, p.utility_damage,
               p.enemies_flashed, c.performance, c.before, c.after]


class SqliteStorage:
    """A dry run works on an in-memory copy of the database."""

    def __init__(self, path, dry_run=False):
        self.path, self.conn = path, sqlite3.connect(":memory:" if dry_run else path)
        if dry_run and os.path.exists(path):
            with closing(sqlite3.connect(path)) as saved:
                saved.backup(self.conn)
        for table, header in (("players", PLAYER_HEADER), ("matches", MATCH_HEADER)):
            if [row[1] for row in self.conn.execute(f"PRAGMA table_info({table})")] not in ([], header):
                raise _outdated()
        with self.conn:
            self.conn.execute("CREATE TABLE IF NOT EXISTS players (steamid TEXT PRIMARY KEY, elo INTEGER, name TEXT)")
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS matches ({', '.join(MATCH_HEADER)},"
                              " PRIMARY KEY (match_id, steamid))")

    def has_match(self, match_id):
        return self.conn.execute("SELECT 1 FROM matches WHERE match_id = ?", (match_id,)).fetchone() is not None

    def get_ratings(self, steamids):
        marks = ", ".join("?" * len(steamids))
        found = self.conn.execute(f"SELECT 'player ' || steamid, steamid, elo FROM players WHERE steamid IN ({marks})",
                                  steamids)
        return _ratings(self.path, found)

    def save_match(self, match, changes):
        try:
            with self.conn:  # one transaction: either everything is saved or nothing
                self.conn.executemany("INSERT OR REPLACE INTO players VALUES (?, ?, ?)",
                                      [(p.steamid, changes[p.steamid].after, p.name) for p in match.players])
                self.conn.executemany(f"INSERT INTO matches VALUES ({', '.join('?' * len(MATCH_HEADER))})",
                                      _match_rows(match, changes))
        except sqlite3.Error as e:
            raise RuntimeError(f"can't write {self.path}: {e}") from e


def _write(cell, value):
    if isinstance(value, str):
        cell.value = ILLEGAL_CHARACTERS_RE.sub("", value)  # control characters can't be saved
        cell.data_type = "s"  # text even if it starts with "=", which would make it a formula
        cell.number_format = "@"  # and Excel keeps it text (and SteamIDs unrounded) when it's edited
    else:
        cell.value = value


class XlsxStorage:
    """The workbook is kept in memory and written after every match; a dry run never writes it."""

    def __init__(self, path, players_sheet="Players", matches_sheet="Matches", dry_run=False):
        if openpyxl is None:
            raise RuntimeError("the xlsx storage needs openpyxl: pip install openpyxl")
        self.path, self.players, self.matches, self.dry_run = path, players_sheet, matches_sheet, dry_run
        self.wb = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            wb = openpyxl.Workbook()
            wb.active.title = self.players
            wb.active.append(PLAYER_HEADER)
            wb.create_sheet(self.matches).append(MATCH_HEADER)
            return wb
        wb = openpyxl.load_workbook(self.path)
        for sheet, header in ((self.players, PLAYER_HEADER), (self.matches, MATCH_HEADER)):
            if sheet not in wb.sheetnames or [c.value for c in wb[sheet][1]][:len(header)] != header:
                raise _outdated()
        for row, (sid,) in enumerate(self._column(wb, self.players), 2):
            if sid is not None and not isinstance(sid, str):
                raise RuntimeError(f"the SteamID in row {row} of sheet {self.players} is a number, which Excel may "
                                   "have rounded. Type it in again as text (start it with ').")
        return wb

    @staticmethod
    def _column(wb, sheet, col=1):
        return wb[sheet].iter_rows(min_row=2, min_col=col, max_col=col, values_only=True)

    def _rows(self):
        """{steamid: first row} on the players sheet; spaces around hand-edited SteamIDs are ignored."""
        rows = {}
        for row, (sid,) in enumerate(self._column(self.wb, self.players), 2):
            rows.setdefault(str(sid).strip(), row)
        return rows

    def has_match(self, match_id):
        return any(value == match_id for value, in self._column(self.wb, self.matches))

    def get_ratings(self, steamids):
        sheet = self.wb[self.players]
        return _ratings(self.path, ((f"row {row}", sid, sheet.cell(row, 2).value)
                                    for sid, row in self._rows().items() if sid in steamids))

    def save_match(self, match, changes):
        try:
            players, matches = self.wb[self.players], self.wb[self.matches]
            rows = self._rows()
            for p in match.players:
                row = rows.setdefault(p.steamid, players.max_row + 1)
                for col, value in enumerate((p.steamid, changes[p.steamid].after, p.name), 1):
                    _write(players.cell(row, col), value)
            for row, values in enumerate(_match_rows(match, changes), matches.max_row + 1):
                for col, value in enumerate(values, 1):
                    _write(matches.cell(row, col), value)
            if not self.dry_run:
                self._save()
        except Exception:
            self.wb = self._load()  # forget the match, so it isn't saved with the next one
            raise

    def _save(self):
        # write a temporary file first so a crash can't leave a half written workbook
        tmp = self.path + ".tmp"
        try:
            self.wb.save(tmp)
            if os.path.exists(self.path):
                shutil.copymode(self.path, tmp)
            os.replace(tmp, self.path)
        except PermissionError as e:
            raise RuntimeError(f"can't write {self.path}, is it open in Excel?") from e
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
