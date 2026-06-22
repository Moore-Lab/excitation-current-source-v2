# SESSION_KICKOFF.md

Start-of-session procedure. Run it **in order** every session so work starts from verified
ground truth and ends in a state the next session can resume cleanly.

> Parallel mode: if you were handed a `docs/tasks/TRACK_*.md` brief, that brief is your
> kickoff. Read it, read this file's "During" and "End of session" sections, read your own
> `docs/sessions/<track>.md` log, and stay inside your owned paths. The steps below in full
> apply to single-session and integration work.

## A. Orient (recover state)

1. Read the top entry of the relevant log (per-track log in parallel mode; else
   `docs/SESSION_LOG.md` — newest on top). Extract: current phase, last completed action,
   open issues, and the single "Next action" line.
2. Read `docs/board_spec.md`. This is the electrical source of truth. Note the two open
   inputs (RTD type, channel count); if unresolved and your task needs them, surface to
   Lucas rather than guess.
3. Skim `docs/BOARD_DEV_CHECKLIST.md` for your phase.

## B. Verify the environment

4. Record tool versions: `kicad-cli version` (must match the pinned version in the log),
   `ngspice --version`, `python --version` + venv. A KiCad major bump can rewrite file
   formats — note it.
5. Check git: `git status`, `git branch --show-current`, `git log --oneline -5`. Clean tree,
   on a dev/track branch (not `main`). Reconcile any crashed-session leftovers against the
   log first.

## C. Confirm ground truth (re-run the gates)

6. If a schematic exists:
   ```
   kicad-cli sch erc --exit-code-violations --severity-error \
     --format json --output reports/erc/erc_kickoff.json hardware/rtd-readout.kicad_sch
   ```
7. If a PCB exists:
   ```
   kicad-cli pcb drc --exit-code-violations --severity-error \
     --format json --output reports/drc/drc_kickoff.json hardware/rtd-readout.kicad_pcb
   ```
8. If results disagree with the log, **stop and reconcile.** A wrong log is a bug — fix its
   accuracy before new work.

## D. Plan before editing

9. Restate the objective in 1–2 sentences from the log's "Next action". If it's ambiguous or
   blocked on a Lucas decision, ask — don't invent scope.
10. Write a short ordered plan (3–7 steps); name the gate each step must pass to count as done.

Begin work only now.

## During the session

- Small reversible steps. After any schematic/layout change, re-run the relevant gate.
- Commit at each checkpoint with the validation result in the message, e.g.
  `sch: add ADS1115 subsystem (4 chips, I2C); ERC clean (0/0)`.
- Record design decisions in the log **as you make them**, with reason and spec reference.
- Log any deviation from `docs/board_spec.md` before acting on it.

## End of session (mandatory)

Append a new entry to the **top** of your log using the schema in `SESSION_LOG.md`:
date/session id, objective, state before→after, files touched, validation results **with
numbers** (ERC errors/warnings, DRC violations, sim pass/fail), decisions + rationale, open
issues/risks, the **exact next action**, and the git commit hash. Then commit, including the
log update. The session is not done until the log is written and committed.
