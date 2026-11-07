# Compiling GAMESS-US 2024 R2

After getting GAMESS 2023 R2 to compile on my Mac, I repeated the process with the 2024 R2 release (v2024.2.1). This time I started from the 2023 instructions and Claude worked out what had changed. The changes were small: a different gfortran version answer, a different line number in `lked`, and some path settings in `rungms`. I also went straight to the faster OpenBLAS math library instead of building the slow reference library first.

The steps below are written so that a student with an Apple Silicon Mac (M1 to M5) can follow them from start to finish.

Tested result: all 49 standard tests pass (`checktst`: "All 49 test results are correct!").
Build folder used here: `~/gamess` (the archive unpacks into a folder called `gamess` in your home folder). If you use a different folder, change every `~/gamess` and `$HOME/gamess` below to match.

## Why the extra steps?

The stock GAMESS build assumes GNU tools and gives wrong answers with Apple's math library:

| Problem | Cause | Fix |
|---|---|---|
| `Makefile:120: missing separator` | macOS `make` is GNU Make 3.81 (no `undefine`) | Homebrew GNU make (`gmake`) |
| `sed: extra characters at the end of p command` | macOS `sed` is BSD sed | Homebrew GNU sed, first on PATH |
| `ld: library 'System' not found` | the linker can't find the macOS SDK | `export SDKROOT=$(xcrun --show-sdk-path)` |
| exam45-47 fail, `ERROR INFO: 4294967296` | Apple's Accelerate LAPACK uses 4-byte integers; GAMESS uses 8-byte | link OpenBLAS built with 8-byte integers (step 4) |
| many tests segfault in "LZ VALUE ANALYSIS" | Accelerate's complex BLAS (ZDOTC) uses an incompatible return convention | drop Accelerate completely (step 6) |
| OpenBLAS builds generic `ARMV8` kernels | CPU not auto-detected | `TARGET=VORTEX` (step 4) |
| OpenBLAS build ends in fatal errors | its own test programs fail to link with recent Xcode | build only `libs netlib` (step 4) |
| `rungms` can't find GAMESS | its default paths don't match your folders | edit three lines (step 7) |

---

## 1. Prerequisites (one time)

You need Homebrew (<https://brew.sh>). Then:

```zsh
xcode-select --install          # Command Line Tools (skip if already installed)
brew install gcc@13 make gnu-sed

# make "gfortran" point to gfortran-13
mkdir -p ~/bin
rm -f ~/bin/gfortran
ln -s /opt/homebrew/bin/gfortran-13 ~/bin/gfortran
```

Add these lines to `~/.zshrc`, then open a new terminal (or run `source ~/.zshrc`):

```zsh
export PATH="$HOME/bin:$PATH"
export PATH="$(brew --prefix)/opt/make/libexec/gnubin:$PATH"
export PATH="$(brew --prefix)/opt/gnu-sed/libexec/gnubin:$PATH"
export SDKROOT=$(xcrun --show-sdk-path)
```

Check:

```zsh
gfortran --version   # GNU Fortran 13.x
make --version       # GNU Make 4.x
sed --version        # GNU sed
echo $SDKROOT        # a path ending in MacOSX.sdk
```

All four checks must pass before you go on. Every later step depends on them.

## 2. Unpack the source

Download `gamess-current.tar.gz` from the GAMESS website (<https://www.msg.chem.iastate.edu/gamess/download.html>). You must register for a free licence first. These steps assume the file is in your `Downloads` folder.

```zsh
cd ~
cp ~/Downloads/gamess-current.tar.gz .
tar -xzf gamess-current.tar.gz
cd ~/gamess
head -5 VERSION.md       # expect v2024.2.1 (or newer)
```

The archive unpacks into `~/gamess`, so `config`, `Makefile` and `source/` are already in the right place. Run every command from here on inside `~/gamess` unless a step says otherwise.

## 3. Configure

```zsh
./config
```

The script asks a series of questions. Answer them as follows:

| Question | Answer |
|---|---|
| "please hit <ENTER> to go on" | Enter |
| target machine name | `mac64` |
| GAMESS directory, build directory, version | Enter (accept the defaults `~/gamess` and `00`) |
| gfortran version | `13.3` (see note below) |
| any "Hit <ENTER> to continue" message | Enter |
| optional plug-ins (yes/no questions) | `no` to every one |

Notes:

- Homebrew installs gfortran 13.4, but the script only accepts `13.1`, `13.2`, `13.3` or `14.1`. Enter `13.3`. It is the closest match and works.
- There is no math-library question for mac64. The script always sets `vecLib`. That is expected; step 5 overrides it.
- The script reads your macOS version. A new macOS (for example 27) shows as "unrecognized" and the script falls back to `11`. That is harmless.
- For mac64 there is no question about DDI; it uses `sockets`, which is what we want.

**Do not run `./config` again after step 5.** It rewrites `install.info` and undoes your edit.

## 4. Build OpenBLAS with 8-byte integers (about 5-15 min)

OpenBLAS contains both BLAS and LAPACK. Homebrew's `openblas` uses 4-byte integers, so it cannot be used. Build it from source:

```zsh
cd ~/gamess/3rd-party
curl -L -o OpenBLAS-0.3.28.tar.gz https://github.com/OpenMathLib/OpenBLAS/releases/download/v0.3.28/OpenBLAS-0.3.28.tar.gz
tar -xzf OpenBLAS-0.3.28.tar.gz
cd OpenBLAS-0.3.28
gmake -j4 TARGET=VORTEX INTERFACE64=1 USE_THREAD=0 USE_OPENMP=0 NO_SHARED=1 CC=clang FC=gfortran libs netlib 2>&1 | tee openblas-build.log
ls -l libopenblas*.a          # expect libopenblas_vortex-r0.3.28.a
gmake PREFIX=$HOME/gamess/3rd-party/openblas64 NO_SHARED=1 install 2>&1 | tee -a openblas-build.log
ls -l ../openblas64/lib/libopenblas.a
cd ~/gamess
```

What the flags mean:

- `TARGET=VORTEX`: kernels for Apple M-series chips.
- `INTERFACE64=1`: 8-byte integers. This is the essential one.
- `USE_THREAD=0 USE_OPENMP=0`: single-threaded. GAMESS runs in parallel with its own DDI processes, so threaded BLAS would overload the cores.
- `NO_SHARED=1`: static library only, so `gamess.00.x` does not depend on outside files.

Note: after `install`, `OpenBLAS-0.3.28/Makefile.conf` says `CORE=ARMV8`, because the install step re-runs CPU detection. This is not a problem. The library file name (`libopenblas_vortex-r0.3.28.a`) shows that the VORTEX kernels were built.

## 5. Edit `install.info` (line 26)

This tells GAMESS where OpenBLAS is. First keep a copy of the original, then change the line:

```zsh
cp install.info install.info.orig
sed -i "s|^setenv GMS_LAPACK_LINK_LINE.*|setenv GMS_LAPACK_LINK_LINE  \"$HOME/gamess/3rd-party/openblas64/lib/libopenblas.a\"|" install.info
grep GMS_LAPACK_LINK_LINE install.info
```

The `grep` should show your full path, for example:

```
setenv GMS_LAPACK_LINK_LINE  "/Users/yourname/gamess/3rd-party/openblas64/lib/libopenblas.a"
```

## 6. Edit `lked` (line 926, mac64 section)

Change

```
         set LIBRARIES='-Wl,-framework -Wl,Accelerate'
```

to

```
         set LIBRARIES="$LAPACK"
```

This removes Apple's Accelerate library from the link completely. If any routine were missing from OpenBLAS, you would see a link error instead of GAMESS quietly using Accelerate's incompatible version.

```zsh
cp lked lked.orig
sed -i "s|set LIBRARIES='-Wl,-framework -Wl,Accelerate'|set LIBRARIES=\"\$LAPACK\"|" lked
chmod 755 lked
sed -n 926p lked          # expect:          set LIBRARIES="$LAPACK"
```

## 7. Edit `rungms` (lines 97-99)

`rungms` is the script that runs a GAMESS job. Its default paths are:

```
set SCR=~/gamess/restart
set USERSCR=~/gamess/restart
set GMSPATH=~/gamess
```

Change them to:

```
set SCR=~/gamess/scr
set USERSCR=~/gamess/restart
if ($?GMS_USERSCR) set USERSCR=$GMS_USERSCR
set GMSPATH=~/gamess
```

The new `if` line lets the `gms` script (step 11) save extra output files (`.dat`, `.trj`, `.rst`) next to your input file. To make the edit and create the two folders:

```zsh
cp rungms rungms.orig
sed -i 's|^set SCR=~/gamess/restart$|set SCR=~/gamess/scr|' rungms
sed -i 's|^set USERSCR=~/gamess/restart$|&\nif ($?GMS_USERSCR) set USERSCR=$GMS_USERSCR|' rungms
sed -n 95,101p rungms     # check the four lines
mkdir -p scr restart
```

If your GAMESS folder is not `~/gamess`, also change the `GMSPATH` line and the two `~/gamess` paths to match.

## 8. Compile and link (a few minutes)

```zsh
cd ~/gamess
gmake -j4 2>&1 | tee build.log
ls -l gamess.00.x
```

Use a larger number after `-j` if your Mac has more cores (`sysctl -n hw.ncpu` tells you how many). On an M5 with `-j8`, the build took about 2 minutes. `gamess.00.x` should be about 34 MB.

These warnings near the end are expected and harmless:

- `ld: warning: ignoring duplicate libraries: ...libopenblas.a`. `lked` puts OpenBLAS on the link line twice.
- Many lines like `object file ... was built for newer 'macOS' version (27.2) than being linked (27.0)`.

## 9. Raise shared-memory limits (resets at reboot)

```zsh
sudo sysctl -w kern.sysv.shmmax=8589934592
sudo sysctl -w kern.sysv.shmall=2097152
sysctl kern.sysv.shmmax kern.sysv.shmall
```

**After every reboot, run these two `sudo` lines again before your first GAMESS job.**

## 10. Run and check the tests (about 1-2 min)

```zsh
cd ~/gamess
./runall 00 >& runall.log
./tests/standard/checktst >& check.log
tail -2 check.log        # expect: All 49 test results are correct!
```

---

## 11. Set up the `gms` run script

`rungms` is awkward to use directly. The short `gms` script below calls it for you, names the log file, and keeps extra output files in the folder you run from. Create it with one copy-and-paste (everything from `cat` to the final `EOF`):

```zsh
cat > ~/gamess/gms <<'EOF'
#!/bin/zsh
#
#   gms - run GAMESS 2024R2 on this Mac, output to a log file
#
#   usage:  gms [-l logfile] [-n ncpus] [-v version] job[.inp]
#
#   Run it from the folder that holds job.inp.
#   Extra output files (job.dat, .trj, .rst, ...) are written to this folder too.
#   Rerunning a job deletes its previous job.dat etc. (rungms DEL_OLD=yes).
#
GMS=$HOME/gamess

usage() {
  cat <<USAGE
usage:  gms [-l logfile] [-n ncpus] [-v version] job[.inp]

   job       name of job.inp in the current folder
   -l file   log file name          (default: job.log)
   -n N      number of CPU cores    (default: 1)
   -v NN     version, gamess.NN.x   (default: 00)
USAGE
}

ncpus=1
verno=00
log=""
job=""

while (( $# > 0 )); do
  case "$1" in
    -l) log="$2";   shift 2 ;;
    -n) ncpus="$2"; shift 2 ;;
    -v) verno="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "gms: unknown option $1"; usage; exit 1 ;;
    *)  if [[ -n "$job" ]]; then
          echo "gms: too many input files: $job and $1"; exit 1
        fi
        job="${1%.inp}"; shift ;;
  esac
done

[[ -z "$job" ]] && { usage; exit 0; }
[[ -f "$job.inp" ]] || { echo "gms: cannot find $job.inp in $PWD"; exit 1; }
[[ -x "$GMS/gamess.$verno.x" ]] || { echo "gms: no program $GMS/gamess.$verno.x"; exit 1; }
[[ "$ncpus" == <1-> ]] || { echo "gms: -n needs a whole number, got '$ncpus'"; exit 1; }
log="${log:-$job.log}"

# clear scratch files left by an interrupted run of the same job
rm -f "$GMS/scr/$job".*(N)     # (N): no error if there is nothing to delete

# keep .dat, .trj, .rst etc. in this folder instead of $GMS/restart
# pass "job.inp" (not "job"): rungms locates the input with readlink -f,
# which on macOS fails for a name that does not exist as a file
GMS_USERSCR="$PWD" "$GMS/rungms" "$job.inp" "$verno" "$ncpus" > "$log" 2>&1

if grep -q "TERMINATED NORMALLY" "$log"; then
  echo "$job: finished normally ($log)"
else
  echo "$job: FAILED, see $log"
  exit 1
fi
EOF
chmod 755 ~/gamess/gms
ln -sf ~/gamess/gms ~/bin/gms
which gms                 # expect: /Users/yourname/bin/gms
```

`~/bin` is already on your PATH from step 1, so `gms` now works from any folder.

### Try it

Run the first test molecule as a normal job, in a folder of its own:

```zsh
mkdir -p ~/gmstest
cd ~/gmstest
cp ~/gamess/tests/standard/exam01.inp water.inp
gms water                 # expect: water: finished normally (water.log)
grep "FINAL RHF ENERGY" water.log    # expect: -37.2322678015
ls                        # water.inp  water.log  water.dat
```

Usage:

```bash
gms water                 # 1 core, writes water.log
gms water.inp -n 4        # 4 cores
gms -l test1.log water    # different log name
gms -v 01 water           # run gamess.01.x
gms                       # show help
```

---

## Useful extras

- Watch a log grow: `tail -f build.log` (Ctrl+C to stop watching).
- `gmake -j4 2>&1 | tee build.log` means: build with 4 parallel jobs, merge errors into the normal output, show it on screen and save it to `build.log`.
- Relink only (after changing libraries): `rm gamess.00.x && gmake 2>&1 | tee build.log`
- Clean rebuild: `gmake clean clean_ddi`, then step 8.
- `runall` calls `./rungms` directly, so the test `.dat` files go to `~/gamess/restart/`, not to the folder you ran from.

## If something goes wrong

- A step fails with `gfortran: Command not found`, `missing separator` or a `sed` error: your PATH from step 1 is not active. Open a new terminal and repeat the checks in step 1.
- `ld: library 'System' not found`: `SDKROOT` is not set (step 1).
- `undefined symbol` at the link step: check the `install.info` path (step 5) with `ls -l` on the file it names.
- Jobs fail with shared-memory (`shmget`) errors: you rebooted and need step 9 again.
- A job fails after an interrupted run: `gms` clears old scratch files automatically. If you use `rungms` directly, delete `~/gamess/scr/jobname.*` first.
- You ran `./config` again by mistake: repeat step 5 (`lked` and `rungms` are not affected).
- To undo an edit, copy the `.orig` file back, for example `cp lked.orig lked && chmod 755 lked`.

## What changed from the 2023 R2 instructions

| Step | 2023 R2 | 2024 R2 |
|---|---|---|
| Folder layout | archive contents moved up one level | left in the `gamess/` folder the archive creates |
| `config` gfortran answer | `13.1` | `13.3` (script now accepts 13.1-13.3 and 14.1) |
| Math library | reference LAPACK/BLAS first, OpenBLAS optional | OpenBLAS only |
| `lked` edit | line ~909 | line 926 (same change) |
| `rungms` | paths already set | three path lines must be edited (step 7) |
| Run script | `gms()` shell function, then `gms` script | `gms` script only (step 11) |
