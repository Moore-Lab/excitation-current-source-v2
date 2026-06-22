# DIRECTORY_MANAGEMENT.md

How this repository is organized and the rules for keeping it clean. The guiding
principle: **source is committed and human/agent-authored; generated artifacts are
reproducible and either gitignored or tagged to a release.** If a file can be regenerated
from source by a command, it is not source.

---

## Layout

```
ref200-rtd-board/
├── CLAUDE.md                  # bootstrap, auto-read by Claude Code
├── README.md                  # human overview, build/run instructions
├── docs/
│   ├── SESSION_KICKOFF.md
│   ├── SESSION_LOG.md
│   ├── DIRECTORY_MANAGEMENT.md
│   ├── BOARD_DEV_CHECKLIST.md
│   ├── TESTING_PLAN.md
│   ├── board_spec.md          # electrical design source of truth
│   └── datasheets/            # REF200, T7, reference resistor, LDO, connectors
├── hardware/                  # the KiCad project (SOURCE)
│   ├── ref200-rtd.kicad_pro
│   ├── ref200-rtd.kicad_sch   # + per-sheet .kicad_sch for hierarchical channels
│   ├── ref200-rtd.kicad_pcb
│   └── fp-lib-table, sym-lib-table   # point ONLY at project-local libs
├── libraries/                 # project-local libraries (SOURCE) — portability
│   ├── symbols/   *.kicad_sym
│   ├── footprints/ *.pretty/*.kicad_mod
│   └── 3dmodels/  *.step / *.wrl
├── sim/                       # SPICE (SOURCE)
│   ├── models/                # vendor SPICE models (REF200 if available)
│   ├── netlists/              # *.cir test decks
│   ├── scripts/               # ngspice batch + python analysis/plots
│   └── README.md              # how to run each sim
├── scripts/                   # automation (SOURCE): kicad-cli wrappers, gate runners
├── test/                      # bench testing (SOURCE)
│   ├── procedures/            # stage-by-stage bring-up scripts (T7 / LabJack)
│   └── data/                  # raw measured data (commit; it's irreplaceable)
├── reports/                   # GENERATED, committed for traceability
│   ├── erc/  drc/  sim/  test/
└── fab/                       # GENERATED manufacturing outputs (gitignored; tag releases)
    ├── gerbers/ drill/ pos/ bom/ assembly/
```

## Source vs generated — the dividing line

| Committed (source) | Generated (reproducible) |
|--------------------|--------------------------|
| `hardware/*.kicad_*`, project-local libs | `fab/**` gerbers, drill, pos |
| `docs/**`, `README.md` | `reports/**` ERC/DRC/sim/BOM exports |
| `sim/` decks, models, scripts | rendered 3D images, schematic PDFs |
| `test/procedures`, `test/data` (raw measurements) | netlists exported from the schematic |
| `scripts/**` | |

- **`reports/` is generated but committed.** It is cheap, diffs well, and gives the log
  something to point at ("DRC clean — reports/drc/drc_s007.json"). Regenerate it from the
  gate commands; never hand-edit.
- **`fab/` is generated and gitignored.** Produce it only when cutting a manufacturing
  drop, and capture that drop with a git **tag** (e.g. `fab-rev-A`) so the exact source
  that produced it is recoverable. Do not let stale gerbers linger in the working tree.
- **`test/data/` is committed even though it isn't "source"** — measured data cannot be
  regenerated and is the whole point of building the board.

## Libraries — keep them project-local

Point `sym-lib-table` and `fp-lib-table` at `libraries/` inside the repo, not at the
global KiCad libraries. Reasons:

- The project must build identically on any machine and for any future session, regardless
  of what global libraries happen to be installed or what version they are.
- A symbol or footprint silently changing under you (global library update) is a class of
  bug that is very hard to notice on a board this sensitive (a wrong land pattern on the
  REF200 or a wrong pinout on the connector is fatal).

Every custom or vendor symbol/footprint used goes into `libraries/`. The reference
resistor and REF200 footprints in particular must be verified against their datasheets and
committed here.

## Naming conventions

- Project base name: `ref200-rtd`. Keep it consistent across `.kicad_pro/.sch/.pcb`.
- Hierarchical sheets per channel or per functional block; name them by function
  (`unit_cell`, `power`, `connectors`), not by number where possible.
- Reports carry the session id: `reports/drc/drc_s007.json`. This is what the log cites.
- Releases are git tags: `rev-A`, `rev-B`; fab drops `fab-rev-A`.

## .gitignore essentials (KiCad)

```
# KiCad local/auto
*-backups/
*.kicad_prl
_autosave-*
fp-info-cache
~*.lck
# generated manufacturing outputs
fab/
# python
__pycache__/
.venv/
# sim scratch (keep decks + final results in reports/sim, ignore raw scratch)
sim/scratch/
```

Keep `*.kicad_pro` committed (it holds board setup, netclasses, design rules — that is
source). `*.kicad_prl` is per-user local state — ignore it.

## One-line test

Before committing, ask of each new file: *"Can a command regenerate this from what's
already in git?"* If yes and it isn't measured data, it belongs in `reports/` (commit) or
`fab/` (ignore), not loose in the tree.
