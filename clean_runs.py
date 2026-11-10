"""
clean_runs.py  --  delete every file in the runs/ folder
========================================================

The notebooks write everything a GAMESS job makes into runs/chN/: log
files, .dat files, input files generated from templates, and tables of
results. Notebooks that call ``gt.run_gamess(..., rerun=False)`` reuse a
finished log file instead of running the job again. Delete the files to
make every job run from scratch.

Usage (from the book folder):

    python clean_runs.py              # list the files, then ask before deleting
    python clean_runs.py ch8 ch9      # only these chapter folders
    python clean_runs.py --dry-run    # list the files, delete nothing
    python clean_runs.py --yes        # delete without asking

Every file inside runs/ is removed. The chapter folders themselves stay.
Your original inputs live in inputs/ and are never touched.
"""

import argparse
from collections import Counter
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runs"


def find_files(chapters):
    """Return a sorted list of every file in runs/ (or in the chapter folders given)."""
    folders = [RUNS / ch for ch in chapters] if chapters else [RUNS]
    files = []
    for folder in folders:
        if not folder.is_dir():
            print(f"skipping {folder}: no such folder")
            continue
        files.extend(p for p in folder.rglob("*") if p.is_file())
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description="Delete every file in runs/.")
    parser.add_argument("chapters", nargs="*", help="chapter folders, e.g. ch8 ch9 (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="list the files, delete nothing")
    parser.add_argument("--yes", action="store_true", help="delete without asking")
    args = parser.parse_args()

    files = find_files(args.chapters)
    if not files:
        print("No files found.")
        return

    for f in files:
        print(f.relative_to(RUNS.parent))
    kinds = Counter(f.suffix or f.name for f in files)
    summary = ", ".join(f"{n} {kind}" for kind, n in sorted(kinds.items()))
    print(f"\n{len(files)} file(s) found: {summary}")

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

    for f in files:
        f.unlink()
    print(f"Deleted {len(files)} file(s).")


if __name__ == "__main__":
    main()
