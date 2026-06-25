# PARALLEL_PLAN.md

How to run multiple Claude Code sessions on this board at once without collisions.

## The hazard

KiCad's `.kicad_sch` / `.kicad_pcb` are monolithic s-expression files — **they don't
merge.** Two sessions editing the same schematic or board = guaranteed conflict. So
parallelism is carved along *file ownership*, not along "tasks that sound separate." Layout
and fab are an unavoidable serial spine; the win is that library, SPICE, host/bench, and
automation work touch **none** of the KiCad files and run now.

One upstream decision gates the schematic: **Pt100 vs Pt1000** (T7 range) and **how many of
the 7 channels are RTDs** (CRD/R_ref/ADS1115 counts) — see `board_spec.md` open inputs.
Resolve it early. It does **not** block Wave 0.

---

## Waves

### Wave 0 — start now, 4 sessions in parallel (zero file contention)

| Track | Focus | Owns | Blocked by |
|-------|-------|------|------------|
| **A** | Component libraries (CRD, ADS1115, R_ref, connectors) | `libraries/`, lib-tables | nothing |
| **B** | SPICE harness + accuracy/noise budget | `sim/`, `reports/sim/` | nothing |
| **C** | Acquisition (`host/`: T7 + ADS1115 I²C + ratiometric) and bench procedures | `host/`, `test/` | nothing |
| **D** | Automation, gates, repo meta | `scripts/`, `reports/{erc,drc,bom}/`, `.gitignore`, `README.md` | nothing |

In parallel, **you** resolve RTD type + channel count.

### Wave 1 — schematic (after A merges + decision)

| Track | Owns | Blocked by |
|-------|------|------------|
| **E** | `hardware/*.kicad_sch` | A (symbols), the decision |

Optional split via hierarchical sheets: **E1** owns the `unit_cell` sheet, **E2** owns the
`ads1115` + `power` + `connectors` sheets. The root sheet is a chokepoint — one owns it, or
run E as a single session.

### Wave 2 — layout

| Track | Owns | Blocked by |
|-------|------|------------|
| **F** | `hardware/*.kicad_pcb` | E, A |

Single session; layout doesn't parallelize on one board.

### Wave 3 — fab + closeout

| Track | Owns | Blocked by |
|-------|------|------------|
| **G** | `fab/`, final `reports/` | F |

Wave 3 also re-points Track B's SPICE at the **real exported netlist** and runs Track C's
`host/` + bench procedures on the physical board.

---

## Ownership matrix (Wave 0 — the collision rule)

| Track | May write | Must NOT touch |
|-------|-----------|----------------|
| A | `libraries/**`, `hardware/sym-lib-table`, `hardware/fp-lib-table` | any `.kicad_sch/.kicad_pcb`, `sim/`, `host/`, `test/`, `scripts/` |
| B | `sim/**`, `reports/sim/**` | `hardware/`, `libraries/`, `host/`, `test/`, `scripts/` |
| C | `host/**`, `test/**` | `hardware/`, `libraries/`, `sim/`, `scripts/` |
| D | `scripts/**`, `reports/{erc,drc,bom}/`, `.gitignore`, `README.md` | `hardware/` contents, `libraries/`, `sim/`, `host/`, `test/` |

Shared docs (`board_spec.md`, process docs) are **read-only** for Wave-0 sessions. The global
`SESSION_LOG.md` is **not** touched during parallel work (see below).

---

## Coordination mechanics

### One worktree per session
> **Worktrees MUST live outside any other git repo.** Put them in a dedicated sibling folder,
> never a bare `../rtd-trackX`. (A past run created them inside the unrelated `ivmux-python`
> repo because this repo then sat at `ivmux-python/excitation-current-source-v2`, so `../`
> resolved *into* that repo — they polluted its status and risked being committed there.)
```bash
# run from this repo's root
git switch -c integration
mkdir -p ../excitation-worktrees
git worktree add ../excitation-worktrees/trackA -b trackA integration
git worktree add ../excitation-worktrees/trackB -b trackB integration
git worktree add ../excitation-worktrees/trackC -b trackC integration
git worktree add ../excitation-worktrees/trackD -b trackD integration
```
Open each Claude Code session in its own `../excitation-worktrees/trackX` directory — shared
object store, independent working trees and branches, no collisions. Confirm the target is
**not** inside another repo (`git -C <target>/.. rev-parse --show-toplevel` should be empty or
this repo). (Fallback: separate clones.)

### Per-track logs
Each track logs to `docs/sessions/trackX.md` (same schema as `SESSION_LOG.md`). The global
`SESSION_LOG.md` is updated only at integration. The per-track brief is each session's
effective kickoff, replacing the single-session "read the global log" step.

### Reports pre-partitioned
B → `reports/sim`, D → `reports/{erc,drc,bom}`, C → `reports/test`. No collisions.

### Integration order (you, or a dedicated integration session)
1. **A first** — libraries gate the schematic.
2. **B, C, D** — any order; independent.
3. Resolve RTD/channel decision → start **E** off the post-A `integration` branch.
4. **F** after E; **G** after F.

Re-run gates after each merge and update the global `SESSION_LOG.md` with a one-entry summary.

## How each session starts
Hand the session its `docs/tasks/TRACK_<X>_*.md` brief as the first message. The brief points
it at `CLAUDE.md`, `docs/board_spec.md`, the relevant process docs, and its own track log,
and confines it to its owned paths.
