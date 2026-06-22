# CLAUDE.md — Project Bootstrap

**Project:** Multi-channel 4-wire RTD readout board. Per-channel current-regulator diode
(CRD) excitation + precision reference resistor; V_RTD read on a LabJack T7 Pro's existing
differential pairs; V_ref digitized on-board by I²C ADS1115s; **live ratiometric** with a
per-channel cross-calibration constant. Designed in KiCad.

Claude Code reads this file automatically at the start of every session. Its only job is to
route you into the real process.

## Do this first, every session — no exceptions

1. Read **`docs/SESSION_KICKOFF.md`** in full and follow it step by step.
2. It will direct you to read the relevant session log (per-track log in parallel mode, or
   `docs/SESSION_LOG.md` otherwise) to recover state, then verify that state against the
   actual repo before touching anything.

If you are a parallel-track session, your first message is your task brief in
`docs/tasks/TRACK_*.md`; follow it and stay inside your owned paths.

## The canonical documents

| File | Purpose |
|------|---------|
| `docs/SESSION_KICKOFF.md` | Start/end-of-session procedure |
| `docs/SESSION_LOG.md` | Integration-level development record |
| `docs/board_spec.md` | Electrical design source of truth |
| `docs/DIRECTORY_MANAGEMENT.md` | Where every file lives; source vs generated |
| `docs/BOARD_DEV_CHECKLIST.md` | Engineering discipline gates |
| `docs/TESTING_PLAN.md` | SPICE (you run) + bench (Lucas runs) + reporting |
| `docs/PARALLEL_PLAN.md` | How multiple sessions run at once without collisions |
| `docs/tasks/TRACK_*.md` | Per-session task briefs (A–G) |

## Hard rules

- Never commit a state with ERC or DRC **errors**. Warnings are fixed or justified in the log.
- Every design choice traces to `docs/board_spec.md`. Log any deviation before acting.
- Verify, don't trust: re-run gates yourself rather than believing the log.
- The result is ratiometric across **two ADCs** (T7 + ADS1115). Protect the precision-analog
  path and keep the I²C/digital side away from it — this is the dominant layout concern.
- End every session by updating the log and committing.
