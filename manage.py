"""Reads finished matches from demo files and updates the elo of every player.

    python manage.py match.dem                 # one demo
    python manage.py demos/                    # every .dem / .dem.bz2 in a folder
    python manage.py demos/ --dry-run          # show the changes without saving
    python manage.py demos/ --game csgo        # override GAME from config.py

Demos are processed in the given order (folders sorted by file name), so pass
them oldest first. Demos that were already recorded are skipped.
"""
import argparse
import logging
import os
import sys

import config
from demo_parser import GAMES, DemoError, read_demo
from elo_calc import rate_match
from storage import SqliteStorage, XlsxStorage

STORAGES = ("xlsx", "sqlite")


def find_demos(paths):
    demos = []
    for path in paths:
        if os.path.isdir(path):
            demos += sorted(os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith((".dem", ".dem.bz2")))
        else:
            demos.append(path)
    return demos


def print_match(match, changes):
    result = f"{match.winner} won" if match.winner else "draw"
    print(f"  {match.map_name}: T {match.score_t} - {match.score_ct} CT, {result}"
          " (teams are named after the side they finished on)")
    print(f"    {'':<2}  {'':<24}  {'  K/ A/D':<10}  {'ADR':>3}  perf    elo")
    for team in ("T", "CT"):
        for p in sorted(match.team(team), key=lambda p: changes[p.steamid].after - changes[p.steamid].before,
                        reverse=True):
            c = changes[p.steamid]
            adr = round(p.damage / max(p.rounds, 1))
            print(f"    {team:<2}  {p.name[:24]:<24}  {p.kills:>3}/{p.assists:>2}/{p.deaths:<3}"
                  f"  {adr:>3}  {c.performance:4.2f}  {c.before:>5} -> {c.after:<5} ({c.after - c.before:+d})")


def main(argv=None):
    # player names can contain any character; don't crash when the console or a
    # redirected output file can't show them
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Update player elo from CS:GO / CS2 demos.")
    parser.add_argument("demos", nargs="+", help="demo files or folders containing demos")
    parser.add_argument("--game", choices=GAMES, default=config.GAME, help="default: GAME from config.py")
    parser.add_argument("--storage", choices=STORAGES, default=config.STORAGE,
                        help="default: STORAGE from config.py")
    parser.add_argument("--dry-run", action="store_true", help="show the elo changes without saving them")
    args = parser.parse_args(argv)
    # argparse doesn't check defaults, so check the values that came from config.py too
    for name, value, choices in (("GAME", args.game, GAMES), ("STORAGE", args.storage, STORAGES)):
        if value not in choices:
            parser.error(f"{name} must be one of {', '.join(choices)}, not {value!r}")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    demos = find_demos(args.demos)
    if not demos:
        print("no demos found")
        return 1

    file = config.SQLITE_FILE if args.storage == "sqlite" else config.XLSX_FILE
    try:
        storage = (SqliteStorage(file, args.dry_run) if args.storage == "sqlite"
                   else XlsxStorage(file, config.XLSX_SHEET, config.XLSX_MATCHES_SHEET, args.dry_run))
    except Exception as e:  # outdated or broken file, missing openpyxl, ...
        print(f"error: can't use {file}: {e}")
        return 1
    counts = {"recorded": 0, "skipped": 0, "failed": 0}
    for path in demos:
        print(path, flush=True)  # if a broken demo crashes the parser, this shows which one it was
        try:
            match = read_demo(path, args.game, storage.has_match)
            if match is None:
                print("  already recorded, skipped")
                counts["skipped"] += 1
                continue
            changes = rate_match(match, storage.get_ratings([p.steamid for p in match.players]), config.START_ELO)
            storage.save_match(match, changes)  # a dry run only saves it in memory
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as e:  # e.g. the parser choking on a broken demo; its panics aren't Exceptions
            known = isinstance(e, (DemoError, OSError, RuntimeError))
            print(f"  error: {e}" if known else f"  error: {type(e).__name__}: {e}")
            counts["failed"] += 1
            continue
        print_match(match, changes)
        counts["recorded"] += 1

    verb = "checked (dry run)" if args.dry_run else "recorded"
    print(f"\n{counts['recorded']} {verb}, {counts['skipped']} already recorded, {counts['failed']} failed")
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
