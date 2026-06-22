# CLAUDE.md — Project Bootstrap

**Project:** Multi-channel 4-wire RTD readout board (REF200 current sources → LabJack T7 Pro), designed in KiCad.

Claude Code reads this file automatically at the start of every session. Its only job is to route you into the real process.

## Do this first, every session — no exceptions

1. Read **`docs/SESSION_KICKOFF.md`** in full and follow it step by step.
2. The kickoff will direct you to read `docs/SESSION_LOG.md` (most recent entry first) to recover state, then verify that state against the actual repo before touching anything.

Do not start editing schematics, layout, or scripts until you have completed the kickoff sequence.

## The canonical documents

| File | Purpose |
|------|---------|
| `docs/SESSION_KICKOFF.md` | What to do at the start and end of every session |
| `docs/SESSION_LOG.md` | Running development record — source of truth for "where we left off" |
| `docs/board_spec.md` | Electrical design spec — source of truth for "what we are building" |
| `docs/DIRECTORY_MANAGEMENT.md` | Where every file lives and what is source vs generated |
| `docs/BOARD_DEV_CHECKLIST.md` | Engineering discipline gates for good PCB development |
| `docs/TESTING_PLAN.md` | SPICE verification (you run) + bench verification (Lucas runs) + reporting |

## Hard rules (full rationale in BOARD_DEV_CHECKLIST.md)

- Never commit a state with ERC or DRC **errors**. Warnings must be either fixed or explicitly justified in the session log.
- Every design choice traces back to `docs/board_spec.md`. If you deviate, record the deviation and reason in the log before proceeding.
- Verify, don't trust: re-run the validation gates yourself rather than believing the log's claimed state.
- End every session by updating `docs/SESSION_LOG.md` and committing.
