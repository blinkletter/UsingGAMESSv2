# The Helper Tools: A User's Manual

Every notebook in this book starts with

```python
import gamess_tools as gt
```

That one line loads a small library of functions that **run *GAMESS***, **read its log files** and **write new input files**, so that the notebooks never need the terminal. This page is the manual for that library. It tells you what each tool does, what you give it, what you get back, and shows a short example. Look things up here when a notebook uses a `gt.` function, or when you want to use the tools for your own molecules in the exercises.

The library lives in two files next to the notebooks:

| File | What it holds | Do you edit it? |
| :--- | :--- | :--- |
| `gamess_settings.py` | Where *GAMESS* lives on **your** computer | **Yes, once** |
| `gamess_tools.py` | The tools described on this page | No, but do read it |

```{tip}
Every tool has a **docstring**, a short description in triple quotes under its `def` line. In a notebook you can read it without opening the file: type `gt.final_energy?` in a cell and run it. `help(gt)` prints the table of contents of the whole library.
```

The examples on this page use log files from the chapters of this book, such as `runs/ch2/water_321G.log` (water, HF/3-21G optimization). Your numbers can differ in the last digits if you run the jobs yourself.

## Quick Reference

| Task | Tool | Section |
| :--- | :--- | :--- |
| Check that *GAMESS* is set up | `check_installation()` | [](#sec-1e-setup) |
| Run a job | `run_gamess(input_file)` | [](#sec-1e-running) |
| Did it finish? | `terminated_normally(log)` | [](#sec-1e-running) |
| Find lines in a file | `grep(text, file)` | [](#sec-1e-text) |
| Show part of a log file | `excerpt(log, text)` | [](#sec-1e-text) |
| Fill in a template | `substitute(template, new, {...})` | [](#sec-1e-text) |
| Final energy | `final_energy(log)` | [](#sec-1e-energy) |
| Energy at each optimization step | `nserch_energies(log)`, `optimization_steps(log)` | [](#sec-1e-energy) |
| Plot an optimization | `plot_optimization(log)` | [](#sec-1e-energy) |
| How long did it take? | `wall_time(log)` | [](#sec-1e-energy) |
| Final structure | `final_geometry(log)` | [](#sec-1e-geometry) |
| Bond lengths and angles | `distance()`, `angle()`, `shortest_distance()`, `internal_coordinates()` | [](#sec-1e-geometry) |
| Molecular orbitals | `molecular_orbitals(log)`, `occupied_orbitals(log)` | [](#sec-1e-orbitals) |
| Find π orbitals | `pi_orbitals(log, axis)`, `p_character()`, `p_coefficients()` | [](#sec-1e-orbitals) |
| Localized orbitals | `localized_orbitals(log)`, `localized_fock(log)` | [](#sec-1e-orbitals) |
| Draw an MO energy diagram | `energy_levels(ax, x, energies)` | [](#sec-1e-orbitals) |
| Atomic charges | `atomic_charges(log)` | [](#sec-1e-orbitals) |
| New input from an old one | `new_input(old, new, atoms, {...})` | [](#sec-1e-inputs) |
| Copy `$HESS`, `$VEC`, `$ZMAT` from a .dat file | `dat_group(dat, "$HESS")`, `add_group()` | [](#sec-1e-inputs) |
| Saddle point and IRC inputs | `saddle_input()`, `irc_inputs()` | [](#sec-1e-inputs) |
| Vibrational frequencies | `frequencies(log)` | [](#sec-1e-paths) |
| Reaction paths (IRC) | `irc_points()`, `irc_table()`, `irc_path()` | [](#sec-1e-paths) |
| Hartree to kJ/mol | `HARTREE_TO_KJMOL` | [](#sec-1e-energy) |

(sec-1e-setup)=
## Setting Up

### `gamess_settings.py`

This is the only file you change. Open it in any text editor (or in *JupyterLab*), set the values for your computer, save it, and **restart the notebook kernel**, because *Python* reads the file only once.

```{literalinclude} gamess_settings.py
:language: python
```

| Setting | Meaning |
| :--- | :--- |
| `GAMESS_DIR` | The folder that holds `rungms`, `gamess.00.x`, `auxdata/` and `scr/`. `~` means your home folder. |
| `RUN_SCRIPT` | The name of the run script in that folder, normally `rungms`. |
| `VERSION` | The version number in the name of the program, the `00` in `gamess.00.x`. |
| `NCPUS` | How many CPU cores a job uses unless you ask for another number. |

If the environment variable `GAMESS_DIR` is set before *Jupyter* starts, it wins over the value in the file. That is handy if you keep two builds of *GAMESS*.

### `check_installation()`

Prints a checklist and returns `True` when every line is `OK`. Run it first, and run it again whenever jobs start failing.

```python
gt.check_installation()
```

```text
  OK    GAMESS folder /Users/you/gamess
  OK    run script rungms
  OK    program gamess.00.x
  OK    auxdata folder
  OK    scr folder (scratch files)
  OK    shared memory limit 16.0 GB
```

The last line only appears on a Mac. *MacOS* resets the shared-memory limit to a tiny value every time it restarts; see the compiling pages for how to raise it. Three smaller tools sit behind the checklist: `gt.gamess_dir()` and `gt.run_script()` return the paths it uses, and `gt.shared_memory_limits()` returns the two Mac limits in bytes (or `None` on other systems).

### The settings cell of a notebook

Every chapter notebook begins with a settings cell like this one:

```python
from pathlib import Path
import gamess_tools as gt

INPUTS = Path("inputs/ch2")   # input files for this chapter
RUNS = Path("runs/ch2")       # where log files are written
gt.RUN_FOLDER = RUNS          # run_gamess() writes its files here
```

`gt.RUN_FOLDER` tells `run_gamess()` where to put the results. Each chapter has its own folder so that its files don't get mixed up with those of other chapters. Copy this cell when you start a notebook of your own and change the chapter folder.

(sec-1e-running)=
## Running *GAMESS*

### `run_gamess(input_file, ncpus=None, rerun=True, ...)`

Runs one job and returns the **path of the log file**. This is the tool you will use most.

```python
log = gt.run_gamess(INPUTS / "water.inp")
```

```text
water: finished normally (water.log)
```

What it does, step by step:

1. Takes the job name from the input file (`water` from `water.inp`).
2. Makes the run folder (`gt.RUN_FOLDER`) if it isn't there yet.
3. Removes scratch files that an interrupted run of the same job left in *GAMESS*'s `scr/` folder.
4. Starts `rungms` and writes everything *GAMESS* prints into `water.log`. The `.dat` file (and `.trj`, `.rst` ...) go into the run folder too.
5. Prints whether the job finished normally.

| Argument | Default | Meaning |
| :--- | :--- | :--- |
| `input_file` | | The `.inp` file. |
| `ncpus` | `NCPUS` from the settings | Number of CPU cores. |
| `rerun` | `True` | `False` skips the job if a finished log file is already there. Use it for long jobs so that running the notebook again takes seconds, not hours. |
| `run_folder` | `gt.RUN_FOLDER` | Where to write the results. |
| `log_file` | `run_folder/job.log` | A different name for the log file. |
| `version` | `VERSION` from the settings | The `00` in `gamess.00.x`. |

A job that fails still returns the log file path, so you can look inside to see what went wrong (try `gt.excerpt(log, "ERROR")`).

```{warning}
`rungms` is a C-shell script and can fail when a folder name contains a space. Keep the book and *GAMESS* in folders without spaces.
```

### `terminated_normally(log_file)`

`True` if the log file exists and ends with `TERMINATED NORMALLY`. Use it in a loop to check a batch of jobs:

```python
for log in sorted(RUNS.glob("*.log")):
    print(log.name, gt.terminated_normally(log))
```

(sec-1e-text)=
## Searching and Editing Text

A log file is just a long text file. These three tools are the *Python* versions of the classic text tools `grep` and `sed`.

### `grep(text, file)`

Returns a list of every line of the file that contains `text`.

```python
gt.grep("FINAL", "runs/ch2/water_321G.log")
```

```text
[' FINAL RHF ENERGY IS      -75.5853052286 AFTER   9 ITERATIONS',
 ' FINAL RHF ENERGY IS      -75.5841810825 AFTER   7 ITERATIONS',
 ...
 ' FINAL RHF ENERGY IS      -75.5859597578 AFTER   3 ITERATIONS']
```

The search is case sensitive and looks for plain text, not a pattern.

### `excerpt(log_file, text, before=0, after=20, occurrence=-1)`

Prints a piece of the file around the line that contains `text`, with line numbers. By default it shows the **last** match and the 20 lines after it.

```python
gt.excerpt("runs/ch2/water_321G.log", "EQUILIBRIUM GEOMETRY LOCATED", after=5)
```

```text
 1211        ***** EQUILIBRIUM GEOMETRY LOCATED *****
 1212   COORDINATES OF SYMMETRY UNIQUE ATOMS (ANGS)
 1213     ATOM   CHARGE       X              Y              Z
 1214   ------------------------------------------------------------
 1215   O           8.0   0.0000000000   0.0000000000  -0.0081020518
 1216   H           1.0  -0.7804697613  -0.0000000000  -0.5784383303
```

Use `occurrence=0` for the first match, `occurrence=1` for the second, and so on. `before=5` adds five lines above the match. The line numbers are the ones you would see in a text editor, so you can find the place again in the full file.

### `substitute(template, new_file, replacements)`

Copies a file and swaps text on the way. `replacements` is a dictionary of `{old: new}` pairs. It returns the path of the new file. This is how the notebooks make a series of inputs from one **template**:

```python
for n in (2, 3, 6):
    inp = gt.substitute(INPUTS / "water_template.inp",
                        RUNS / f"water_sto{n}g.inp",
                        {"NGAUSS=NUMBER": f"NGAUSS={n}"})
    gt.run_gamess(inp)
```

Choose a placeholder word that can't appear anywhere else in the file (`NUMBER`, `ANGLE`). Numbers in the replacements are turned into text for you. The rotation scans in [chapter 5](5_Rotation_Profiles.ipynb) and [chapter 7](7_Butadiene.ipynb) are built this way.

(sec-1e-energy)=
## Energies and Optimizations

### `final_energy(log_file)`

The number from the last `FINAL ... ENERGY IS` line, in hartree, or `None` if there is none. For an optimization this is the energy of the optimized structure.

```python
gt.final_energy("runs/ch2/water_321G.log")
```

```text
-75.5859597578
```

### `nserch_energies(log_file)`

A geometry optimization prints one `NSERCH` line per step. This returns a list of `(step, energy)` pairs.

```python
gt.nserch_energies("runs/ch2/water_321G.log")
```

```text
[(0, -75.5853052286), (1, -75.5841810825), (2, -75.585884075),
 (3, -75.5859592318), (4, -75.5859597493), (5, -75.5859597578)]
```

The last pair is the final structure, so `gt.nserch_energies(log)[-1][1]` is its energy.

### `optimization_steps(log_file)`

Like `nserch_energies()` but with the gradients too: `(step, energy, largest gradient, RMS gradient)`. The gradients, in hartree/bohr, show how far the structure still is from a stationary point. The optimization stops when the largest gradient falls below `OPTTOL` in `$STATPT`.

```python
gt.optimization_steps("runs/ch2/water_321G.log")[-1]
```

```text
(5, -75.5859597578, 1.43e-05, 6e-06)
```

### `plot_optimization(log_file, title="", zoom_from=3)`

Plots the energy at each step relative to the final energy, in kJ/mol. The left panel shows every step; the right panel starts at step `zoom_from`, where the changes are too small to see on the left.

```python
gt.plot_optimization(RUNS / "butadiene_trans.log", "s-trans butadiene, HF/3-21G*")
```

See [chapter 7](7_Butadiene.ipynb) for the figure.

### `wall_time(log_file)`

How long the job took, in seconds of wall-clock time. Use it to compare the cost of methods, basis sets and symmetries, as in [the benzene chapter](6_Benzene.ipynb).

### `HARTREE_TO_KJMOL`

Not a function but a number: 2625.5 kJ/mol in one hartree. Multiply an energy **difference** in hartree by it:

```python
dE = (E_syn - E_anti) * gt.HARTREE_TO_KJMOL
```

(sec-1e-geometry)=
## Geometries

### `final_geometry(log_file, unique=False)`

The last structure printed in the log file, in ångström, as a list of `(name, nuclear charge, x, y, z)` tuples. For an optimization this is the optimized structure.

```python
atoms = gt.final_geometry("runs/ch2/water_321G.log")
atoms
```

```text
[('O', 8.0, 0.0, 0.0, -0.0081020518),
 ('H', 1.0, 0.7804697613, -0.0, -0.5784383303),
 ('H', 1.0, -0.7804697613, -0.0, -0.5784383303)]
```

With `unique=True` you get only the **symmetry-unique** atoms, the ones that go into the `$DATA` group of an input that uses symmetry (for water in *C<sub>2v</sub>*: one O and one H). Use `unique=False` (all atoms) for a `C1` input.

`gt.atom_lines(atoms)` turns such a list back into text in the `$DATA` format:

```text
 O        8.0    0.0000000000    0.0000000000   -0.0081020518
 H        1.0   -0.7804697613   -0.0000000000   -0.5784383303
```

### `distance(atoms, i, j)` and `angle(atoms, i, j, k)`

The distance between atoms `i` and `j` in ångström, and the angle i–j–k in degrees with atom `j` at the vertex. **Atoms are numbered from 1**, as in the log file.

```python
gt.distance(atoms, 1, 2), gt.angle(atoms, 2, 1, 3)
```

```text
(0.9666522222996793, 107.68429992780175)
```

### `shortest_distance(atoms, a, b)`

The shortest distance between an atom named `a` and one named `b`. This saves you from looking up atom numbers, which change from one input file to the next.

```python
gt.shortest_distance(atoms, "C", "C")   # shortest C-C bond
gt.shortest_distance(atoms, "C", "H")   # shortest C-H bond
```

It is used in [the benzene chapter](6_Benzene.ipynb) to compare four structures that number their atoms differently.

### `internal_coordinates(log_file)`

The last table of internal coordinates in the log file. *GAMESS* prints it only when `NZVAR` is set in `$CONTRL` (with a `$ZMAT` group, or a Z-matrix input). Each entry is `(type, atoms, value)`; stretches are in ångström, bends and torsions in degrees.

```python
gt.internal_coordinates("runs/ch7/butadiene_trans.log")[:4]
```

```text
[('STRETCH', (2, 1), 1.3204331),
 ('STRETCH', (3, 2), 1.4671149),
 ('BEND', (3, 2, 1), 123.9525002),
 ('STRETCH', (4, 3), 1.3204695)]
```

The list is in the same order as the `$ZMAT` coordinates, so `gt.internal_coordinates(log)[5][2]` is the value of the sixth coordinate.

(sec-1e-orbitals)=
## Molecular Orbitals and Charges

### `molecular_orbitals(log_file)`

The last set of molecular orbitals in the log file, as a dictionary:

| Key | Holds |
| :--- | :--- |
| `"energies"` | Orbital energies in hartree, lowest first |
| `"symmetries"` | Symmetry labels such as `"A1"` or `"B2"` |
| `"labels"` | The basis function of each row, such as `"O 1 S"` or `"H 2 X"` (element, atom number, type) |
| `"coefficients"` | A `numpy` array: one row per basis function, one column per orbital |

```python
mo = gt.molecular_orbitals("runs/ch2/water_321G.log")
mo["energies"][:5], mo["symmetries"][:5]
```

```text
([-20.4272, -1.321, -0.6855, -0.5298, -0.4772], ['A1', 'A1', 'B1', 'A1', 'B2'])
```

**Column 0 is orbital 1.** So orbital `n` is `mo["coefficients"][:, n - 1]` and its energy is `mo["energies"][n - 1]`. *GAMESS* prints all occupied orbitals and some empty ones; with `NPRINT=-5` it prints none, and this function raises an error.

### `occupied_orbitals(log_file)`

The number of occupied (alpha) orbitals. For a closed-shell RHF molecule this is the number of the **HOMO**, and the LUMO is one more. Water has 5.

### `p_character(mo, axis)`

For every orbital, the share made of p functions along one axis (`"X"`, `"Y"` or `"Z"`), from 0 to 1. It takes the dictionary from `molecular_orbitals()`. For a planar molecule, use the axis perpendicular to the plane: π orbitals score near 1 and σ orbitals 0. (It is the sum of squared coefficients, a rough but useful measure.)

### `pi_orbitals(log_file, axis="Z", limit=0.5)`

Finds the π orbitals in one step. It returns three things: the orbital dictionary, the column numbers of the orbitals whose `p_character` is above `limit`, and the `p_character` of every orbital.

```python
mo, pis, share = gt.pi_orbitals("runs/ch6/AllylCat_6311_U.log", axis="X")
[n + 1 for n in pis]          # orbital numbers, counted from 1
```

```text
[11, 12, 16, 19]
```

The numbers in `pis` count from 0, like the columns, so add 1 to get the orbital numbers that *GAMESS* and *MacMolPlt* use.

### `p_coefficients(mo, orbital, atom="C 1")`

The coefficients `(x, y, z)` of the first set of p functions of one atom in one orbital. Here `orbital` counts from 1. It shows which way a p-type orbital points:

```python
mo = gt.molecular_orbitals("runs/ch3/methane_6311_U_E.log")
gt.p_coefficients(mo, 3, atom="C 1")
```

```text
array([ 0.189743, -0.      , -0.      ])
```

This HOMO of *T<sub>d</sub>* methane is built from the carbon p<sub>x</sub> function only ([chapter 3](3_Visual_Input.ipynb)).

### `localized_orbitals(log_file)` and `localized_fock(log_file)`

With `LOCAL=RUEDNBRG` (or `BOYS`) in `$CONTRL`, *GAMESS* also prints **localized orbitals**: one orbital per bond or lone pair. `localized_orbitals()` returns `(labels, coefficients)` in the same layout as `molecular_orbitals()`. Localized orbitals have no energy or symmetry label.

`localized_fock()` returns the Fock matrix written in the localized valence orbitals as a square `numpy` array. Its diagonal holds the energy of each localized orbital; the off-diagonal numbers show how strongly two of them interact. Diagonalizing it (`np.linalg.eigvalsh(fock)`) gives back the canonical orbital energies.

### `energy_levels(ax, x, energies, color="tab:blue", labels=None)`

Draws orbital energies as short horizontal lines, the skeleton of an MO diagram. Degenerate levels are drawn side by side. `ax` is a *matplotlib* axes, `x` is where the column of levels starts, and `labels` (optional) are written to the left of each level.

```python
import matplotlib.pyplot as plt

mo = gt.molecular_orbitals("runs/ch2/water_321G.log")
fig, ax = plt.subplots(figsize=(3, 4))
gt.energy_levels(ax, 0, mo["energies"][1:7], labels=mo["symmetries"][1:7])
ax.set_xticks([])
ax.set_ylabel("orbital energy (hartree)")
plt.show()
```

Call it again with a larger `x` to put a second column beside the first, as in [chapter 3](3_Visual_Input.ipynb).

### `atomic_charges(log_file)`

The last population analysis, as `(atom, Mulliken charge, Löwdin charge)` for each atom.

```python
gt.atomic_charges("runs/ch2/water_321G.log")
```

```text
[('O', -0.732848, -0.470343), ('H', 0.366424, 0.235171), ('H', 0.366424, 0.235171)]
```

(sec-1e-inputs)=
## Writing New Input Files

Many exercises take the result of one job and use it to start the next one. These tools do the copy and paste that you would otherwise do in a text editor.

### `new_input(old_input, new_input_file, atoms=None, replacements=None)`

Writes a new input file based on an old one and returns its path.

- `replacements` swaps text, for example `{"GBASIS=AM1": "GBASIS=N21 NGAUSS=3"}`. If the old text is not in the file you get an error, so a typo can't slip through unnoticed.
- `atoms` replaces the coordinates in the `$DATA` group. The title line and the symmetry line are kept.

The usual pattern is to carry an optimized structure up to a higher level of theory:

```python
am1_log = gt.run_gamess(INPUTS / "water_AM1_U.inp")

inp = gt.new_input(INPUTS / "water_AM1_U.inp", RUNS / "water_321_U.inp",
                   atoms=gt.final_geometry(am1_log, unique=True),
                   replacements={"GBASIS=AM1": "GBASIS=N21 NGAUSS=3"})
log_321 = gt.run_gamess(inp)
```

```{note}
Match `unique=` to the input. With symmetry (any point group other than `C1`), the `$DATA` group holds only the unique atoms, so use `unique=True`. For `C1`, use all atoms. `atoms` works for inputs with Cartesian coordinates (`COORD=UNIQUE` or `CART`), not for a Z-matrix.
```

An input line must be shorter than 80 characters. If a replacement makes a line long, put `\n   ` in the new text to start a new line inside the group.

### `count_unique_atoms(input_file)`

The number of atom lines in the `$DATA` group. With symmetry this is the number of unique atoms; *GAMESS* makes the rest. Benzene in *D<sub>6h</sub>* needs 2, in *C<sub>1</sub>* all 12.

### `dat_group(dat_file, group, occurrence=-1)`

Copies one group, such as `"$HESS"`, `"$VEC"` or `"$ZMAT"`, out of the `.dat` file that *GAMESS* writes beside the log file. A `.dat` file can hold several copies of a group (one per step); by default you get the last one, from the final structure.

```python
hess = gt.dat_group(RUNS / "SN2_D3h_H2O_321G_HESS.dat", "$HESS")
print(hess[:160])
```

```text
 $HESS
ENERGY IS     -955.6969584957 E(NUC) IS      107.7130904566
 1  1 7.24722957E-03 4.72746048E-09 1.40751901E-03 1.64032681E-03 6.23231002E-09
```

The `.dat` file has the same name as the log file, so `log.with_suffix(".dat")` finds it.

### `add_group(input_file, group_text, new_input_file=None)`

Pastes a group (for example one from `dat_group()`) at the end of an input file. Without `new_input_file` the input file itself is changed.

```python
gt.add_group(inp, gt.dat_group(old_log.with_suffix(".dat"), "$VEC"))
```

### `saddle_input(hessian_input, hessian_log, new_input_file)`

The second step of a **transition state** search. Takes the input of a finished `RUNTYP=HESSIAN` job, changes it to `RUNTYP=SADPOINT`, and pastes in the `$HESS` group from that job's `.dat` file, so the saddle-point search starts with the exact force constants.

```python
hess_log = gt.run_gamess(hess_inp)
sadl_inp = gt.saddle_input(hess_inp, hess_log, RUNS / "SN2_D3h_321G_SADL.inp")
sadl_log = gt.run_gamess(sadl_inp)
```

### `irc_inputs(template, saddle_log, name, run_folder=None)`

The third step: follow the reaction path downhill from the transition state in both directions. It takes an IRC template (`RUNTYP=IRC`, `C1` symmetry, `FORWRD=.TRUE.` in `$IRC`) and writes two files into the run folder:

- `name.inp` with the atoms of the located saddle point and its `$HESS` group, and
- `name_R.inp`, the same with `FORWRD=.FALSE.` for the reverse direction.

It returns both paths.

```python
forward, reverse = gt.irc_inputs(INPUTS / "SN2_D3h_321G_IRC.inp", sadl_log,
                                 "SN2_D3h_321G_IRC")
irc_logs = [gt.run_gamess(f) for f in (forward, reverse)]
```

[Chapter 9](9_Solvent.ipynb) uses all three steps for the S<sub>N</sub>2 reaction.

(sec-1e-paths)=
## Vibrations and Reaction Paths

### `frequencies(log_file)`

The vibrational frequencies in cm⁻¹ from the last normal-mode table (`RUNTYP=HESSIAN`, or `HSSEND=.TRUE.` after an optimization). **Imaginary frequencies are returned as negative numbers.** A minimum has none; a transition state has exactly one. The six near-zero values for translation and rotation are included.

```python
freqs = gt.frequencies(RUNS / "SN2_D3h_H2O_321G_HESS.log")
[f for f in freqs if f < 0]
```

```text
[-345.51]
```

### `irc_points(log_file, bonds=((1, 3), (2, 3)))`

Reads one IRC run (one direction). Returns one dictionary per point with the `stride` (distance along the path from the transition state, in √amu·bohr), the `energy` in hartree, and the length of each bond in `bonds`, named `R(i,j)`.

```python
gt.irc_points(RUNS / "SN2_D3h_H2O_321G_IRC.log")[:2]
```

```text
[{'stride': 0.0, 'energy': -955.6969739956, 'R(1,3)': 2.3924399, 'R(2,3)': 2.3895381},
 {'stride': 0.29996, 'energy': -955.6971679, 'R(1,3)': 2.441993, 'R(2,3)': 2.3401237}]
```

Point 0 is the transition state. Its energy is the first `FINAL` energy in the log file, so set `TSENGY=.TRUE.` in `$IRC`. The bond lengths come from the internal-coordinate table, so the job needs `NZVAR`.

### `irc_table(forward_log, reverse_log, bonds=((1, 3), (2, 3)), names=None)`

Joins the forward and reverse runs into one *pandas* table that covers the whole path: the reverse strides become negative, the transition state appears once, the rows are sorted, and `E(kJ/mole)` is the energy relative to the transition state. `names` renames the bond columns.

```python
data = gt.irc_table(RUNS / "SN2_D3h_H2O_321G_IRC.log", RUNS / "SN2_D3h_H2O_321G_IRC_R.log",
                    names={"R(1,3)": "C-Cl1", "R(2,3)": "C-Cl2"})
data.head(3)
```

```text
    stride      energy  E(kJ/mole)     C-Cl1     C-Cl2
0 -4.94483 -955.705799  -23.169787  1.958442  3.111766
1 -4.78000 -955.705798  -23.167949  1.959227  3.098834
2 -4.48232 -955.705773  -23.101524  1.961550  3.062479
```

The table is ready to plot (`data.plot("stride", "E(kJ/mole)")`) or to save (`data.to_csv(...)`). The [data cleaning notebook](10_Solvent_IRC_Plots.ipynb) builds this table step by step before handing the job to `irc_table()`.

### `irc_path(log_file)`

Another way to read an IRC run, when you want the whole structure at each point rather than a few bond lengths. Returns a list of `(s, energy, atoms)`, where `atoms` is in the same form as `final_geometry()`, so `distance()` and `angle()` work on it.

```python
for s, energy, atoms in gt.irc_path(log):
    print(f"{s:7.3f} {energy:.6f} {gt.distance(atoms, 1, 3):.3f}")
```

## Putting It Together

Most chapters use the tools in one of three patterns.

**A ladder of methods** ([chapter 2](2_SmallMolecules.ipynb)): optimize cheaply, then carry the structure up.

```python
log = gt.run_gamess(INPUTS / "water_AM1_U.inp")
for basis, tag in [("GBASIS=N21 NGAUSS=3", "321_U"), (BASIS_6311, "6311_U")]:
    inp = gt.new_input(INPUTS / "water_AM1_U.inp", RUNS / f"water_{tag}.inp",
                       atoms=gt.final_geometry(log, unique=True),
                       replacements={"GBASIS=AM1": basis})
    log = gt.run_gamess(inp)
    print(tag, gt.final_energy(log))
```

**A scan** ([chapters 5](5_Rotation_Profiles.ipynb) and [7](7_Butadiene.ipynb)): one template, many jobs, one table.

```python
results = []
for angle in range(0, 181, 10):
    inp = gt.substitute(INPUTS / "butadiene_scan_template.inp",
                        RUNS / f"butadiene_scan_{angle:03d}.inp", {"ANGLE": f"{angle:.1f}"})
    log = gt.run_gamess(inp, rerun=False)
    results.append((angle, gt.final_energy(log)))
```

**A transition state and its reaction path** ([chapters 7](7_Butadiene.ipynb), [8](8A_Diels_Alder.ipynb) and [9](9_Solvent.ipynb)): Hessian → saddle point → check for one imaginary frequency → IRC both ways → table.

```python
hess_log = gt.run_gamess(hess_inp)
sadl_log = gt.run_gamess(gt.saddle_input(hess_inp, hess_log, RUNS / "ts_SADL.inp"))
print([f for f in gt.frequencies(sadl_log) if f < 0])      # expect exactly one
forward, reverse = gt.irc_inputs(INPUTS / "ts_IRC.inp", sadl_log, "ts_IRC")
data = gt.irc_table(gt.run_gamess(forward), gt.run_gamess(reverse))
```

## When Things Go Wrong

| Symptom | What to try |
| :--- | :--- |
| `FileNotFoundError: cannot find ...inp` | The path is relative to the notebook's folder. Check `INPUTS` and the file name. |
| A job prints `FAILED` at once | Run `gt.check_installation()` and fix every `FIX` line. Then look at the end of the log: `gt.excerpt(log, "ERROR", before=5)` or `print(log.read_text()[-2000:])`. |
| `semget` or shared-memory errors on a Mac | The Mac was restarted and the shared-memory limit was reset. See the compiling pages. |
| `ValueError: '...' is not in ...inp` | A `replacements` key in `new_input()` doesn't match the file exactly. Check spaces and spelling. |
| `ValueError: no molecular orbitals found` | The job used `NPRINT=-5`, or it failed before the orbitals were printed. |
| `internal_coordinates()` returns `[]` | Set `NZVAR` in `$CONTRL` and add a `$ZMAT` group (or use a Z-matrix input). |
| `IndexError` in `final_energy()` or `wall_time()` | The job didn't finish; check `gt.terminated_normally(log)`. |
| A notebook re-runs long jobs | Use `gt.run_gamess(inp, rerun=False)` to reuse finished log files. |
| Changes to `gamess_settings.py` are ignored | Restart the kernel. |

## Reading the Code

You don't need to read `gamess_tools.py` to use it, but you are encouraged to: every tool is a short function written to be read. Most of them do the same three things: read the log file, find a line that *GAMESS* always prints in the same words, and turn the numbers on it into *Python* numbers. Once you see the pattern, you can write a tool of your own for any part of the log file that this library doesn't cover yet.

::::{dropdown} The complete gamess_tools.py
:::{literalinclude} gamess_tools.py
:language: python
:::
::::

## AI Statement

This page has no counterpart in the original book. It was written by Claude (Anthropic) at the author's request as a user's manual for `gamess_tools.py` and `gamess_settings.py`, the helper module added to this Python edition. It replaces an earlier version of the page that walked through the code section by section. The tools `count_unique_atoms`, `shortest_distance`, `pi_orbitals`, `p_coefficients`, `saddle_input`, `irc_inputs`, `irc_table`, `plot_optimization`, `energy_levels` and the constant `HARTREE_TO_KJMOL` were first written by AI inside the chapter notebooks and were moved into `gamess_tools.py` at the same time, so that every notebook can use them. All text and examples on this page were written by AI; the example output was produced by running the tools on the log files of this book's chapters.
