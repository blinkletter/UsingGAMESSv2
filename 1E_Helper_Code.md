# The Python Helper Files

Every notebook in this book starts with `import gamess_tools as gt`. That one line loads a small library of functions that **run *GAMESS*** and **read its log files**, so that the notebooks never need the terminal. The library is split into two files that sit next to the notebooks:

| File | What it holds | Do you edit it? |
| :--- | :--- | :--- |
| `gamess_settings.py` | Where *GAMESS* lives on **your** computer | **Yes, once** |
| `gamess_tools.py` | The functions used by the notebooks | No, but do read it |

This page lists the code of both files and describes what each function does. You don't need to understand every line before you start. Come back here when a notebook uses a function and you want to know what happens inside it.

```{tip}
Every function has a **docstring**, the text in triple quotes under the `def` line. In a notebook you can read it without opening the file: type `gt.final_energy?` in a cell and run it.
```

## `gamess_settings.py`

This is the only file you change. It holds four settings. The comments explain each one.

```{literalinclude} gamess_settings.py
:language: python
```

| Setting | Meaning |
| :--- | :--- |
| `GAMESS_DIR` | The folder that holds `rungms`, `gamess.00.x`, `auxdata/` and `scr/`. `~` means your home folder. |
| `RUN_SCRIPT` | The name of the run script in that folder, normally `rungms`. |
| `VERSION` | The version number in the name of the program, the `00` in `gamess.00.x`. |
| `NCPUS` | How many CPU cores a job uses unless you ask for another number. |

If the environment variable `GAMESS_DIR` is set before *Jupyter* starts, it wins over the value in the file. After any change, **restart the notebook kernel**, because *Python* reads the file only once.

## `gamess_tools.py`

The file starts with a docstring that works as a table of contents, followed by the modules it needs. `subprocess` starts programs, `pathlib` handles files and folders, `re` finds patterns in text, and `numpy` does the vector arithmetic.

```{literalinclude} gamess_tools.py
:language: python
:end-before: # -----
```

The rest of this page goes through the file section by section.

### Settings

These functions turn the settings file into paths and check that your installation is complete.

**`gamess_dir()`** returns the *GAMESS* folder as a `Path`. It takes the environment variable `GAMESS_DIR` if one is set, otherwise the value from `gamess_settings.py`, and expands `~` into your home folder.

**`run_script()`** returns the full path of the `rungms` script inside that folder.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def gamess_dir(
:end-before: def shared_memory_limits(
```

**`shared_memory_limits()`** only matters on a Mac. *GAMESS* shares memory between its processes, and *MacOS* allows only a few megabytes of shared memory after every restart. The function asks the system for the two limits with the `sysctl` command and returns them in bytes. On *Linux* or *Windows* it returns `None`.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def shared_memory_limits(
:end-before: def check_installation(
```

**`check_installation()`** prints a checklist with `OK` or `FIX` on each line: is the *GAMESS* folder there, can the run script be executed, does the program `gamess.00.x` exist, are the `auxdata` and `scr` folders present, and (on a Mac) is the shared-memory limit at least 1 GB. It returns `True` when every line is `OK`. Run it first whenever jobs start failing.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def check_installation(
:end-before: # -----
```

### Running GAMESS

**`terminated_normally(log_file)`** returns `True` when the log file exists and contains the words `TERMINATED NORMALLY`. *GAMESS* writes them as the last thing it does after a successful job.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def terminated_normally(
:end-before: def run_gamess(
```

**`run_gamess(input_file)`** is the heart of the library. It does what you would do in a terminal with the `gms` script:

1. Finds the input file and takes the job name from it (`water` from `water.inp`).
2. Creates the run folder for the results: `RUN_FOLDER`, which each notebook sets to its chapter folder (for example `runs/ch2`), or the `run_folder` you choose.
3. With `rerun=False`, skips the job if a finished log file is already there. This saves time when you run a notebook a second time.
4. Deletes scratch files that an interrupted run of the same job left in `scr/`.
5. Sets the variable `GMS_USERSCR` so that `rungms` writes the `.dat` and `.trj` files into the run folder, then starts `rungms` with `subprocess.run`. Everything *GAMESS* prints goes into the `.log` file.
6. Prints whether the job finished normally and returns the path of the log file.

The optional arguments `ncpus`, `version` and `log_file` override the values from `gamess_settings.py` and the default log name.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def run_gamess(
:end-before: # -----
```

### Reading text files

These two functions search and edit text files. Their names come from the *Unix* tools `grep` and `sed`, which do the same jobs in a terminal.

**`grep(text, file)`** returns a list of every line in the file that contains `text`, just like `grep "text" file` in the terminal. Many of the functions below start with it.

**`substitute(template, new_file, replacements)`** copies a file and swaps text on the way, like `sed "s/OLD/NEW/"`. The replacements are a dictionary such as `{"NUMBER": "100"}`. The notebooks use it to make a series of input files from one template, for example one per dihedral angle in a rotation scan.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def grep(
:end-before: # -----
```

### Reading GAMESS log files

A geometry optimization prints one `NSERCH` line per step. `NSERCH_LINE` is a **regular expression**, a pattern that picks the step number and the energy out of such a line.

**`nserch_energies(log_file)`** returns a list of `(step, energy)` pairs, one per optimization step. Plot them to watch the energy fall as *GAMESS* searches for the minimum.

**`optimization_steps(log_file)`** returns more for each step: `(step, energy, largest gradient, RMS gradient)`. The gradients (hartree/bohr) show how far the structure is from a stationary point. The last item belongs to the final structure.

**`final_energy(log_file)`** returns the number from the last `FINAL ... ENERGY IS` line, in hartree, or `None` if there is no such line.

**`excerpt(log_file, text)`** prints a piece of the log file around the line that contains `text`, with line numbers. By default it shows the last match and the 20 lines after it. Use `before`, `after` and `occurrence` to see more or to pick another match. It is the notebook version of scrolling through the log file in a text editor.

```{literalinclude} gamess_tools.py
:language: python
:start-at: # Matches lines such as:
:end-before: # -----
```

### Geometries

**`_atom_table(lines, start)`** is a helper for the functions below; the leading underscore means it is not meant to be called from a notebook. *GAMESS* prints a geometry as a header, two lines of column titles and dashes, and then one line per atom with five entries: name, nuclear charge, *x*, *y* and *z*. The function reads atom lines until one no longer has five entries.

**`final_geometry(log_file)`** returns the last geometry in the log file as a list of `(name, charge, x, y, z)` tuples, in ångström. For an optimization this is the optimized structure. With `unique=True` you get only the **symmetry-unique** atoms, the ones that go into the `$DATA` group of an input file that uses symmetry.

**`atom_lines(atoms)`** turns such a list back into text lines in the format of the `$DATA` group, ready for a new input file.

**`distance(atoms, i, j)`** returns the distance between atoms `i` and `j` in ångström. **`angle(atoms, i, j, k)`** returns the angle i–j–k in degrees, with atom `j` at the vertex. Atoms are numbered from 1, as in the log file. Both use `numpy` vectors: a distance is the length of the difference of two position vectors, and an angle comes from the dot product of two bond vectors.

**`internal_coordinates(log_file)`** reads the last table of internal coordinates. *GAMESS* prints it only when `NZVAR` is set in `$CONTRL`. Each entry is `(type, atoms, value)`, for example `("STRETCH", (1, 2), 1.096)`. Stretches are in ångström, bends and torsions in degrees.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def _atom_table(
:end-before: # -----
```

### Molecular orbitals

**`occupied_orbitals(log_file)`** returns the number of occupied alpha orbitals. For a closed-shell (RHF) molecule this is also the number of the **HOMO**.

**`_is_int_line(line)`** is a helper. It is `True` for a line that holds only whole numbers, such as the orbital numbers above each block of an orbital table.

**`_orbital_blocks(lines, start)`** is the helper that does the hard work. *GAMESS* prints orbitals five columns at a time, as the docstring shows. For each block the function reads the orbital numbers, the energies and symmetry labels, and then one row of coefficients per basis function. At the end it glues the blocks side by side into one `numpy` array. Large coefficients can run into each other in the log file (`-10.340924-172.072365`), so the numbers are found with a regular expression that expects six decimals instead of being split at spaces.

**`molecular_orbitals(log_file)`** returns the last set of orbitals in the log file as a dictionary with the orbital `energies`, the `symmetries` labels, the basis-function `labels` (such as `C 1 S` or `H 2 X`) and the `coefficients`. In the coefficient array, column 0 is orbital 1 and each row is one basis function.

**`localized_orbitals(log_file)`** does the same for **localized orbitals** (printed when `LOCAL=` is set in `$CONTRL`). These have no energy or symmetry label, so it returns only `(labels, coefficients)`.

**`localized_fock(log_file)`** reads the Fock matrix written in the localized orbitals and returns it as a square `numpy` array. The diagonal holds the energy of each localized orbital and the off-diagonal elements show how strongly two localized orbitals interact. The table is printed as a triangle, so every value is stored in two places to fill the square.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def occupied_orbitals(
:end-before: # -----
```

### Writing new input files

Many exercises take the result of one job and use it to start the next one. These functions do the copy and paste that you would otherwise do in a text editor.

**`new_input(old_input, new_input_file, atoms, replacements)`** writes a new input file based on an old one. `replacements` swaps keywords, for example `{"GBASIS=AM1": "GBASIS=N21 NGAUSS=3"}`, and raises an error if the old text is missing, so a typo can't pass unnoticed. `atoms` replaces the coordinates in the `$DATA` group, for example with `final_geometry(log, unique=True)`. The title line and the symmetry line are kept. For a symmetry other than `C1`, *GAMESS* expects a blank line after the symmetry line, so the atoms start one line later.

**`add_group(input_file, group_text)`** adds a group, such as a `$HESS` or `$VEC` group, to the end of an input file.

**`dat_group(dat_file, group)`** copies one group, for example `"$ZMAT"`, `"$VEC"` or `"$HESS"`, out of the `.dat` file that *GAMESS* writes beside the log file. A `.dat` file can contain several copies of a group; by default the last one, from the final structure, is returned.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def new_input(
:end-before: # -----
```

### Vibrations and reaction paths

**`frequencies(log_file)`** returns the vibrational frequencies in cm⁻¹ from the last normal-mode table. *GAMESS* marks an **imaginary frequency** with an `I` after the number; the function returns it as a negative number. A minimum has no negative values and a transition state has exactly one. The six near-zero values for translation and rotation are included.

**`irc_path(log_file)`** reads an intrinsic reaction coordinate run (`RUNTYP=IRC`). For each point along the path it returns `(s, energy, atoms)`: the distance from the transition state in √amu·bohr, the energy in hartree, and the geometry in the same form as `final_geometry()`.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def frequencies(
:end-before: # -----
```

### Pi orbitals, charges and timing

**`p_character(mo, axis)`** takes the dictionary from `molecular_orbitals()` and, for each orbital, adds up the squared coefficients of the p functions along one axis and divides by the sum of all squared coefficients. For a planar molecule, choose the axis perpendicular to the plane: π orbitals give a number near 1 and σ orbitals give 0. This is a rough measure, but it is enough to find the π orbitals in a long list.

**`atomic_charges(log_file)`** reads the last population analysis and returns `(atom, Mulliken charge, Löwdin charge)` for each atom.

**`wall_time(log_file)`** returns how long the job took, in seconds of wall-clock time. Use it to compare the cost of different methods and basis sets.

**`irc_points(log_file, bonds)`** is a second way to read an IRC run, written for the solvent chapter. It returns one dictionary per point with the `stride` (the distance along the path), the `energy` and the length of each bond listed in `bonds`, such as `R(1,3)`. The bond lengths come from the internal-coordinate table, so the job needs `NZVAR`. Point 0 is the transition state; its energy comes from the first `FINAL` energy in the log, so set `TSENGY=.TRUE.` in `$IRC`. The result is ready to turn into a table or a plot of energy against bond length.

```{literalinclude} gamess_tools.py
:language: python
:start-at: def p_character(
```

## AI Statement

This page is new and has no counterpart in the original book. It was written by Claude (Anthropic) at the author's request to document the helper module `gamess_tools.py` and the settings file `gamess_settings.py`, which were added to this Python edition of the book. The code is shown directly from the two files with `literalinclude`, so the listings stay in step with the files. All descriptive text on this page was written by AI; none of it comes from the original author's pages.
