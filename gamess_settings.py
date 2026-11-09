"""
gamess_settings.py  --  EDIT THIS FILE ONCE FOR YOUR COMPUTER
=============================================================

Every notebook in this book reads these settings through ``gamess_tools``.
Change the values below to match your own GAMESS installation, save the
file, and restart the notebook kernel.

You can also override GAMESS_DIR without editing this file by setting an
environment variable of the same name before starting Jupyter, e.g.

    export GAMESS_DIR=~/gamess
"""

# Folder that holds rungms, gamess.00.x, auxdata/ and scr/.
# "~" means your home folder.
GAMESS_DIR = "~/github/compChem/gamess2024R2claude/gamess-gf14"

# Name of the run script inside GAMESS_DIR.
RUN_SCRIPT = "rungms"

# Version number used when GAMESS was linked (the "00" in gamess.00.x).
VERSION = "00"

# Default number of CPU cores for a job.
NCPUS = 4
