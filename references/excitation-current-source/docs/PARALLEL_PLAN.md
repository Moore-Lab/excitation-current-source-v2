# PARALLEL_PLAN.md

How to run multiple Claude Code sessions on this board at once without them stepping on
each other.

## The hazard

KiCad's `.kicad_sch` and `.kicad_pcb` files are single monolithic s-expression files.
**They do not merge** — two sessions editing the same schematic or board is a guaranteed
conflict. So parallelism is carved along *file ownership*, not along "tasks that sound
separate." Layout and fab are an unavoidable serial spine; the win is that library, SPICE,
bench, and automation work touch **none** of the KiCad files and can all run now.

There is also one upstream decision that gates the schematic: **Pt100 vs Pt1000 and total
channel count** (sets current, R_ref, chips/channel, AIN mode — see `board_spec.md` open
inputs). Resolve that early; it unblocks Wave 1. It does **not** block Wave 0.

---

## Waves

### Wave 0 — start now, 4 sessions in parallel (zero file contention)

| Track | Session focus | Owns | Blocked by |
|-------|---------------|------|------------|
| **A** | Component libraries | `libraries/`, lib-tables | nothing |
| **B** | SPICE harness + accuracy/noise budget | `sim/`, `reports/sim/` | nothing |
| **C** | Bench procedures + T7 control code | `test/` | nothing |
| **D** | Automation, gates, repo meta | `scripts/`, `reports/{erc,drc}/`, `.gitignore`, `README.md` | nothing |

In parallel, **you** resolve the RTD-type + channel-count decision.

### Wave 1 — schematic (after A merges + decision made)

| Track | Owns | Blocked by |
|-------|------|------------|
| **E** | `hardware/*.kicad_sch` | A (symbols), the decision |

E can optionally be two sessions via hierarchical sheets: **E1** owns the `unit_cell`
sheet file, **E2** owns the `power` + `connectors` sheet files. The root sheet is a
chokepoint — one of them owns it, the other adds its sheet via a coordinated hand-off, or
do E as a single session if that's simpler.

### Wave 2 — layout (after E + footprints from A)

| Track | Owns | Blocked by |
|-------|------|------------|
| **F** | `hardware/*.kicad_pcb` | E, A |

Single session. Layout does not parallelize on one board.

### Wave 3 — fab + closeout (after F)

| Track | Owns | Blocked by |
|-------|------|------------|
| **G** | `fab/`, final `reports/` | F |

Wave 3 also re-points Track B's SPICE at the **real exported netlist** (not the modeled
one) and runs Track C's procedures on the physical board.

---

## Ownership matrix (Wave 0 — the rule that prevents collisions)

| Track | May write | Must NOT touch |
|-------|-----------|----------------|
| A | `libraries/**`, `hardware/sym-lib-table`, `hardware/fp-lib-table` | any `.kicad_sch/.kicad_pcb`, `sim/`, `test/`, `scripts/` |
| B | `sim/**`, `reports/sim/**` | `hardware/`, `libraries/`, `test/`, `scripts/` |
| C | `test/**` | `hardware/`, `libraries/`, `sim/`, `scripts/` |
| D | `scripts/**`, `reports/erc|drc/`, `.gitignore`, `README.md` | `hardware/` contents, `libraries/`, `sim/`, `test/` |

Shared docs (`board_spec.md`, the process docs) are **read-only** for all Wave-0 sessions.
The global `docs/SESSION_LOG.md` is **not touched** during parallel work — see below.

---

## Coordination mechanics

### One worktree per session (recommended)

Give each session its own working directory and branch off a shared integration branch, so
they never share a working tree:

```bash
git switch -c integration            # once
git worktree add ../ref200-trackA -b trackA integration
git worktree add ../ref200-trackB -b trackB integration
git worktree add ../ref200-trackC -b trackC integration
git worktree add ../ref200-trackD -b trackD integration
```

Open each Claude Code session in its own `../ref200-trackX` directory. They share the same
git object store but have independent files and branches — no working-tree collisions.
(Fallback if worktrees are awkward: separate branches in separate clones.)

### Per-track logs, not the global log

To avoid every session fighting over `SESSION_LOG.md`, each track logs to its **own** file:

```
docs/sessions/trackA.md
docs/sessions/trackB.md
...
```

Same entry schema as `SESSION_LOG.md`. The global `SESSION_LOG.md` is updated **only at
integration**, summarizing each merged track. This keeps the per-track briefs (below) as
each session's effective kickoff, replacing the single-session "read the top of the global
log" step while parallel work is in flight.

### Reports are pre-partitioned

Each track writes only its own `reports/` subdir (B→`reports/sim`, D→`reports/erc|drc`,
C→`reports/test`), so generated artifacts never collide either.

### Integration order (you, or a dedicated integration session)

Merge to `integration` in dependency order, re-running gates after each:

1. **A first** — libraries are a prerequisite for the schematic; nothing else depends on
   merge order among B/C/D.
2. **B, C, D** — any order; independent.
3. Resolve the RTD/channel decision, then start **E** off the post-A `integration` branch.
4. **F** after E. **G** after F.

At each merge, update the global `SESSION_LOG.md` with a one-entry summary and confirm
`kicad-cli sch erc` / `pcb drc` still pass (once those files exist).

---

## How each Wave-0 session starts

The session's first message is its task brief in `docs/tasks/TRACK_<X>_*.md`. That brief
tells it to read `CLAUDE.md`, `docs/board_spec.md`, the one or two process docs relevant to
its track, and its own track log — then work only within its owned paths. Hand each session
its brief and let it run.
