# UsingGAMESSv2

A MystMD book teaching GAMESS quantum chemistry to students. It is a rewrite of
the book in `~/github/UsingGAMESS`: every page that ran GAMESS or processed log
files with terminal commands is converted to a Jupyter notebook that does the
same work in Python. Students should be able to run the notebooks on their own
computer after installing GAMESS.

## Folders and permissions

| Folder | Role | May I change it? |
|---|---|---|
| `~/github/UsingGAMESSv2` | This book. All new and edited files go here. | Yes |
| `~/github/UsingGAMESS` | Original book (`.md` pages + a few `.ipynb`). Source material to convert. | **No. Read only.** |
| `~/github/GAMESS-docs` | GAMESS manual (`02-docs-input.txt` is the input reference). | **No. Read only.** |
| `~/github/gamess2024R2claude/gamess` | GAMESS 2024 R2 build (note the `gamess/` subfolder): `gamess.00.x`, `rungms`, `gms`, `auxdata/`, `scr/`, `restart/`. | **Only** run scripts such as `rungms` and `gms` may be edited, when needed. Change nothing else there. |

- Never write build output, scratch files or test runs into the read-only folders.
- Before editing `rungms` or `gms`, make a dated backup copy beside it and tell
  the user what changed and why.

## Environment and installs

- Use the conda env **`jupyter2`** for everything (`conda run -n jupyter2 ...`
  or activate it).
- **Always ask before installing anything** (conda, pip, brew or otherwise).
- Python packages go into `jupyter2` only.

## Conversion goals

- Replace terminal steps (running `rungms`/`gms`, `grep`/`awk`/`sed` on log
  files, file shuffling) with Python in notebook cells: `subprocess` to run
  GAMESS, `pathlib` for files, and Python parsing of `.log` output.
- Notebooks must run on a student's own machine. Don't hard-code
  `/Users/blink/...` paths: put the GAMESS location and the run script in a
  single, clearly marked settings cell (or a small shared helper module) that
  students edit once.
- Keep the teaching text, explanations and exercises of the original pages.
  Adapt the wording where the workflow changes from terminal to notebook.
- Prefer a small shared Python helper module (for example for running a job and
  parsing energies, geometries and orbitals) over copying the same code into
  every notebook. Keep it readable, because students will look at it.
- Commit saved outputs only when they are small, so the book renders without
  running GAMESS.
- Add and 'AI Statement' at the end on each converted page detailing how the 
  new page has been changed,  how much of the original author's text remains 
  and what was written by AI. Keep this brief, but informative.

## Build

- Preview: `myst start`
- Build HTML: `myst build --html`
- Execute notebooks: `myst build --html --execute`
- The `toc` lives in `myst.yml`. Mirror the structure of
  `~/github/UsingGAMESS/myst.yml`, swapping converted pages for their notebooks.

## Conventions

- Chapters are `.md` pages and `.ipynb` notebooks listed in the `myst.yml` toc.
- Citations use `[@key]` with entries in `references.bib`.
- GAMESS input files live in `inputs/chN/` and job output in `runs/chN/`, one
  folder per chapter, so each chapter runs on its own. Each notebook's settings
  cell sets `INPUTS`, `RUNS` and `gt.RUN_FOLDER`. Show inputs in pages with
  `{literalinclude}`, or read them in notebooks with Python.
- Use SI units. Energies are in hartree unless stated otherwise.

## Don't

- Don't commit notebook outputs larger than a few MB.
- Don't rename chapter files, because that breaks cross-references.
- Don't modify anything in `~/github/UsingGAMESS` or `~/github/GAMESS-docs`.
