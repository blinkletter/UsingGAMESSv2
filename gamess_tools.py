"""
gamess_tools.py  --  small helpers for running GAMESS from a Jupyter notebook
==============================================================================

The notebooks in this book use these functions instead of typing commands
into a terminal.  Each function is short so that you can read it and see
exactly what it does.

Your GAMESS location is set in ``gamess_settings.py``.  Edit that file, not
this one.

Running a job
    RUN_FOLDER                      where jobs are written; each notebook sets
                                    its chapter folder, e.g. Path("runs/ch2")
    run_gamess(input_file)          run GAMESS, write a .log file, return its path
    terminated_normally(log_file)   True if GAMESS finished without error
    check_installation()            print a checklist for your GAMESS setup

Reading text files (Python versions of the Unix tools grep and sed)
    grep(text, file)                lines of a file that contain some text
    substitute(template, new, {...})  write a copy of a file with text replaced

Reading GAMESS log files
    nserch_energies(log_file)       energy at each optimisation step
    optimization_steps(log_file)    step, energy and gradients at each step
    final_energy(log_file)          the last energy in the log file
    excerpt(log_file, text)         print the lines around some text
    final_geometry(log_file)        the last geometry, as (name, charge, x, y, z)
    internal_coordinates(log_file)  bond lengths and angles (needs NZVAR)
    distance(atoms, i, j)           bond length from a geometry
    angle(atoms, i, j, k)           bond angle from a geometry

Molecular orbitals
    occupied_orbitals(log_file)     number of doubly occupied orbitals
    molecular_orbitals(log_file)    energies, symmetry labels and coefficients
    localized_orbitals(log_file)    coefficients of the localized orbitals
    localized_fock(log_file)        Fock matrix written in localized orbitals
    p_character(mo, "X")            share of each MO made of p functions on one axis

Charges and timing
    atomic_charges(log_file)        Mulliken and Lowdin charge on each atom
    wall_time(log_file)             how long the job took, in seconds

Vibrations and reaction paths
    frequencies(log_file)           vibrational frequencies (imaginary ones < 0)
    irc_path(log_file)              (s, energy, geometry) at each IRC point
    irc_points(log_file, bonds)     stride, energy and bond lengths at each IRC point

Writing input files
    new_input(old, new, atoms, {...})  copy an input with new coordinates/keywords
    dat_group(dat_file, "$ZMAT")    copy a group such as $ZMAT, $VEC or $HESS
                                    out of a .dat file
    add_group(inp, text, new)       paste a group (e.g. $HESS) at the end of an input
"""

import os
import platform
import re
import subprocess
from pathlib import Path

import numpy as np

import gamess_settings


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def gamess_dir():
    """The GAMESS folder, from $GAMESS_DIR or gamess_settings.py."""
    folder = os.environ.get("GAMESS_DIR", gamess_settings.GAMESS_DIR)
    return Path(folder).expanduser()


def run_script():
    """Full path to the rungms script."""
    return gamess_dir() / gamess_settings.RUN_SCRIPT


def shared_memory_limits():
    """macOS SystemV shared-memory limits in bytes, or None on other systems.

    GAMESS needs these raised (see the compiling pages).  They reset to tiny
    values every time the Mac restarts.
    """
    if platform.system() != "Darwin":
        return None
    limits = {}
    for key in ("kern.sysv.shmmax", "kern.sysv.shmall"):
        out = subprocess.run(["sysctl", "-n", key], capture_output=True, text=True)
        limits[key] = int(out.stdout.strip() or 0)
    # shmall is counted in 4 kB pages; convert it to bytes for easy comparison
    limits["kern.sysv.shmall"] *= 4096
    return limits


def check_installation(version=None):
    """Print a checklist for the GAMESS installation.  Returns True if all OK."""
    version = version or gamess_settings.VERSION
    folder = gamess_dir()
    checks = [
        (f"GAMESS folder {folder}", folder.is_dir()),
        (f"run script {run_script().name}", os.access(run_script(), os.X_OK)),
        (f"program gamess.{version}.x", (folder / f"gamess.{version}.x").is_file()),
        ("auxdata folder", (folder / "auxdata").is_dir()),
        ("scr folder (scratch files)", (folder / "scr").is_dir()),
    ]
    limits = shared_memory_limits()
    if limits is not None:
        enough = min(limits.values()) >= 1024**3          # at least 1 GB
        checks.append((f"shared memory limit {limits['kern.sysv.shmmax'] / 1024**3:.1f} GB", enough))

    for label, ok in checks:
        print(("  OK    " if ok else "  FIX   ") + label)
    all_ok = all(ok for _, ok in checks)
    if not all_ok:
        print("\nFix the lines marked FIX (see gamess_settings.py and the setup pages).")
    return all_ok


# ---------------------------------------------------------------------------
# Running GAMESS
# ---------------------------------------------------------------------------

# Folder where run_gamess() writes the .log, .dat, ... files of each job.
# Every chapter keeps its own folder, so each notebook sets this in its
# settings cell, for example:   gt.RUN_FOLDER = Path("runs/ch2")
RUN_FOLDER = Path("runs")


def terminated_normally(log_file):
    """True if the log file says GAMESS finished normally."""
    log_file = Path(log_file)
    return log_file.is_file() and "TERMINATED NORMALLY" in log_file.read_text(errors="replace")


def run_gamess(input_file, ncpus=None, version=None, log_file=None,
               run_folder=None, rerun=True):
    """Run GAMESS on one input file and return the path of the .log file.

    input_file  the .inp file (e.g. "inputs/ch2/water.inp")
    ncpus       number of CPU cores (default from gamess_settings.py)
    version     the "00" in gamess.00.x (default from gamess_settings.py)
    log_file    where to write the output (default: run_folder/job.log)
    run_folder  where the .log, .dat, .trj ... files go
                (default: RUN_FOLDER, e.g. "runs/ch2")
    rerun       False = skip the job if a finished log file already exists

    This does what the gms script does in a terminal:
        rm -f $GMS/scr/job.*
        GMS_USERSCR=run_folder  rungms job.inp 00 1  >  job.log
    """
    input_file = Path(input_file).resolve()
    if not input_file.is_file():
        raise FileNotFoundError(f"cannot find {input_file}")
    job = input_file.stem                                   # "water" from "water.inp"
    ncpus = ncpus or gamess_settings.NCPUS
    version = version or gamess_settings.VERSION
    run_folder = Path(run_folder or RUN_FOLDER).resolve()
    run_folder.mkdir(parents=True, exist_ok=True)
    log_file = Path(log_file).resolve() if log_file else run_folder / f"{job}.log"

    if not rerun and terminated_normally(log_file):
        print(f"{job}: using existing {log_file.name} (rerun=True to run again)")
        return log_file

    if " " in str(input_file) or " " in str(run_folder):
        print("Warning: rungms is a C-shell script and may fail on folder names with spaces.")

    # Remove scratch files left behind by an earlier, interrupted run of this job.
    for old in (gamess_dir() / "scr").glob(f"{job}.*"):
        old.unlink()

    # GMS_USERSCR tells rungms to write job.dat, job.trj, ... into run_folder.
    # (This needs the one-line addition to rungms described on the setup page.)
    env = dict(os.environ, GMS_USERSCR=str(run_folder))
    command = [str(run_script()), str(input_file), str(version), str(ncpus)]
    with open(log_file, "w") as log:
        subprocess.run(command, cwd=run_folder, env=env,
                       stdout=log, stderr=subprocess.STDOUT)

    if terminated_normally(log_file):
        print(f"{job}: finished normally ({log_file.name})")
    else:
        print(f"{job}: FAILED, see {log_file}")
    return log_file


# ---------------------------------------------------------------------------
# Reading text files: Python versions of grep and sed
# ---------------------------------------------------------------------------

def grep(text, file):
    """Return the lines of `file` that contain `text` (like: grep "text" file)."""
    with open(file, errors="replace") as f:
        return [line.rstrip("\n") for line in f if text in line]


def substitute(template, new_file, replacements):
    """Copy `template` to `new_file`, replacing text (like: sed "s/OLD/NEW/").

    replacements is a dictionary such as {"NUMBER": "100"}.
    """
    text = Path(template).read_text()
    for old, new in replacements.items():
        text = text.replace(old, str(new))
    Path(new_file).write_text(text)
    return Path(new_file)


# ---------------------------------------------------------------------------
# Reading GAMESS log files
# ---------------------------------------------------------------------------

# Matches lines such as:
#  NSERCH:   2  E=      -37.2380037239  GRAD. MAX=  0.0025260  R.M.S.=  0.0013100
NSERCH_LINE = re.compile(r"NSERCH:\s+(\d+)\s+E=\s+(-?\d+\.\d+)")


def nserch_energies(log_file):
    """List of (step, energy in hartree) for each step of a geometry optimisation."""
    steps = []
    for line in grep("NSERCH:", log_file):
        match = NSERCH_LINE.search(line)
        if match:
            steps.append((int(match.group(1)), float(match.group(2))))
    return steps


def optimization_steps(log_file):
    """List of (step, energy, max gradient, RMS gradient) for each NSERCH line.

    This is the Python version of:  grep "NSERCH" log | grep "GRAD"
    Energies are in hartree, gradients in hartree/bohr.  The last item is the
    final structure of the optimisation.
    """
    steps = []
    for line in grep("NSERCH:", log_file):
        if "GRAD. MAX=" not in line:
            continue
        parts = line.replace("NSERCH:", "").split()
        # parts = [step, 'E=', energy, 'GRAD.', 'MAX=', gmax, 'R.M.S.=', rms]
        steps.append((int(parts[0]), float(parts[2]), float(parts[5]), float(parts[7])))
    return steps


def final_energy(log_file):
    """The last 'FINAL ... ENERGY IS' value in the log file (hartree), or None."""
    lines = grep("FINAL", log_file)
    energies = [float(line.split("ENERGY IS")[1].split()[0])
                for line in lines if "ENERGY IS" in line]
    return energies[-1] if energies else None


def excerpt(log_file, text, before=0, after=20, occurrence=-1):
    """Print part of a log file around a line containing `text`.

    occurrence  which match to show: 0 = first, -1 = last (the default)
    before      lines to show before the match
    after       lines to show after the match

    Each line is printed with its line number, like `grep -n -A 20` would.
    """
    lines = Path(log_file).read_text(errors="replace").splitlines()
    hits = [i for i, line in enumerate(lines) if text in line]
    if not hits:
        print(f"'{text}' not found in {Path(log_file).name}")
        return
    i = hits[occurrence]
    for n in range(max(0, i - before), min(len(lines), i + after + 1)):
        print(f"{n + 1:5d}  {lines[n]}")


# ---------------------------------------------------------------------------
# Geometries
# ---------------------------------------------------------------------------

def _atom_table(lines, start):
    """Read atom lines (NAME CHARGE X Y Z) that follow a header at `start`."""
    atoms = []
    for line in lines[start + 3:]:            # skip header, column titles, dashes
        parts = line.split()
        if len(parts) != 5:
            break
        name, charge, x, y, z = parts
        atoms.append((name, float(charge), float(x), float(y), float(z)))
    return atoms


def final_geometry(log_file, unique=False):
    """The last geometry printed in the log file, in angstrom.

    Returns a list of (name, nuclear charge, x, y, z) tuples.  With
    unique=True only the symmetry unique atoms are returned: these are the
    lines to paste into the $DATA group of a COORD=UNIQUE input file.
    """
    lines = Path(log_file).read_text(errors="replace").splitlines()
    header = ("COORDINATES OF SYMMETRY UNIQUE ATOMS (ANGS)" if unique
              else "COORDINATES OF ALL ATOMS ARE (ANGS)")
    starts = [i for i, line in enumerate(lines) if header in line]
    if not starts:
        raise ValueError(f"no geometry found in {log_file}")
    return _atom_table(lines, starts[-1])


def atom_lines(atoms):
    """Format atoms as $DATA lines:  ' O    8.0   0.0000000000 ...'."""
    return "\n".join(f" {name:<6}{charge:6.1f}{x:16.10f}{y:16.10f}{z:16.10f}"
                     for name, charge, x, y, z in atoms)


def distance(atoms, i, j):
    """Distance (angstrom) between atoms i and j.  Atoms are numbered from 1."""
    a, b = (np.array(atoms[k - 1][2:]) for k in (i, j))
    return float(np.linalg.norm(a - b))


def angle(atoms, i, j, k):
    """Angle i-j-k in degrees, with atom j at the vertex.  Numbered from 1."""
    a, b, c = (np.array(atoms[n - 1][2:]) for n in (i, j, k))
    u, v = a - b, c - b
    cos = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def internal_coordinates(log_file):
    """The last INTERNAL COORDINATES table (only printed when NZVAR is set).

    Returns a list of (type, atoms, value) where value is in angstrom for a
    STRETCH and in degrees for a BEND or TORSION.
    """
    lines = Path(log_file).read_text(errors="replace").splitlines()
    starts = [i for i, line in enumerate(lines) if "INTERNAL COORDINATES" in line
              and "-" not in line]
    if not starts:
        return []
    table = []
    for line in lines[starts[-1] + 6:]:      # skip the title and column headers
        parts = line.split()
        if len(parts) < 5 or not parts[0].isdigit():
            break
        kind = parts[1]
        table.append((kind, tuple(int(p) for p in parts[2:-2]), float(parts[-1])))
    return table


# ---------------------------------------------------------------------------
# Molecular orbitals
# ---------------------------------------------------------------------------

def occupied_orbitals(log_file):
    """Number of occupied (alpha) orbitals.  For RHF this is the HOMO number."""
    line = grep("NUMBER OF OCCUPIED ORBITALS (ALPHA)", log_file)[-1]
    return int(line.split("=")[1])


def _is_int_line(line):
    parts = line.split()
    return bool(parts) and all(p.isdigit() for p in parts)


def _orbital_blocks(lines, start, with_energies=True):
    """Read an orbital table that GAMESS prints five columns at a time.

    Each block looks like this (the energy and symmetry lines are missing
    for localized orbitals):

                          1          2          3     <- orbital numbers
                      -11.2052    -0.9451    -0.5461  <- energies (hartree)
                         A1         A1         T2     <- symmetry labels
        1  C  1  S    0.563404  -0.102964  -0.000000  <- one row per basis function
    """
    energies, symmetries, labels, columns = [], [], [], []
    i = start + 1
    while i < len(lines):
        while i < len(lines) and not lines[i].strip():        # skip blank lines
            i += 1
        if i >= len(lines) or not _is_int_line(lines[i]):
            break                                              # end of the table
        i += 1
        if with_energies:
            energies += [float(e) for e in lines[i].split()]
            symmetries += lines[i + 1].split()
            i += 2
        while i < len(lines) and not lines[i].strip():        # skip blank lines
            i += 1
        block, block_labels = [], []
        # coefficient rows start with the basis-function number
        while i < len(lines) and lines[i].split()[:1] and lines[i].split()[0].isdigit():
            line = lines[i]
            # the first 15 characters hold "  1  C  1  S  ", the rest are numbers
            block_labels.append(" ".join(line[:15].split()[1:]))
            # every number has 6 decimals; large ones can touch, e.g.
            # "-10.340924-172.072365", so find them with a regex, not split()
            block.append([float(v) for v in re.findall(r"-?\d+\.\d{6}", line[15:])])
            i += 1
        if not labels:
            labels = block_labels
        columns.append(np.array(block))
    coefficients = np.hstack(columns) if columns else np.empty((0, 0))
    return energies, symmetries, labels, coefficients


def molecular_orbitals(log_file):
    """The last set of molecular orbitals printed in the log file.

    Returns a dictionary with
        "energies"      orbital energies in hartree, lowest first
        "symmetries"    symmetry labels such as "A1" or "T2"
        "labels"        the basis function on each row, e.g. "C 1 S", "H 2 X"
        "coefficients"  array with one row per basis function and one
                        column per orbital (column 0 is orbital 1)
    """
    lines = Path(log_file).read_text(errors="replace").splitlines()
    starts = [i for i, line in enumerate(lines)
              if line.strip() in ("EIGENVECTORS", "MOLECULAR ORBITALS")]
    if not starts:
        raise ValueError(f"no molecular orbitals found in {log_file}")
    start = starts[-1] + 1                    # skip the dashed line under the title
    energies, symmetries, labels, coefficients = _orbital_blocks(lines, start)
    return {"energies": energies, "symmetries": symmetries,
            "labels": labels, "coefficients": coefficients}


def localized_orbitals(log_file):
    """Coefficients of the last set of localized orbitals (needs LOCAL=...).

    Returns (labels, coefficients) in the same layout as molecular_orbitals().
    Localized orbitals have no orbital energy or symmetry label.
    """
    lines = Path(log_file).read_text(errors="replace").splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip().endswith("LOCALIZED ORBITALS")]
    if not starts:
        raise ValueError(f"no localized orbitals found in {log_file}")
    _, _, labels, coefficients = _orbital_blocks(lines, starts[-1], with_energies=False)
    return labels, coefficients


def localized_fock(log_file):
    """The 'FOCK OPERATOR FOR THE LOCALIZED ORBITALS' as a square numpy array.

    The diagonal holds the energy of each localized orbital (hartree); the
    off-diagonal numbers say how strongly two localized orbitals interact.
    Only the valence orbitals are included (core orbitals are frozen).
    """
    lines = Path(log_file).read_text(errors="replace").splitlines()
    start = [i for i, line in enumerate(lines)
             if "FOCK OPERATOR FOR THE LOCALIZED ORBITALS" in line][-1]
    values = {}
    i = start + 1
    while i < len(lines):
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines) or not _is_int_line(lines[i]):
            break
        columns = [int(c) for c in lines[i].split()]
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        while i < len(lines) and lines[i].strip() and not _is_int_line(lines[i]):
            parts = lines[i].split()
            row = int(parts[0])
            for col, value in zip(columns, parts[1:]):
                values[(row, col)] = values[(col, row)] = float(value)
            i += 1
    n = max(r for r, _ in values)
    fock = np.zeros((n, n))
    for (r, c), value in values.items():
        fock[r - 1, c - 1] = value
    return fock


# ---------------------------------------------------------------------------
# Writing new input files from old ones
# ---------------------------------------------------------------------------

def new_input(old_input, new_input_file, atoms=None, replacements=None):
    """Write a new input file based on an old one.

    atoms         new atom lines for the $DATA group, e.g. from
                  final_geometry(log, unique=True).  The title, the
                  symmetry line and the blank line are kept.
    replacements  text to swap, e.g. {"GBASIS=AM1": "GBASIS=N21 NGAUSS=3"}

    This is the Python version of copying the old file and pasting the
    coordinates from the log file into it with a text editor.
    """
    text = Path(old_input).read_text()
    for old, new in (replacements or {}).items():
        if old not in text:
            raise ValueError(f"'{old}' is not in {old_input}")
        text = text.replace(old, new)

    if atoms is not None:
        lines = text.splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip().upper() == "$DATA")
        end = next(i for i in range(start, len(lines)) if lines[i].strip().upper() == "$END")
        symmetry = lines[start + 2].strip().upper()
        first_atom = start + 3 if symmetry in ("C1", "C 1") else start + 4
        lines[first_atom:end] = atom_lines(atoms).splitlines()
        text = "\n".join(lines) + "\n"

    Path(new_input_file).write_text(text)
    return Path(new_input_file)


def add_group(input_file, group_text, new_input_file=None):
    """Append a group (e.g. from dat_group) to the end of an input file.

    This is the Python version of pasting a $HESS or $VEC group from a
    .dat file into the bottom of an input file with a text editor.
    """
    new_input_file = Path(new_input_file or input_file)
    text = Path(input_file).read_text().rstrip("\n") + "\n" + group_text
    new_input_file.write_text(text)
    return new_input_file


def dat_group(dat_file, group, occurrence=-1):
    """Copy one group, e.g. "$ZMAT", "$VEC" or "$HESS", out of a .dat file.

    Returns the text from the line that starts the group up to and including
    its " $END" line, ready to paste into a new input file.  A .dat file can
    hold several copies of a group; occurrence=-1 (the default) takes the
    last one, which belongs to the final structure.

    This is the Python version of opening the .dat file in a text editor and
    copying the group by hand.
    """
    lines = Path(dat_file).read_text(errors="replace").splitlines()
    name = group.upper().lstrip("$")
    starts = [i for i, line in enumerate(lines)
              if line.upper().startswith(f" ${name}")]
    if not starts:
        raise ValueError(f"no {group} group in {dat_file}")
    start = starts[occurrence]
    end = next(i for i in range(start, len(lines))
               if lines[i].strip().upper().startswith("$END"))
    return "\n".join(lines[start:end + 1]) + "\n"


# ---------------------------------------------------------------------------
# Vibrations and reaction paths
# ---------------------------------------------------------------------------

def frequencies(log_file):
    """Vibrational frequencies (cm-1) from the last normal-mode table.

    Imaginary frequencies, which GAMESS prints as e.g. "523.45 I", are
    returned as negative numbers.  A transition state has exactly one.
    The six near-zero translations and rotations are included.
    """
    text = Path(log_file).read_text(errors="replace")
    # a job can print several tables (e.g. HSSEND=.TRUE.); use the last one
    last_table = text.split("NORMAL COORDINATE ANALYSIS IN THE HARMONIC")[-1]
    lines = [line for line in last_table.splitlines() if "FREQUENCY:" in line]
    values = []
    for line in lines:
        parts = line.split("FREQUENCY:")[1].split()
        i = 0
        while i < len(parts):
            value = float(parts[i])
            if i + 1 < len(parts) and parts[i + 1] == "I":
                value, i = -value, i + 1
            values.append(value)
            i += 1
    return values


def irc_path(log_file):
    """The points along an intrinsic reaction coordinate (RUNTYP=IRC).

    Returns a list of (s, energy, atoms), one per IRC point, where
        s       distance travelled along the path from the transition state,
                in sqrt(amu)*bohr
        energy  total energy in hartree
        atoms   the geometry, as returned by final_geometry()

    GAMESS prints each point like this:
        POINT   1 ON THE REACTION PATH
        AT PATH DISTANCE STOTAL =   0.29995     SQRT(AMU)-BOHR
        TOTAL ENERGY            =  -232.8810928 HARTREE
        ...
        COORDINATES OF ALL ATOMS ARE (ANGS)
    """
    lines = Path(log_file).read_text(errors="replace").splitlines()
    points = []
    for i, line in enumerate(lines):
        if "ON THE REACTION PATH" not in line:
            continue
        s = float(lines[i + 2].split("=")[1].split()[0])
        energy = float(lines[i + 3].split("=")[1].split()[0])
        start = next(j for j in range(i, len(lines))
                     if "COORDINATES OF ALL ATOMS ARE (ANGS)" in lines[j])
        points.append((s, energy, _atom_table(lines, start)))
    return points


# ---------------------------------------------------------------------------
# Pi orbitals, charges and timing
# ---------------------------------------------------------------------------

def p_character(mo, axis):
    """For each orbital, the share made of p functions along one axis.

    mo    the dictionary returned by molecular_orbitals()
    axis  "X", "Y" or "Z": the axis perpendicular to a planar molecule

    Returns a numpy array with one number (0 to 1) per orbital.  A pi
    orbital of a molecule lying in the yz-plane is built only from X
    functions, so its share is close to 1; a sigma orbital has 0.
    (This is the sum of squared coefficients, a rough but useful measure.)
    """
    rows = [i for i, label in enumerate(mo["labels"]) if label.split()[-1] == axis]
    squares = mo["coefficients"] ** 2
    return squares[rows].sum(axis=0) / squares.sum(axis=0)


def atomic_charges(log_file):
    """The last 'TOTAL MULLIKEN AND LOWDIN ATOMIC POPULATIONS' table.

    Returns a list of (atom name, Mulliken charge, Lowdin charge).
    """
    lines = Path(log_file).read_text(errors="replace").splitlines()
    starts = [i for i, line in enumerate(lines)
              if "TOTAL MULLIKEN AND LOWDIN ATOMIC POPULATIONS" in line]
    if not starts:
        raise ValueError(f"no population analysis found in {log_file}")
    charges = []
    for line in lines[starts[-1] + 2:]:       # skip the title and column headers
        parts = line.split()
        if len(parts) != 6:
            break
        charges.append((parts[1], float(parts[3]), float(parts[5])))
    return charges


def wall_time(log_file):
    """Total wall clock time of the job in seconds (the last value printed)."""
    line = grep("TOTAL WALL CLOCK TIME", log_file)[-1]
    return float(line.split("=")[1].split()[0])


def irc_points(log_file, bonds=((1, 3), (2, 3))):
    """Table of the points along an IRC run (RUNTYP=IRC, needs NZVAR).

    Returns a list of dictionaries, one per point, such as
        {"stride": 0.29997, "energy": -955.6091117, "R(1,3)": 2.434, "R(2,3)": 2.335}
    stride  distance along the path, STOTAL, in sqrt(amu)*bohr
    energy  total energy in hartree
    R(i,j)  bond length in angstrom for each pair in `bonds` (atoms numbered
            from 1, as in the INTERNAL COORDINATES table of the log file)

    Point 0 is the transition state (stride 0).  Its energy is the first
    FINAL energy in the log file, so use TSENGY=.TRUE. in $IRC.  This does the
    work of grep-ing for "AT PATH DISTANCE STOTAL", "TOTAL ENERGY" and
    "STRETCH   1  3" and lining the results up.
    """
    def key(i, j):
        return f"R({i},{j})"

    wanted = {(i, j) for i, j in bonds} | {(j, i) for i, j in bonds}
    points = []
    point = {"stride": 0.0, "energy": None}
    for line in Path(log_file).read_text(errors="replace").splitlines():
        if "AT PATH DISTANCE STOTAL" in line:          # a new IRC point starts
            points.append(point)
            point = {"stride": float(line.split("=")[1].split()[0]), "energy": None}
        elif "TOTAL ENERGY" in line and "HARTREE" in line:
            point["energy"] = float(line.split("=")[1].split()[0])
        elif line.startswith(" FINAL") and "ENERGY IS" in line and point["energy"] is None \
                and not points:                         # transition state energy
            point["energy"] = float(line.split("ENERGY IS")[1].split()[0])
        elif "STRETCH" in line:
            parts = line.split()                        # NO. STRETCH I J BOHR ANG
            i, j = int(parts[2]), int(parts[3])
            if (i, j) in wanted:
                name = key(*((i, j) if (i, j) in bonds else (j, i)))
                point.setdefault(name, float(parts[-1]))   # first table after the point
    points.append(point)
    return points
