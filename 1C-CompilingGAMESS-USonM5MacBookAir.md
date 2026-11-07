# Compiling GAMESS-US 2021 R2

I have never been able to successfully compile GAMESS on either Intel or Apple silicon machines. But now Claude is here to help. I fed the errors to Claude and used the solutions offered. There were a few wrong turns but in the end I had a working copy of the executable.

In the end, I asked Claude to gather all my steps into a single set of instructions. The next project is to compile again using these instructions and confirm that everything still works. 

First I compiled a source from 2021. It was what I had on hand. The instructions are below.

## Overview

These steps build GAMESS-US from the `gamess-current.tar.gz` release on an Apple Silicon MacBook Air (macOS 27) and produce `gamess.00.x` in `~/gamess`. They record the exact path that worked, including three fixes to the GAMESS scripts and source that the stock release needs on this Mac.

| Setting | Value used |
| --- | --- |
| Target | `mac64` |
| Fortran compiler | Homebrew `gcc@12` (gfortran 12), entered as version 12.1 |
| Math library | `vecLib` (Apple Accelerate) |
| DDI communication | `sockets`, SystemV shared memory |
| Optional plug-ins | VB2000 on (default); LibXC, MDI, OpenMP, NEO, NBO, Tinker off |
| Version number | `00` |
| Install and build folder | `/Users/yourname/gamess` |
| Scratch folder | `/Users/yourname/scr` |

Status: the link step succeeded. The first test (`exam01`) had not yet completed a normal run when these notes were written; it was last blocked by the shared-memory limit and leftover scratch files (steps 8 and 10).

## Step 1: Prerequisites

Install Apple's command-line tools and gfortran 12, then make plain `gfortran` and the macOS SDK visible to every build step. gfortran 16 was tried first, but GAMESS's `config` doesn't recognise it, so these notes use 12.

```bash
xcode-select --install
brew install gcc@12
gfortran-12 --version          # should report 12.x
```

`gcc@12` only installs `gfortran-12`, so link a plain `gfortran` to it in `~/bin`:

```bash
mkdir -p ~/bin
ln -sf "$(brew --prefix)/bin/gfortran-12" ~/bin/gfortran
```

Add these two lines to `~/.zshrc`, then open a new Terminal window or run `source ~/.zshrc`:

```bash
export PATH="$HOME/bin:$PATH"
export SDKROOT=$(xcrun --show-sdk-path)
```

Check both in the same window you'll build from:

```bash
which gfortran        # /Users/yourname/bin/gfortran
gfortran --version    # 12.x
echo $SDKROOT         # .../CommandLineTools/SDKs/MacOSX.sdk
```

- Without the `PATH` line, every module fails with `gfortran: Command not found`.
- Without `SDKROOT`, the link step fails with `ld: library 'System' not found`.

## Step 2: Get and unpack the source

Register on the Iowa State GAMESS site, accept the license and download `gamess-current.tar.gz`. Check that the archive has a single `gamess/` folder at the top, then unpack it into `~/gamess`:

```bash
tar -tzf ~/Downloads/gamess-current.tar.gz | head     # every line should start with gamess/
mkdir ~/gamess && cd ~/gamess
tar -xzf ~/Downloads/gamess-current.tar.gz --strip-components=1
```

`--strip-components=1` drops the archive's top `gamess/` folder, so the files land directly in `~/gamess` rather than `~/gamess/gamess`.

## Step 3: Run config

Run `./config` from `~/gamess` and give these answers. It writes them to `install.info`.

| Prompt | Answer |
| --- | --- |
| Target machine | `mac64` |
| GAMESS directory | `/Users/yourname/gamess` |
| Build directory | `/Users/yourname/gamess` |
| Version number | `00` |
| Fortran compiler | `gfortran` |
| gfortran version | `12.1` |
| Math library | `vecLib` |
| Communication library | `sockets` |
| LibXC, MDI, MSU-CC, LIBCCHEM, OpenMP, VM2 | no |

`config` will warn `OS X version number is unrecognized: 27` and fall back to El Capitan settings. That's harmless here.

To check what was recorded:

```bash
grep -v '^#' install.info | grep setenv
```

## Step 4: Build DDI

DDI is GAMESS's parallel communication layer. Build it first:

```bash
cd ~/gamess/ddi
./compddi >& compddi.log
mv ddikick.x ..          # if it was built here rather than in ~/gamess
cd ~/gamess
ls -l ddi/libddi.a ddikick.x
```

It has worked when both `ddi/libddi.a` and `ddikick.x` exist.

To look for real errors, search for `error:`. A plain search for `error` also matches the source file `ddikick_error.c`:

```bash
grep -n -i "error:" ddi/compddi.log
```

## Step 5: Patch three files before compiling

The stock release needs three small fixes on this Mac. Make a backup of each file first, for example `cp comp comp.orig`.

| File | Problem | Symptom without the fix |
| --- | --- | --- |
| `compall`, line 718 | Missing `if`, a typo in the distributed file | `Badly placed ()'s`; `compall` stops before VB2000 |
| `comp`, `mac64` section near line 2993 | gfortran 12 rejects undersized array arguments in `qfmm` and `vscf` | `Actual argument contains too few elements for dummy argument` |
| `vb2000/compvb2c`, line 77 | Looks for `malloc.h` in `/usr/include`, which no longer exists | `fatal error: 'malloc.h' file not found` |

**1. `compall`.** Add the missing `if`:

```bash
sed -i '' 's/^(\$GMS_PHI != none)/if ($GMS_PHI != none)/' compall
grep -n "GMS_PHI" compall     # should show: if ($GMS_PHI != none) set VB2000=false
```

**2. `comp`.** In the `mac64` section, find the line that adds `-std=legacy` for `vb2000` (about line 2993). Add two lines after it so it reads:

```
         if ($MODULE == nameio) set EXTRAOPT="$EXTRAOPT -std=legacy"
         if ($MODULE == vb2000) set EXTRAOPT="$EXTRAOPT -std=legacy"
         if ($MODULE == qfmm)   set EXTRAOPT="$EXTRAOPT -std=legacy"
         if ($MODULE == vscf)   set EXTRAOPT="$EXTRAOPT -std=legacy"
```

The GAMESS code is fine; `-std=legacy` turns this gfortran check back into a warning.

**3. `vb2000/compvb2c`.** Change line 77 to point at the header inside the Xcode SDK. Use double quotes so the backticks run:

```
if ($TARGET == mac64)    set extraflags="-DLINUX64 -m64 -I`xcrun --show-sdk-path`/usr/include/malloc"
```

Check the two edited scripts:

```bash
grep -n "qfmm\|vscf" comp | grep legacy
grep -n "mac64" vb2000/compvb2c
```

## Step 6: Compile with compall

Compiling all of GAMESS took about 34 minutes. Run it in the same Terminal window where you checked `gfortran` and `SDKROOT`:

```bash
cd ~/gamess
./compall >& compall.log &
tail -f compall.log            # Ctrl+C stops watching, not the build
```

When it prints `done with all compilations`, check for failures:

```bash
grep -c "Compilation failure" compall.log            # want 0
grep -n -E "Error:|error:|Fatal|Command not found" compall.log
ls object/qfmm.o object/vscf.o object/vb2c.o
```

`-Werror=align-commons` appears on every compile line, so search for `Error:` or `error:` rather than plain `error`. A `vb2c` failure doesn't show up as `Compilation failure`, so check that `vb2c.o` exists.

These messages are expected and harmless:

- `gfortran 11 on the Apple M1 does not support quadruple precision`: quad precision is switched off in `qeigen`.
- Two `-Wdeprecated-non-prototype` warnings from `vb2c.c`.

To recompile a single file after a fix, run `./comp <name>`, for example `./comp qfmm`. There's no need to rerun all of `compall`.

## Step 7: Link with lked

Linking takes under a minute and produces `gamess.00.x`, about 29 MB:

```bash
echo $SDKROOT                  # must not be blank
./lked gamess 00 >& lked.log
tail -3 lked.log               # The linking of GAMESS to binary gamess.00.x was successful.
ls -l gamess.00.x
```

The `00` is only a label in the program's name. It must match the version number you give `rungms` and `runall`. GAMESS's own `instructions.txt` uses `01` as an example, but `00` is the default in `rungms`, so it needs no extra edits.

If the log shows `ld: library 'System' not found`, `SDKROOT` isn't set in that window (step 1).

## Step 8: Raise the shared-memory limits

Even the smallest test asks for about 160 MB of SystemV shared memory, and macOS's default limit is only a few MB. Without this step, every job fails with `shmget returned an error` and `Error EINVAL`. Set the limit to about half your RAM:

| Mac's RAM | `kern.sysv.shmmax` (bytes) | `kern.sysv.shmall` (4 KB pages) |
| --- | --- | --- |
| 16 GB | 8589934592 | 2097152 |
| 24 GB | 12884901888 | 3145728 |
| 32 GB | 17179869184 | 4194304 |

```bash
sudo sysctl -w kern.sysv.shmmax=8589934592   # 16 GB example; set shmmax first
sudo sysctl -w kern.sysv.shmall=2097152
sysctl kern.sysv.shmmax kern.sysv.shmall     # confirm
```

- These are ceilings, not reservations. RAM is only used while a GAMESS job runs.
- They reset on every reboot, so run the two commands again after restarting.
- If a value is refused, reboot and set them before running anything else.
- A crashed job can leave segments behind. List them with `ipcs -m` and remove one with `ipcrm -m <id>`.

## Step 9: Configure rungms

Only four lines near the top of `rungms` (lines 83–86) need editing:

```
set TARGET=sockets
set SCR=/Users/yourname/scr
set USERSCR=/Users/yourname/scr
set GMSPATH=/Users/yourname/gamess
```

- Make sure the scratch folder exists: `mkdir -p ~/scr`.
- Leave `JOB`, `VERNO`, `NCPUS` and `LOGN` alone. They come from the command line: `./rungms <job> <version> <ncpus>`. Without them, `rungms` uses `VERNO=00` and `NCPUS=1`.
- The `hostname == ...iastate.edu` lines and the PBS/SGE scheduler code don't apply to a Mac and can stay as they are.
- When running several processes, `export VECLIB_MAXIMUM_THREADS=1` stops Apple's math library from oversubscribing the cores.

## Step 10: Run the tests

Start with one quick test. Clear leftover scratch files first, because `rungms` refuses to start a job when files from an earlier run of the same name are still there (`Please save, rename, or erase these files from a previous run`).

```bash
cd ~/gamess
rm -f ~/scr/exam01.*
./rungms exam01 00 1 >& exam01.log
grep -i -E "normally|gracefully" exam01.log
```

A good run prints `EXECUTION OF GAMESS TERMINATED NORMALLY` and `ddikick.x: exited gracefully`. Then run the full suite and check it against the reference answers:

```bash
rm -f ~/scr/exam*
./runall 00 >& runall.log
tests/standard/checktst                 # every test should say Passed
grep -i -L normally exam*.log           # lists any test that did not finish
```

- [ ] `exam01` finishes normally
- [ ] `runall` completes and `checktst` reports every test Passed

If some tests fail with wrong energies, note which ones. A routine may need recompiling at a lower optimisation level (`-O0` or `-O1`).

## Everyday use: a gms shortcut

The `tools/gms` script that ships with GAMESS is for Iowa State's cluster batch queues and isn't used on a Mac. Instead, add this function to `~/.zshrc`. It clears leftovers, runs the job and reports whether it finished:

```bash
# run a GAMESS job:  gms input[.inp] [ncpus]
gms() {
  local job="${1%.inp}"
  rm -f ~/scr/"$job".*
  ~/gamess/rungms "$job" 00 "${2:-1}" >& "$job.log"
  grep -q "TERMINATED NORMALLY" "$job.log" && echo "$job: finished normally" || echo "$job: FAILED, see $job.log"
}
```

Run it from the folder that holds the input file:

```bash
gms water          # water.inp on 1 core, output in water.log
gms water 4        # 4 cores
gms water 4 &      # in the background
```

After a reboot, raise the shared-memory limits again (step 8) before the first job.

## Troubleshooting quick reference

| Message | Cause | Fix |
| --- | --- | --- |
| `config` doesn't list gfortran 16 | Too new for this release | Use `gcc@12` and answer `12.1` (step 1, step 3) |
| `gfortran: command not found` after installing `gcc@12` | `gcc@12` only provides `gfortran-12` | Link `~/bin/gfortran` and add `~/bin` to `PATH` (step 1) |
| `OS X version number is unrecognized: 27` | `config` predates macOS 27 | Harmless; continue |
| `gfortran: Command not found` on every module in `compall.log` | `PATH` not set in the build window | `source ~/.zshrc`, `hash -r`, rerun `compall` |
| `Badly placed ()'s` at the end of `compall.log` | Typo at line 718 of `compall` | Step 5, fix 1 |
| `Actual argument contains too few elements` (`qfmm`, `vscf`) | gfortran 12 strictness | Step 5, fix 2, then `./comp qfmm` and `./comp vscf` |
| `'malloc.h' file not found` (`vb2c`) | Header moved into the Xcode SDK | Step 5, fix 3, then `./comp vb2c` |
| `ld: library 'System' not found` | `SDKROOT` not set | `export SDKROOT=$(xcrun --show-sdk-path)`, relink |
| `shmget returned an error` / `Error EINVAL` | macOS shared-memory limit too low | Step 8 |
| `Please save, rename, or erase these files from a previous run` | Leftovers in `~/scr` | `rm ~/scr/<job>.*` |
| `IEEE_UNDERFLOW_FLAG` / `IEEE_DENORMAL` notes | Normal floating-point notices | Ignore |

When reading any log, fix the first real error; later ones are usually knock-on effects.

## Using this build from the notebooks

The notebooks in this book run *GAMESS* through `gamess_tools.run_gamess()` instead of the `gms` shell function above. Set `GAMESS_DIR` in `gamess_settings.py` to your build folder (here `"~/gamess"`), add the two extra `rungms` lines described in [Editing RUNGMS](1_Setup.ipynb), and run the test cells of the setup notebook.

## AI Statement

This page is copied from `1C-CompilingGAMESS-USonM5MacBookAir.md` in the original book. It stays a Markdown page because compiling *GAMESS* has to happen in the terminal. The original page was itself assembled by Claude (Anthropic) from the author's build session, with the author's introduction.

- **Original text kept (about 95 %).** All build steps, tables and troubleshooting notes are unchanged.
- **Changed by AI in this version.** Personal paths were generalized to `/Users/yourname/...`. The section "Using this build from the notebooks" is new.
