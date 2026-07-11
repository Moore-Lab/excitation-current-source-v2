# DIRECTORY_MANAGEMENT.md

Repository organization and hygiene. Principle: **source is committed and authored;
generated artifacts are reproducible and either gitignored or tagged to a release.** If a
command can regenerate a file from source, it isn't source.

## Layout

```
rtd-readout-board/
├── CLAUDE.md                  # bootstrap, auto-read by Claude Code
├── README.md                  # human overview, build/run
├── docs/
│   ├── SESSION_KICKOFF.md  SESSION_LOG.md
│   ├── DIRECTORY_MANAGEMENT.md  BOARD_DEV_CHECKLIST.md  TESTING_PLAN.md
│   ├── PARALLEL_PLAN.md
│   ├── board_spec.md          # electrical source of truth
│   ├── datasheets/            # CRD (SEMITEC S-101T), ADS1115, R_ref, LDO, connectors, T7
│   ├── sessions/              # per-track logs in parallel mode (trackA.md, ...)
│   └── tasks/                 # TRACK_A..G briefs
├── hardware/                  # KiCad project (SOURCE)
│   ├── rtd-readout.kicad_pro / .kicad_sch / .kicad_pcb
│   └── sym-lib-table, fp-lib-table   # point ONLY at project-local libs
├── libraries/                 # project-local symbols/footprints/3d (SOURCE)
│   ├── symbols/  footprints/*.pretty  3dmodels/
├── sim/                       # SPICE (SOURCE): models/ netlists/ scripts/
├── host/                      # acquisition library (SOURCE): T7 LJM driver, ADS1115 I²C
│   │                          #   driver, time-aligned read, ratiometric + cross-cal math
├── test/                      # bench (SOURCE): procedures/ (use host/), data/ (committed)
├── scripts/                   # automation (SOURCE): kicad-cli gates, report runners
├── reports/                   # GENERATED, committed: erc/ drc/ sim/ test/
└── fab/                       # GENERATED, gitignored; tag releases: gerbers/ drill/ pos/ bom/
```

## Source vs generated

| Committed (source) | Generated (reproducible) |
|--------------------|--------------------------|
| `hardware/*.kicad_*`, project-local libs | `fab/**` (gerbers, drill, pos, step) |
| `docs/**`, `README.md` | `reports/**` (ERC/DRC/sim/BOM exports) |
| `sim/` decks/models/scripts | netlists exported from the schematic |
| `host/**`, `test/procedures` | rendered 3D images, schematic PDFs |
| `test/data/**` (measured — irreplaceable) | |
| `scripts/**` | |

- `reports/` is generated but **committed** — cheap, diffs well, gives the log something to
  cite. Regenerate from the gate commands; never hand-edit.
- `fab/` is generated and **gitignored**; produce only at a release and capture it with a
  git **tag** (`fab-rev-A`). Don't leave stale gerbers in the tree.
- `test/data/` is committed despite being "output" — measured data can't be regenerated.

## host/ vs test/

`host/` holds the **reusable acquisition code**: the LJM driver for the T7 (V_RTD), the
ADS1115 I²C driver (V_ref), the time-aligned dual-ADC read, and the ratiometric +
cross-calibration math. `test/procedures/` holds the staged bench scripts that *import*
`host/`. The same `host/` code is what eventually takes real measurements — so it is
first-class source, not throwaway test scaffolding.

## Libraries — keep them project-local

Point `sym-lib-table` / `fp-lib-table` at `libraries/` inside the repo, not the global KiCad
libs, so the project builds identically on any machine and a global-lib update can't
silently swap a footprint. The CRD, ADS1115, connector, and R_ref footprints in particular
must be verified against their datasheets and committed here.

## Naming & releases
- Base name `rtd-readout` across `.kicad_pro/.sch/.pcb`.
- Hierarchical sheets by function (`unit_cell`, `ads1115`, `power`, `connectors`).
- Reports carry the session id: `reports/drc/drc_s007.json`.
- Releases are git tags (`rev-A`); fab drops `fab-rev-A`.

## .gitignore essentials

```
*-backups/
*.kicad_prl
_autosave-*
fp-info-cache
~*.lck
fab/
__pycache__/
.venv/
sim/scratch/
```

Keep `*.kicad_pro` tracked (board setup, netclasses, rules = source). Ignore `*.kicad_prl`
(per-user local state).

## One-line test
Before committing a new file ask: *can a command regenerate this from what's in git?* If yes
and it isn't measured data → `reports/` (commit) or `fab/` (ignore), not loose in the tree.
