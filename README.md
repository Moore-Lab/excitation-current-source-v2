# RTD Readout Board

Multi-channel 4-wire RTD readout for a LabJack T7 Pro.

Each RTD gets its own constant-current loop: a **current-regulator diode (CRD, ~220 µA)**
drives a precision **reference resistor R_ref** in series with the RTD. The RTD voltage
**V_RTD** is read on the T7's existing differential pairs; the current-sense voltage
**V_ref** is digitized on-board by **I²C ADS1115** ADCs on the T7's digital lines. Each RTD
is then computed **ratiometrically** as `R_RTD = C · (V_RTD / V_ref)`, where the per-channel
constant `C` is found by one-time **cross-calibration** against a known resistor. This makes
the result independent of the CRD's accuracy and R_ref's absolute value, and fits within the
T7's already-committed 7 analog pairs by moving V_ref onto the I²C bus.

**This build (locked, `docs/board_spec.md` §Resolved inputs):** Pt100 RTDs, T7 range ±0.1 V;
**3 channels** → 3 CRD/R_ref unit cells, **2 ADS1115** (ADDR 0x48/0x49; 4 differential V_ref
reads, 1 spare), 3 RTD 4-wire connectors. The result is **ratiometric across two ADCs**
(T7 + ADS1115), so the dominant design concern is protecting the precision-analog path
(sense + V_ref) and keeping the I²C/digital side off it.

## Where to start
- **Design:** `docs/board_spec.md` (electrical source of truth).
- **Working with Claude Code:** `CLAUDE.md` → `docs/SESSION_KICKOFF.md`.
- **Running multiple sessions in parallel:** `docs/PARALLEL_PLAN.md` + `docs/tasks/`.
- **Process:** `docs/DIRECTORY_MANAGEMENT.md`, `docs/BOARD_DEV_CHECKLIST.md`,
  `docs/TESTING_PLAN.md`.

## Toolchain
- **KiCad 10.0.3** — pinned. The gate scripts auto-discover `kicad-cli` on `PATH`, else at
  the standard Windows install (`C:\Program Files\KiCad\<ver>\bin\kicad-cli.exe`); override
  with `KICAD_CLI=/path/to/kicad-cli`. A KiCad **major** bump can rewrite the `.kicad_*`
  formats — bump the pin in `scripts/lib.sh` deliberately and note it in the log.
- **ngspice** — SPICE engine for Track B's harness (`sim/`).
- **Python + LabJack LJM** — acquisition library in `host/` (Track C). *Not* used by the gate
  scripts, which are POSIX `sh` (run under Git Bash on Windows or natively on Linux/macOS).

## Validation gates
The cheap, machine-checkable gates run from one entry point. It **degrades gracefully**: with
no KiCad design files yet (before the schematic/PCB land) it reports "nothing to check" and
exits 0, so every track and the integration step run it identically.

```sh
sh scripts/run_gates            # ERC + DRC -> reports/{erc,drc}/, nonzero on any error
sh scripts/run_gates --tag s007 # stamp reports as erc_s007.json / drc_s007.json
```

| Script | Does | Output |
|--------|------|--------|
| `scripts/run_gates` | ERC + DRC; the gate every session runs | `reports/{erc,drc}/*.json` |
| `scripts/erc` | ERC only (canonical command) | `reports/erc/erc_<tag>.json` |
| `scripts/drc` | DRC only (refills zones; never saves the board) | `reports/drc/drc_<tag>.json` |
| `scripts/export_bom` | BOM incl. **Tempco** field (R_ref stability) | `reports/bom/bom_<tag>.csv` |
| `scripts/export_netlist` | Schematic netlist for the SPICE harness | `sim/netlists/rtd-readout.net` |
| `scripts/fab_drop` | Gerbers + drill + pos + STEP + BOM | `fab/**` (gitignored) |
| `scripts/lib.sh` | Shared helpers (sourced, not run) | — |

`reports/**` is generated but **committed** (cheap, diffs well, gives the log something to
cite); regenerate it from these scripts, never hand-edit. Default tag is `latest` (overwrites
for clean diffs); pass `--tag sNNN` to keep a session-stamped copy.

### Optional: enforce gates on commit
```sh
sh scripts/install_hooks   # installs a pre-commit hook that runs scripts/run_gates
```
Opt-in (not installed automatically, so it never surprises a parallel-track worktree). It's a
no-op until the schematic/PCB exist. Remove it with `rm "$(git rev-parse --git-path hooks)/pre-commit"`.

## Cutting a fab drop
Only at a reviewed, **DRC-clean, tagged** rev — `fab/` is gitignored; capture the drop with a
git tag, never leave it in-tree (`docs/DIRECTORY_MANAGEMENT.md`).

```sh
sh scripts/run_gates && git tag rev-A     # gate, then tag the reviewed state
sh scripts/fab_drop                       # gerbers/drill/pos/step/bom -> fab/
git tag fab-rev-A                          # capture the manufacturing drop
```