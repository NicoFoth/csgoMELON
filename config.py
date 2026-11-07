# Which game the demos are from: "cs2" or "csgo"
# (CS:GO demos need Python 3.11 or older, see README.md)
GAME = "cs2"

# Where the ratings are kept:
#   "xlsx"   - an Excel workbook (XLSX_FILE)
#   "sqlite" - an SQLite database (SQLITE_FILE)
STORAGE = "xlsx"

START_ELO = 1000  # elo of a player that is seen for the first time

XLSX_FILE = "melon.xlsx"
XLSX_SHEET = "Players"  # steamid | elo | name
XLSX_MATCHES_SHEET = "Matches"  # one row per player per match

SQLITE_FILE = "melon.db"
