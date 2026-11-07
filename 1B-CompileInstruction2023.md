# Compiling GAMESS-US 2023 R2

After successfully compiling GAMESS 2021 R2, I found a copy of source code from 2023. this would enable using more modern Fortran and math libraries. After lots of help from Claude, I got it working. I faced entirely different issues than with the 2021 source code. I don't know how anyone manages to compile software on different machines. I am clueless, but Claude held my had at every stage.

Below is the instructions as assembled by Claude after the whole process had produced a working executable that passed the tests. I will next follow these instructions and see if they enable a more direct and successful compile.

Tested result: all 49 standard tests pass (`checktst`: "All 49 test results are correct!").
Build folder used here: `~/gamess2023R2claude`. Adjust paths if you use a different folder.
 
## Why the extra steps?
The stock GAMESS build assumes GNU tools and gives wrong answers with Apple's math library:
 
| Problem | Cause | Fix |
|---|---|---|
| `Makefile:120: missing separator` | macOS `make` is GNU Make 3.81 (no `undefine`) | Homebrew GNU make (`gmake`) |
| `sed: extra characters at the end of p command` | macOS `sed` is BSD sed | Homebrew GNU sed, first on PATH |
| `ld: library 'System' not found` | linker can't find the macOS SDK | `export SDKROOT=$(xcrun --show-sdk-path)` |
| exam45-47 fail, `ERROR INFO: 4294967296` | Accelerate LAPACK uses 4-byte integers; GAMESS uses 8-byte | build 8-byte reference LAPACK |
| many tests segfault in "LZ VALUE ANALYSIS" | Accelerate's complex BLAS (ZDOTC) uses an incompatible return convention | link 8-byte reference BLAS too |
| OpenBLAS build: generic `ARMV8` kernels | CPU not auto-detected | `TARGET=VORTEX` (Section B) |
| OpenBLAS build: fatal errors at the end | its test programs fail to link with recent Xcode | build only `libs netlib` (Section B) |
 
---
 
## 1. Prerequisites (one time)
 
```zsh
xcode-select --install          # Command Line Tools (skip if already installed)
brew install gcc@13 make gnu-sed
 
# make "gfortran" point to gfortran-13
mkdir -p ~/bin
rm -f ~/bin/gfortran
ln -s /opt/homebrew/bin/gfortran-13 ~/bin/gfortran
```
 
Add these lines to `~/.zshrc`, then open a new terminal (or `source ~/.zshrc`):
 
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
 
## 2. Unpack the source
 
```zsh
mkdir ~/gamess2023R2claude
cd ~/gamess2023R2claude
cp ~/Downloads/gamess-current.tar.gz .      # wherever you saved the download
tar -xzf gamess-current.tar.gz
```
 
If the archive unpacks into a subfolder (e.g. `gamess/`), move its contents up so `config`, `Makefile` and `source/` sit directly in `~/gamess2023R2claude`.
 
## 3. Configure
 
```zsh
./config
```
 
Answers: target `mac64`, gfortran version `13.1` (highest the script supports), defaults or "no" for everything else.
There is no math-library question for mac64; it always sets `vecLib` — that's expected.
 
## 4. Build the 8-byte-integer reference LAPACK + BLAS
 
(`gmake lapack USE_CMAKE=false` fails because two patch files are missing from the release, so do it by hand.)
 
```zsh
mkdir -p 3rd-party/lapack 3rd-party/lib
curl -L -o lapack-3.10.1.tar.gz https://github.com/Reference-LAPACK/lapack/archive/refs/tags/v3.10.1.tar.gz
tar -xzf lapack-3.10.1.tar.gz -C 3rd-party/lapack --strip-components=1
cp tools/lapack/make.inc.gfortran.64 3rd-party/lapack/make.inc
cd 3rd-party/lapack
gmake -j4 blaslib
gmake -j4 lapacklib
ln -fs $PWD/librefblas.a ../lib/libblas64.a
ln -fs $PWD/liblapack.a  ../lib/liblapack64.a
cd ../..
ls -l 3rd-party/lib      # libblas64.a and liblapack64.a
```
 
## 5. Edit `install.info` (line ~25)
 
Change
 
```
setenv GMS_LAPACK_LINK_LINE  ""
```
 
to
 
```
setenv GMS_LAPACK_LINK_LINE  "/Users/yourname/gamess2023R2claude/3rd-party/lib/liblapack64.a"
```
 
**Do not run `./config` again after this** — it rewrites `install.info`.
 
## 6. Edit `lked` (line ~909, mac64 section)
 
Change
 
```
         set LIBRARIES='-Wl,-framework -Wl,Accelerate'
```
 
to
 
```
         set LIBRARIES="$LAPACK $GMS_PATH/3rd-party/lib/libblas64.a -Wl,-framework -Wl,Accelerate"
```
 
This puts the 8-byte LAPACK and BLAS ahead of Accelerate on the link line (by default lked puts LAPACK *after* Accelerate, so Accelerate wins).
Then make sure the script is still executable:
 
```zsh
chmod 755 lked
```
 
## 7. Compile and link
 
```zsh
gmake -j4 2>&1 | tee build.log
ls -l gamess.00.x
```
 
## 8. Raise shared-memory limits (resets at reboot)
 
```zsh
sudo sysctl -w kern.sysv.shmmax=8589934592
sudo sysctl -w kern.sysv.shmall=2097152
sysctl kern.sysv.shmmax kern.sysv.shmall
```
 
## 9. Run and check the tests
 
```zsh
./runall 00 >& runall.log
./tests/standard/checktst >& check.log
tail -2 check.log        # expect: All 49 test results are correct!
```
 
---
 
## Useful extras
 
- Watch a log grow: `tail -f build.log` (Ctrl+C to stop watching).
- `gmake -j4 2>&1 | tee build.log` = build with 4 parallel jobs, merge errors into normal output, show on screen and save to build.log.
- Relink only (after changing libraries): `rm gamess.00.x && gmake 2>&1 | tee build.log`
- Clean rebuild: `gmake clean clean_ddi` then step 7.
## Performance note
Steps 4-6 use the plain reference BLAS/LAPACK: correct, but slow for heavy linear algebra (large MP2, CCSD(T)).
Apple's Accelerate is fast but **cannot be used** (4-byte integers, incompatible complex-function returns).
The faster correct option is OpenBLAS built with 64-bit integers — Section B below. Verified: all 49 tests pass.
 
---
 
# B. Optional faster build: OpenBLAS with 64-bit integers (ILP64)
 
Do this after the reference build works (or instead of steps 4-6). OpenBLAS contains both BLAS and LAPACK, so it replaces both reference libraries. It is compiled with gfortran, so there's no complex-return mismatch.
 
Lessons learned:
- Homebrew's `openblas` uses 4-byte integers — not usable. Build from source with `INTERFACE64=1`.
- OpenBLAS did not detect the M-series CPU (built generic `ARMV8`). Force `TARGET=VORTEX`.
- The default target also links OpenBLAS's own test programs, which fail with recent Xcode linkers. Build only `libs netlib` (the GAMESS tests are the real check).
## B1. Back up the working reference build
 
```zsh
cd ~/gamess2023R2claude
cp gamess.00.x  gamess.00.x.refblas
cp lked         lked.refblas
cp install.info install.info.refblas
```
 
## B2. Build and install OpenBLAS (about 5-15 min)
 
```zsh
cd ~/gamess2023R2claude/3rd-party
curl -L -o OpenBLAS-0.3.28.tar.gz https://github.com/OpenMathLib/OpenBLAS/releases/download/v0.3.28/OpenBLAS-0.3.28.tar.gz
tar -xzf OpenBLAS-0.3.28.tar.gz
cd OpenBLAS-0.3.28
gmake -j4 TARGET=VORTEX INTERFACE64=1 USE_THREAD=0 USE_OPENMP=0 NO_SHARED=1 CC=clang FC=gfortran libs netlib 2>&1 | tee openblas-build.log
ls -l libopenblas*.a          # expect libopenblas_vortex-r0.3.28.a
gmake PREFIX=$HOME/gamess2023R2claude/3rd-party/openblas64 NO_SHARED=1 install 2>&1 | tee -a openblas-build.log
ls -l ../openblas64/lib/libopenblas.a
```
 
Flags: `TARGET=VORTEX` = Apple M-series kernels; `INTERFACE64=1` = 8-byte integers (the essential one); `USE_THREAD=0 USE_OPENMP=0` = single-threaded (GAMESS parallelises with DDI processes, so threaded BLAS would oversubscribe cores); `NO_SHARED=1` = static library only, so `gamess.00.x` doesn't depend on external files.
 
Check in the log/config: `grep -E "^CORE" Makefile.conf` shows `CORE=VORTEX`, and the gfortran lines contain `-fdefault-integer-8`.
 
## B3. Point GAMESS at OpenBLAS
 
`install.info` (line ~25):
 
```
setenv GMS_LAPACK_LINK_LINE  "/Users/yourname/gamess2023R2claude/3rd-party/openblas64/lib/libopenblas.a"
```
 
`lked` (line ~909, mac64 section):
 
```
         set LIBRARIES="$LAPACK"
```
 
Accelerate is dropped completely, so any routine missing from OpenBLAS would show up as a link error instead of silently using Accelerate's incompatible version. Then:
 
```zsh
chmod 755 lked
```
 
## B4. Relink and test
 
```zsh
cd ~/gamess2023R2claude
rm gamess.00.x
gmake 2>&1 | tee build.log
./runall 00 >& runall.log
./tests/standard/checktst >& check.log
tail -2 check.log        # expect: All 49 test results are correct!
```
 
## B5. If something goes wrong
 
- Link errors (`undefined symbol`): temporarily use `set LIBRARIES="$LAPACK -Wl,-framework -Wl,Accelerate"` in `lked` and check which routines were missing.
- Tests fail: restore the reference build by copying the three `.refblas` files back over `gamess.00.x`, `lked` and `install.info`.
- Compare speed: copy `gamess.00.x.refblas` to `gamess.01.x` and run the same input with `rungms` version `00` vs `01`.

## Setting up gms shell function

I set up a shell function to run the `rungms` script. I used instructions from the 2021 build. I added the following to the ~/.zshrc file

```zsh
# run a GAMESS job:  gms input[.inp] [ncpus]
gms() {
  local job="${1%.inp}"
  rm -f ~/gamess2023R2claude/scr/"$job".*
  ~/gamess2023R2claude/rungms "$job" 00 "${2:-1}" > "$job.log" 2>&1
  grep -q "TERMINATED NORMALLY" "$job.log" && echo "$job: finished normally" || echo "$job: FAILED, see $job.log"
}
```

Run it from the folder that holds the input file:

```bash
gms water          # water.inp on 1 core, output in water.log
gms water 4        # 4 cores
gms water 4 &      # in the background
```
## A better way to use gms

I deleted the gms() function from the `~/.zshrc` file and had Claude edit the `gms` script from the previous 2020 installation. (A similar script is available in /tools). Claude built a short shell script that will call `rungms` and handle job names, etc

Usage

```bash
gms water                 # 1 core, writes water.log
gms water.inp -n 4        # 4 cores
gms -l test1.log water    # different log name
gms -v 01 water           # run gamess.01.x
gms                       # show help
```

After a reboot, raise the shared-memory limits again before the first job.

## Using this build from the notebooks

The notebooks in this book don't need `gms`. They call `rungms` from *Python* through `gamess_tools.run_gamess()`, which does the same three things as the script above: clear old scratch files, run `rungms`, and check the log for `TERMINATED NORMALLY`. To connect this build to the notebooks:

1. In `rungms`, set `SCR`, `USERSCR` and `GMSPATH`, and add the `GMS_USERSCR` and `DEL_OLD=yes` lines shown in [Editing RUNGMS](1_Setup.ipynb). Back up `rungms` first.
2. In `gamess_settings.py` (next to the notebooks), set `GAMESS_DIR` to this build folder, for example `"~/gamess2023R2claude"`.
3. Run the settings and test cells of [the setup notebook](1_Setup.ipynb).

## AI Statement

This page is copied from `1B-CompileInstruction2023.md` in the original book. It stays a Markdown page because compiling *GAMESS* has to happen in the terminal. The original page was itself assembled by Claude (Anthropic) from the author's build session, with the author's introduction and comments.

- **Original text kept (about 95 %).** All build steps, tables and notes are unchanged.
- **Changed by AI in this version.** Personal paths were generalized (`/Users/yourname/...`, and the source archive is copied from `~/Downloads`). The section "Using this build from the notebooks" is new and links the build to `gamess_settings.py` and the setup notebook.
