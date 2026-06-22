# Track D log — Automation, Gates & Repo Meta

Per-track development record (parallel mode). **Newest entry on top.** Same schema as
`docs/SESSION_LOG.md`. Integration folds a one-line summary of this into the global log.

---

## Track D / Session 1 — 2026-06-22 — Stand up the gate scripts, run_gates, README

**Tooling:** KiCad **10.0.3** (`C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`); ngspice not
installed; Python is only the Windows Store stub (not real) → **gate scripts are POSIX `sh`,
not Python.** Bash tool = Git Bash.
**Branch / commit at start:** `trackD` @ d54eb69 (own worktree `../rtd-trackD`), clean.
**State before:** Repo skeleton only. `scripts/` held just `.gitkeep`; `reports/{erc,drc,bom}/`
empty; `.gitignore` authored in Session 001; `README.md` a stub explicitly inviting Track D to
expand it. No `hardware/*.kicad_sch|pcb` yet.

**Objective:** Turn the checklist's canonical `kicad-cli` gate commands into one-command,
machine-checkable scripts; a single `run_gates` that degrades gracefully before the design
exists; expand the README; confirm `.gitignore`.

**Actions:**
1. Verified env: located KiCad 10.0.3; confirmed **every** canonical flag (ERC/DRC/BOM/
   netlist/gerbers/drill/pos/step) exists in 10.0.3 via `--help`.
2. Wrote `scripts/lib.sh` (sourced): kicad-cli discovery (`$KICAD_CLI` → PATH → Windows
   install glob), path/board constants, pinned-version warn, indicative severity tally.
3. Wrote wrappers `erc`, `drc` (adds `--refill-zones`, never `--save-board`), `export_bom`
   (includes **Tempco**), `export_netlist`, `fab_drop` (gerbers/drill/pos/step/bom → `fab/`).
4. Wrote `scripts/run_gates`: ERC+DRC, `--tag`, nonzero on any error, **exits 0 with
   "nothing to check" when no design files exist**.
5. Optional: `scripts/hooks/pre-commit` + opt-in `scripts/install_hooks` (not auto-installed
   → won't disturb sibling worktrees). `chmod +x` on all runnables.
6. Expanded `README.md` (architecture, pinned KiCad, gate usage, fab-drop recipe, PARALLEL
   pointer). Confirmed `.gitignore` (left unchanged — already correct).

**Files touched:** `scripts/{lib.sh,run_gates,erc,drc,export_bom,export_netlist,fab_drop,
install_hooks,hooks/pre-commit}`, `README.md`, `docs/sessions/trackD.md`.

**Validation (with numbers):**
- `run_gates` (no design files): **exit 0**, discovers kicad-cli 10.0.3, prints "nothing to
  check". `--help` and `--tag s999` also exit 0.
- `erc` / `drc` invoked directly with no input: **exit 2**, clear "not found" error.
- Smoke test of the exact ERC + BOM command lines against KiCad demo
  `pic_programmer.kicad_sch`: ERC **exit 0** ("Found 0 violations", JSON written); severity
  tally `0/0`; BOM **exit 0** with header containing the `Tempco` column. (Temp dir, cleaned.)
- ERC/DRC against this project: **n/a** — no `hardware/*.kicad_*` yet (expected).

**Decisions (rationale + spec ref):**
- **POSIX `sh`, not Python** — Python isn't really installed here and the gates only shell out
  to `kicad-cli`; `sh` runs under Git Bash (Windows) and natively elsewhere. Pin = KiCad
  10.0.3 in `lib.sh` (`SESSION_KICKOFF.md` step 4).
- **Graceful degrade in `run_gates`, hard-fail in wrappers** — orchestrator handles "design
  not present yet" (Track E/F not landed); individual wrappers assume their input exists and
  exit 2 if not. Keeps the brief's "usable before Track E" requirement clean.
- **Default report tag `latest` (overwrites)** — committed `reports/**` diffs cleanly; pass
  `--tag sNNN` for a session-stamped copy (`DIRECTORY_MANAGEMENT.md` §Naming).
- **DRC `--refill-zones` but not `--save-board`** — meaningful check (Phase 3 wants zones
  refilled) without mutating Track F's `.kicad_pcb` source.
- **`.gitignore` left unchanged** — Session 001's version already satisfies the spec
  (`*.kicad_prl` ignored, `*.kicad_pro` tracked, `fab/`, python, sim scratch). Confirmed, not
  churned.
- **Pre-commit hook opt-in, not auto-installed** — worktrees share the common hooks dir;
  auto-installing would block/alter sibling tracks' commits. Integrator runs `install_hooks`.

**Open issues / risks:**
- Real ERC/DRC against *this* board is unproven until Track E (schematic) and Track F (PCB)
  land — by design. Flags are verified against 10.0.3 and the command shapes are smoke-tested
  on a demo, so they should run as-is at integration.
- `export_netlist` writes into `sim/netlists/` (Track B's tree). The script never runs at
  author time; only integration/Track B invokes it. No Wave-0 contention.
- If a contributor uses a different KiCad major, `lib.sh` warns but does not block — intended
  (format-bump awareness lives in the log per kickoff).

**Next action:** Integration: after Track A merges and Track E produces
`hardware/rtd-readout.kicad_sch`, run `sh scripts/run_gates` (now non-vacuous) and commit the
resulting `reports/{erc,drc}/` JSON; optionally `sh scripts/install_hooks` on `integration`.

**Commit:** 213ee50 (scripts + README + this log). Hash recorded by the follow-up log commit.