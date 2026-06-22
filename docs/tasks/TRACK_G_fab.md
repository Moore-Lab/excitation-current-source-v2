# TRACK G — Fab Outputs & Closeout  *(Wave 3 — gated)*

> **Do not start until:** Track F (layout, DRC-clean, tagged `rev-A`) is merged into
> `integration`. Single session.

Claude Code session, **Track G**. Read `CLAUDE.md`, `docs/board_spec.md`,
`docs/BOARD_DEV_CHECKLIST.md` (Phase 4), `docs/TESTING_PLAN.md`, `docs/SESSION_KICKOFF.md`,
and your log `docs/sessions/trackG.md`. Work **only** in your owned paths.

## Owned paths (exclusive write)
`fab/**` (gitignored output), `reports/**` (final review artifacts)

## Must NOT touch
`hardware/*` (frozen at `rev-A` — any change means a new rev via E/F and a re-tag),
`libraries/`, `sim/`, `host/`, `test/`, `scripts/` source.

## Goal
Produce the manufacturing package from the tagged layout and close out the design review.

## Deliverables
- From the tagged `rev-A` board, generate via the Track-D wrappers / `kicad-cli`:
  gerbers, drill, pick-and-place (pos), STEP, and the final BOM. Output to `fab/`
  (gitignored); capture the drop with tag `fab-rev-A`.
- Final review artifacts to `reports/`: schematic PDF, 3D render, DRC report, BOM review vs
  `board_spec.md` (CRD = channels, ADS1115 = ceil(ch/2), R_ref = channels, pull-ups/
  decoupling).
- Fab-readiness check: layer/stackup, drill, fab notes, panelization if required by the fab.

## Closeout / hand-off to verification
- **Re-point Track B's SPICE** at the real netlist `sim/netlists/rtd-readout.net` and re-run
  the harness against the as-designed circuit; archive reports in `reports/sim/`.
- Confirm Track C's `host/` + bench procedures are ready to run on the physical board
  (TESTING_PLAN Part 2), especially **cross-cal (Stage 2)**, **noise/position-independence
  (Stage 5)**, **thermal C-drift (Stage 7)**, and **CRD-noise (Stage 8)**.
- Update the global `SESSION_LOG.md` with the rev-A closeout summary.

## Done when
- `fab/` package generated and tagged `fab-rev-A`; final reports committed; SPICE re-run
  against the real netlist passes; verification hand-off documented.
- Committed on `trackG`; log updated.

## Coordination
Branch `trackG` off post-F `integration`. Commit; integration is the last merge. Log to
`docs/sessions/trackG.md`.
