# REF200 Multi-Channel 4-Wire RTD Readout Board

A multi-channel, 4-wire RTD readout board: per-RTD **REF200** current sources feeding a
**LabJack T7 Pro** ADC, designed in **KiCad**. Each RTD sits in its own loop near ground
and is measured **ratiometrically** against a precision reference resistor, so the current
source's absolute accuracy and drift drop out of the result:

```
R_RTD = R_ref · (V_RTD / V_ref)
```

**Resolved configuration:** Pt100, 3 channels, 100 µA/channel, REF200 Mode B (2 sources/chip,
2 chips), R_ref = 100 Ω (0.01 %, ≤10 ppm/°C), full-differential 4-wire, T7 ±0.1 V range.
The electrical source of truth is [docs/board_spec.md](docs/board_spec.md).

---

## Repository layout

`hardware/` KiCad project (source) · `libraries/` project-local symbols/footprints/3D ·
`sim/` SPICE decks & scripts · `test/` bench procedures & measured data · `scripts/`
automation (this track) · `reports/` generated ERC/DRC/BOM/sim (committed) · `fab/`
manufacturing outputs (generated, gitignored, tagged per release) · `docs/` the canonical
process and spec documents.

Full rules for what is source vs generated: [docs/DIRECTORY_MANAGEMENT.md](docs/DIRECTORY_MANAGEMENT.md).

## Toolchain

| Tool | Pinned version | Notes |
|------|----------------|-------|
| KiCad | **10.0.3** | On Windows, `kicad-cli` is **not on PATH** — it lives at `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`. The scripts auto-detect it (see below). |
| Python | 3.12.x | For SPICE analysis / plotting (Track B). |
| ngspice | (standalone) | Not yet installed on the dev box — only KiCad's bundled `ngspice.dll`. Track B's `ngspice -b` flow needs the standalone CLI. |

The automation scripts are POSIX shell. On Windows run them from **Git Bash** (bundled with
[Git for Windows](https://git-scm.com/download/win)); on Linux/macOS any shell works.

`kicad-cli` is located in this order: `$KICAD_CLI` env var → `kicad-cli` on `PATH` → known
Windows install dirs. If KiCad lives somewhere unusual, set `KICAD_CLI=/path/to/kicad-cli`.

## Running the validation gates

One command runs ERC + DRC, writes JSON reports under `reports/erc|drc/`, and exits nonzero
if any gate finds errors:

```bash
bash scripts/run_gates            # reports tagged "latest"
bash scripts/run_gates s002       # name the reports erc_s002.json / drc_s002.json
```

It **degrades gracefully**: until the schematic/PCB exist it reports the gate as `SKIP` and
exits 0 ("nothing to check"), so it's safe in CI and pre-commit from day one.

Individual wrappers (each takes an optional report tag, each skips cleanly if its input file
is absent):

| Script | What it does | Output |
|--------|--------------|--------|
| `scripts/run_gates [tag]` | ERC + DRC, summary, nonzero on any error | `reports/erc/`, `reports/drc/` |
| `scripts/erc.sh [tag]` | Schematic ERC (`--severity-error`) | `reports/erc/erc_<tag>.json` |
| `scripts/drc.sh [tag]` | PCB DRC (`--severity-error`) | `reports/drc/drc_<tag>.json` |
| `scripts/bom.sh [tag]` | BOM CSV for review vs board_spec §7 | `reports/bom/bom_<tag>.csv` |
| `scripts/netlist.sh` | Schematic netlist for SPICE/cross-checks | `sim/netlists/ref200-rtd.net` (override `NETLIST_OUT`) |
| `scripts/fab.sh [tag]` | Manufacturing drop (see below) | `fab/` |

Reports are committed for traceability; cite them in the session log (e.g. *"DRC clean —
reports/drc/drc_s007.json"*). Never hand-edit a report — regenerate it.

## Producing a fab drop

`fab/` is **generated and gitignored**. Cut it only at a reviewed, DRC-clean, **tagged**
revision so the exact source is recoverable:

```bash
git tag rev-A                 # tag the reviewed state first
bash scripts/fab.sh rev-A     # exports gerbers + drill + pos + STEP into fab/
git tag fab-rev-A             # tag the drop itself
```

`scripts/fab.sh` refuses to run unless DRC is clean (override: `ALLOW_DIRTY_FAB=1`) and warns
if HEAD isn't tagged (override: `ALLOW_UNTAGGED_FAB=1`).

## Enforcing gates on commit (optional)

An opt-in pre-commit hook blocks commits whose gates fail:

```bash
git config core.hooksPath scripts/hooks    # enable
git config --unset core.hooksPath          # disable
git commit --no-verify                     # bypass once (log why)
```

It's a no-op until the schematic/PCB exist, so it's safe to enable now.

## Process & parallel development

- Start/end-of-session procedure: [docs/SESSION_KICKOFF.md](docs/SESSION_KICKOFF.md)
- Running record / "where we left off": [docs/SESSION_LOG.md](docs/SESSION_LOG.md)
- Engineering gate list: [docs/BOARD_DEV_CHECKLIST.md](docs/BOARD_DEV_CHECKLIST.md)
- Verification plan (SPICE + bench): [docs/TESTING_PLAN.md](docs/TESTING_PLAN.md)
- **Running multiple Claude Code sessions at once:** [docs/PARALLEL_PLAN.md](docs/PARALLEL_PLAN.md)