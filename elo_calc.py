"""Elo maths of csgoMELON.

A match is rated like a game between two players: a team's rating is the average of its
players' ratings, the usual Elo formula gives its expected score, and the team wins or
loses K * (score - expected score) points per player. Whatever one team wins, the other
team loses. The points are split between the players by rounds played and performance:
on the team that gains points, better performances get a bigger share; on the team that
loses points, worse performances lose a bigger share.
"""
import math
from typing import NamedTuple

K = 20  # points per player for a win in an even match: K * (1 - 0.5)

# How much performance changes a player's share of the team's points:
# 0 = every player gets the same share, 1 = shares are proportional to performance
PERFORMANCE_IMPACT = 1.0

# The performance score compares a player's per-round stats with the average of the match
# (1 = average). Each part counts at most MAX_PERFORMANCE times the average, and the score
# is clamped between MIN_PERFORMANCE and MAX_PERFORMANCE.
PERFORMANCE_WEIGHTS = {
    "kills": 0.35,     # kills + assists / 2 per round
    "damage": 0.30,    # damage per round (includes grenade and fire damage)
    "survival": 0.20,  # share of rounds survived
    "utility": 0.15,   # utility damage + FLASH_VALUE per enemy flashed, per round
}
FLASH_VALUE = 15
MIN_PERFORMANCE = 0.3
MAX_PERFORMANCE = 3


class RatingChange(NamedTuple):
    before: int
    after: int
    performance: float


def performances(players):
    """Performance score of every player of the match, in the same order."""
    parts = [{"kills": p.kills + p.assists / 2, "damage": p.damage, "survival": max(p.rounds - p.deaths, 0),
              "utility": p.utility_damage + FLASH_VALUE * p.enemies_flashed} for p in players]
    lobby_rounds = sum(p.rounds for p in players)
    lobby = {k: sum(part[k] for part in parts) / lobby_rounds if lobby_rounds else 0 for k in PERFORMANCE_WEIGHTS}
    scores = []
    for p, part in zip(players, parts):
        score = 0  # added up in order: sum() rounds floats differently since Python 3.12
        for k, w in PERFORMANCE_WEIGHTS.items():
            # a part nobody had in the whole match counts as average for everyone
            score += w * (min(part[k] / max(p.rounds, 1) / lobby[k], MAX_PERFORMANCE) if lobby[k] > 0 else 1)
        scores.append(min(max(score, MIN_PERFORMANCE), MAX_PERFORMANCE))
    return scores


def rate_match(match, ratings, start_elo):
    """{steamid: RatingChange} for every player; players without a rating start at start_elo.
    The changes add up to exactly 0."""
    elo = {p.steamid: ratings.get(p.steamid, start_elo) for p in match.players}
    performance = dict(zip(elo, performances(match.players)))
    team_t, team_ct = match.team("T"), match.team("CT")
    expected_t = 1 / (1 + 10 ** ((_team_rating(team_ct, elo) - _team_rating(team_t, elo)) / 400))
    score_t = 0.5 if match.winner is None else float(match.winner == "T")
    # average number of players per team on the server, 5 for a normal 5v5
    player_rounds = sum(p.rounds for p in match.players)
    players = player_rounds / (2 * match.rounds) if match.rounds and player_rounds else len(match.players) / 2
    points = round(K * players * (score_t - expected_t))

    changes = {}
    for team, total in ((team_t, points), (team_ct, -points)):
        for p, delta in zip(team, _split(total, _shares(team, performance, gaining=total > 0))):
            changes[p.steamid] = RatingChange(elo[p.steamid], elo[p.steamid] + delta, round(performance[p.steamid], 2))
    return changes


def _weights(team):
    """Rounds played by every player of a team, or equal weights if nobody has any."""
    rounds = [p.rounds for p in team]
    return rounds if sum(rounds) else [1] * len(team)


def _team_rating(team, elo):
    weights = _weights(team)
    return sum(elo[p.steamid] * n for p, n in zip(team, weights)) / sum(weights)


def _shares(team, performance, gaining):
    """How much of the team's points every player gets (not normalised). The team that gains
    points rewards good performances, the team that loses points spares them."""
    weights = _weights(team)
    value = [performance[p.steamid] if gaining else 1 / performance[p.steamid] for p in team]
    average = sum(n * v for n, v in zip(weights, value)) / sum(weights)
    return [n * (1 - PERFORMANCE_IMPACT + PERFORMANCE_IMPACT * v / average) for n, v in zip(weights, value)]


def _split(total, shares):
    """Splits an integer total by shares into integers that add up to it (largest remainder)."""
    exact = [total * s / sum(shares) for s in shares]
    result = [math.floor(x) for x in exact]
    for i in sorted(range(len(exact)), key=lambda i: (result[i] - exact[i], i))[:total - sum(result)]:
        result[i] += 1
    return result
