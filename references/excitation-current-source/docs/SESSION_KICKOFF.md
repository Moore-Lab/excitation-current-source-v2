# SESSION_KICKOFF.md

This is the start-of-session procedure for developing the REF200 RTD board in KiCad.
Run it **in order** at the beginning of every session. It exists so that each session
starts from verified ground truth instead of assumptions, and ends in a state the next
session can pick up cleanly.

---

## A. Orient (recover state)

1. **Read the top entry of `docs/SESSION_LOG.md`.** Newest entries are at the top. From
   it, extract: the current phase, the last completed action, open issues/risks, and the
   single "Next action" line.
2. **Read `docs/board_spec.md`.** This is the electrical source of truth. The two open
   inputs at the bottom (RTD type, channel count) gate component values — if they are
   still unresolved, the first task is to surface that to Lucas, not to guess.
3. **Skim `docs/BOARD_DEV_CHECKLIST.md`** for the phase you are in.

## B. Verify the environment (don't assume it matches the log)

4. Check the toolchain and record versions:
   - `kicad-cli version` — must match the version pinned in the latest log entry. If it
     changed, note it; a KiCad major-version bump can rewrite file formats.
   - `ngspice --version` — required for the SPICE plan.
   - `python --version` and confirm the project venv (if used) is active.
5. Check git state: `git status`, `git branch --show-current`, `git log --oneline -5`.
   Confirm the working tree is clean and you are on a development branch (not `main`).
   If there are uncommitted changes from a crashed prior session, reconcile them against
   the log before continuing.

## C. Confirm ground truth (re-run the gates)

6. If a schematic exists, run ERC and confirm it matches the log's claim:
   ```
   kicad-cli sch erc --exit-code-violations --severity-error \
     --output reports/erc/erc_kickoff.rpt hardware/<project>.kicad_sch
   ```
7. If a PCB exists, run DRC likewise:
   ```
   kicad-cli pcb drc --exit-code-violations --severity-error \
     --output reports/drc/drc_kickoff.json hardware/<project>.kicad_pcb
   ```
8. If these disagree with the log (log says "DRC clean" but it isn't), **stop and
   reconcile.** A wrong log is a bug; fix the log's accuracy before doing new work.

## D. Plan before editing

9. Restate the session objective in one or two sentences, derived from the log's "Next
   action" line. If the next action is ambiguous or blocked on a decision from Lucas, ask
   — do not invent scope.
10. Write a short ordered plan (3–7 steps) for this session. Identify which validation
    gate each step must pass before it counts as done.

Only now begin work.

---

## During the session

- Work in small, reversible steps. After any change to schematic or layout, re-run the
  relevant gate (ERC for schematic, DRC for layout) before moving on.
- Commit at each meaningful checkpoint with a message that names the change and its
  validation result, e.g. `sch: add channel 3 unit cell; ERC clean (0/0)`.
- When you make a design decision (component value, netclass width, grounding choice),
  record it in the log's decisions list **as you make it**, with the reason and the
  spec reference. Don't reconstruct decisions from memory at the end.
- If you deviate from `docs/board_spec.md`, log the deviation and rationale before acting.

## End of session (mandatory)

Before you stop, append a new entry to the **top** of `docs/SESSION_LOG.md` using the
schema defined in that file. It must contain:

- Date, session id, and the objective you actually worked on.
- State before vs after.
- Files touched.
- Validation results with **numbers** (ERC errors/warnings, DRC violations, sim pass/fail).
- Decisions made and why.
- Open issues and risks.
- The single most important thing: the **exact next action** for the next session.
- The git commit hash that captures this state.

Then commit, including the log update. The session is not complete until the log is
written and committed.
