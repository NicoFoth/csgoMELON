# 🍉csgoMELON🍉
CS:GO MELON (MELON for the ELO and because they're delicious) is an elo calculation tool for Counter-Strike 2 and Counter-Strike: Global Offensive.
It reads the demo (`.dem`) of a finished match, works out the teams, the score and every player's stats (kills, assists, deaths, damage and utility), and updates everyone's elo. The ratings are stored in an Excel file or an SQLite database.

## 🙋🏼‍♂️Introduction🙋🏼‍♂️
We looked for a way to retrieve data from our private matches and calculate an elo value based on that, to build a leaderboard showing the long-term performance of every player.
The first version used Valve's Game State Integration, which meant someone had to sit in every match as a spectator. Now it works on demo files, so nobody has to give up their spot, and matches can be rated after the fact.

## 🛰Technologies🛰
Everything is written in Python. Demos are read with LaihoE's parsers: [demoparser2](https://github.com/LaihoE/demoparser) for CS2 and [demoparser](https://github.com/LaihoE/Python-demoparser) 0.4.0 for CS:GO. Excel files are handled with openpyxl; SQLite comes with Python.

## 🕹Installing/Using🕹
1. Install Python. CS2 demos were tested with Python 3.11 and 3.13 (the parser supports 3.8 and newer). **CS:GO demos need Python 3.11 or older on an x86-64 machine**, because the CS:GO parser has no builds for newer Python versions or for ARM (e.g. Apple Silicon Macs); they were tested with 3.11.
2. `pip install -r requirements.txt`
3. Set `GAME` (`"cs2"` or `"csgo"`) and `STORAGE` (`"xlsx"` or `"sqlite"`) in `config.py`.
4. Rate matches:
   ```
   python manage.py match.dem              # one demo
   python manage.py demos/                 # every .dem / .dem.bz2 in a folder, sorted by file name
   python manage.py demos/ --dry-run       # only show what would change
   python manage.py old/ --game csgo       # override GAME (and --storage STORAGE) for one run
   ```
   Elo depends on the order matches are rated in, so pass demos oldest first. A demo that was already rated is recognised by its content and skipped, so re-running a folder is safe.
   `--dry-run` rates the demos exactly like a real run, one after another, but doesn't change the xlsx or SQLite file.

Example output:
```
match.dem
  de_mirage: T 8 - 2 CT, T won (teams are named after the side they finished on)
                                    K/ A/D    ADR  perf    elo
    T   Подсосник blick'a          11/ 4/5    122  1.66   1000 -> 1013  (+13)
    T   123                        11/ 1/4    116  1.59   1000 -> 1012  (+12)
    T   NIGHTSOUL                  10/ 1/5     95  1.43   1000 -> 1011  (+11)
    T   Голова, глаза               5/ 2/7     57  0.89   1000 -> 1007  (+7)
    T   IMI Negev                   4/ 0/2     32  0.90   1000 -> 1007  (+7)
    CT  -ExΩtiC-                    8/ 1/8     78  0.95   1000 -> 993   (-7)
    CT  Dog                         6/ 2/7     75  0.83   1000 -> 992   (-8)
    CT  miu miu                     3/ 3/8     53  0.70   1000 -> 991   (-9)
    CT  povergo                     4/ 0/9     38  0.51   1000 -> 988   (-12)
    CT  Trahun <3 V                 2/ 3/9     43  0.49   1000 -> 986   (-14)

1 recorded, 0 already recorded, 0 failed
```

### 🎥Getting demos🎥
* **Your own server (CS2 or CS:GO):** enable CSTV/GOTV with `tv_enable 1` (before the map loads) and record the match with `tv_record <name>` and `tv_stoprecord`. The demo is written to the server's game folder.
* **Official matchmaking:** download the match in the game under *Your Matches* and use the downloaded `.dem`. `.dem.bz2` files (as served by Valve's replay servers) are decompressed automatically. Whether private queue matches show up there hasn't been checked.
* Demos recorded on the client with `record` (point of view demos) have not been tested.

Only finished matches are rated: a demo that stops before the match end screen is rejected.

### 💾Storage💾
* **xlsx:** sheet `Players` (`steamid | elo | name`, SteamIDs stored as text because Excel rounds numbers longer than 15 digits) and sheet `Matches` with one row per player per match (score, result, rounds played, K/A/D, damage, utility damage, enemies flashed, performance, elo before and after). The file is created if it doesn't exist.
* **sqlite:** tables `players` and `matches` with the same columns.

Keep charts, images and other extras out of the xlsx file: openpyxl drops them whenever it saves the workbook. Put them in a separate workbook that reads from it instead.

New players are added automatically with `START_ELO`.

## 🧮How the elo works🧮
Elo is zero-sum: whatever the winners gain, the losers lose.

1. **Team result.** Each team's rating is the average of its players' ratings, weighted by the rounds they played. The usual Elo formula gives the win expectation, and the winning team gains `20 * (1 - win expectation)` points per player (10 for an even match), which the losing team loses. In a draw the weaker team gains what the stronger team loses. If a team was short-handed for part of the match, the pot shrinks accordingly.
2. **Split by performance.** On the team that gains points, better performances get a bigger share; on the team that loses points, worse performances lose more. Shares are also proportional to the rounds played, so a player who left after a few rounds only gets a small part. Nobody loses points for a win or gains points for a loss.

The performance score compares a player's per-round stats with the average of everyone in the match (1.0 = average):

| Part | Weight | Per round |
|---|---|---|
| Kills | 35% | kills + assists / 2 |
| Damage | 30% | damage to enemies (ADR, includes grenade and fire damage) |
| Survival | 20% | share of rounds survived |
| Utility | 15% | utility damage + 15 per enemy flashed |

Each part counts at most 3 times the average, and the score is limited to 0.3 to 3. A part that nobody in the match had (e.g. no utility damage at all) counts as average for everyone. Headshots aren't rated: a headshot kill already counts as a kill. The weights and constants are at the top of `elo_calc.py`.

Teams are named after the side they finished on: "T" is the team that played the last round as terrorists. Players who left early are still rated with their team for the rounds they played (in CS2, leaving alive during a round counts as a death). A player who switched teams is only rated for the rounds and stats with the team they finished on. Spectators, coaches and bots are ignored. If a team surrenders, the other team wins regardless of the score.

## ⛔️Important notes⛔
* Files from older versions (including the original Excel workbooks) can't be used: csgoMELON refuses to open an xlsx or SQLite file that doesn't have the current layout. Rename or delete it and rate the demos again. Ratings depend on the order matches are rated in, so to change the rating formula later, start a new file and rate all demos again, oldest first.
* Cut-off CS:GO demos are skipped, but a CS:GO demo that is damaged in the middle can crash the CS:GO parser and with it the whole run. The last file name printed is the broken one: move it out of the folder and run again.
* `gsi.cfg` is no longer needed and can be removed from your game's cfg folder.
* Tested with 5v5 matches. Other two-team modes that end with the match end screen (e.g. wingman) should work but haven't been tested.
