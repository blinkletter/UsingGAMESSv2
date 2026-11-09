"""
clean_runs.py  --  delete GAMESS .log files from the runs/ folder
================================================================

Notebooks that call ``gt.run_gamess(..., rerun=False)`` reuse a finished
log file instead of running the job again. Delete the logs to force every
job to run from scratch.

Usage (from the book folder):

    python clean_runs.py              # list the logs, then ask before deleting
    python clean_runs.py ch8 ch9      # only these chapter folders
    python clean_runs.py --dry-run    # list the logs, delete nothing
    python clean_runs.py --yes        # delete without asking

Only ``*.log`` files are removed. Input files (.inp) and .dat files stay.
"""

import argparse
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runs"


def find_logs(chapters):
    """Return a sorted list of .log files in runs/ (or in the chapter folders given)."""
    folders = [RUNS / ch for ch in chapters] if chapters else [RUNS]
    logs = []
    for folder in folders:
        if not folder.is_dir():
            print(f"skipping {folder}: no such folder")
            continue
        logs.extend(folder.rglob("*.log"))
    return sorted(logs)


def main():
    parser = argparse.ArgumentParser(description="Delete GAMESS .log files from runs/.")
    parser.add_argument("chapters", nargs="*", help="chapter folders, e.g. ch8 ch9 (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="list the files, delete nothing")
    parser.add_argument("--yes", action="store_true", help="delete without asking")
    args = parser.parse_args()

    logs = find_logs(args.chapters)
    if not logs:
        print("No .log files found.")
        return

    for log in logs:
        print(log.relative_to(RUNS.parent))
    print(f"\n{len(logs)} log file(s) found.")

    if args.dry_run:
        print("Dry run: nothing deleted.")
        return
    if not args.yes:
        try:
            answer = input("Delete them? [y/N] ")
        except EOFError:          # no keyboard available, e.g. under `conda run`
            answer = ""
        if answer.strip().lower() != "y":
            print("Nothing deleted. (Use --yes to delete without asking.)")
            return

    for log in logs:
        log.unlink()
    print(f"Deleted {len(logs)} log file(s).")


if __name__ == "__main__":
    main()
