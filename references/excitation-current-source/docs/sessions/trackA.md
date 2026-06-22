# Track A — Component Libraries — session log

Per-track log (PARALLEL_PLAN.md). Newest entry on top. The global `SESSION_LOG.md` is
updated only at integration.

## Track A — 2026-06-19 — Stand up project-local symbol/footprint/3D libraries

**Tooling:** KiCad **10.0.3** (`C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`, not on PATH),
Python 3.12.
**Branch / commit at start:** `trackA` created off `integration` @ db709f3.

**State before:** `libraries/` empty (only `.gitkeep`); no lib-tables; design resolved
(Pt100, 3 ch, 100 µA, Mode B, 2× REF200, R_ref = 100 Ω, full-diff 4-wire — `board_spec.md`).

**Objective:** Project-local symbol + footprint + 3D libraries + lib-tables so Track E can
build the schematic reproducibly, with REF200 pinout and all land patterns verified.

**Actions:**
- Footprints: copied KiCad's canonical (IPC/JEDEC, datasheet-verified) footprints into
  `libraries/footprints/ref200-rtd.pretty` (SOIC-8, R_1206, R_0805, C_0805, MKDS 1×04 & 1×02
  screw terminals, SOD-123, SOT-23-5, TestPoint D1.5mm). Repointed every 3D `model` path from
  `${KICAD10_3DMODEL_DIR}/…` to project-local `${KIPRJMOD}/../libraries/3dmodels/…` and copied
  the 8 `.step` models in, so the project is self-contained/portable.
- Symbols: authored `libraries/symbols/ref200-rtd.kicad_sym` (9 symbols). REF200AU authored as
  a **single body with all 8 pins explicitly named** per `board_spec.md` §2 (KiCad's stock
  symbol splits it into 4 units with unnamed pins — single body is auditable at a glance).
  R, C, D_1N4148, LP2985-5.0, Screw_Terminal_01x02/01x04, TestPoint adapted from KiCad's
  canonical symbols (exact pin geometry/conventions preserved), then fully fielded.
- Each symbol carries Value, Footprint (project nickname `ref200-rtd:`), Datasheet, MPN,
  Manufacturer; R_Precision additionally carries Tolerance, TempCo, Power, Series.
- Wrote `hardware/sym-lib-table` and `hardware/fp-lib-table` pointing **only** at the
  project-local libs via `${KIPRJMOD}/../libraries/…` (nickname `ref200-rtd` for both).
- Datasheets: committed `1N4148W_diodes.pdf` (clean download) + `docs/datasheets/README.md`
  index with canonical URLs and the verified parameters the fields encode. TI (REF200, LP2985)
  and Vishay/Mouser (VSMP) block automated download (HTML interstitial / anti-bot), so those
  are URL-referenced rather than committed as fake PDFs.

**Files touched:** `libraries/symbols/ref200-rtd.kicad_sym`,
`libraries/footprints/ref200-rtd.pretty/*.kicad_mod` (9), `libraries/3dmodels/*.step` (8),
`hardware/sym-lib-table`, `hardware/fp-lib-table`, `docs/datasheets/README.md`,
`docs/datasheets/1N4148W_diodes.pdf`, `docs/sessions/trackA.md`.

**Validation (numbers):**
- `kicad-cli sym upgrade --force`: **exit 0** (strict parse OK). `sym export svg`: **9/9**
  symbols rendered.
- `kicad-cli fp upgrade --force`: **exit 0** on the .pretty. `fp export svg`: **9/9**
  footprints rendered (Cu+silk+courtyard).
- **REF200AU pin map: 8/8 match** the `board_spec.md` §2 datasheet table
  (1 I1_Low, 2 I2_Low, 3 Mirror_Common, 4 Mirror_Output, 5 Mirror_Input, 6 Substrate,
  7 I2_High, 8 I1_High) — cross-checked against KiCad's official `Reference_Current:REF200AU`.
- Footprint geometry sanity-checked: SOIC-8 1.27 mm pitch / 8 pads (MS-012AA); MKDS 1×04 four
  THT pads @ 5.08 mm pitch, pad 1 square; SOD-123 pad 1 = cathode (matches D symbol pin 1 = K);
  SOT-23-5 five pads; TestPoint excluded from BOM/pos. lib-table relative paths resolve from
  `hardware/`.
- ERC/DRC: n/a (no schematic/PCB yet).

**Decisions (rationale + spec ref):**
- **Copy canonical KiCad footprints, don't re-author** — they are IPC/datasheet-verified;
  re-authoring land patterns by hand is the larger silent-fatal risk. `DIRECTORY_MANAGEMENT.md`
  (project-local libs). Provenance kept in each footprint's `descr`.
- **REF200AU single named-pin body** — `board_spec.md` §2; makes the pinout reviewable and the
  Mode-B strap + "mirror open / substrate→GND" obvious.
- **R_ref = Vishay VSMP1206, MPN `Y1625100R000Q9R` (0.02 %, 0.2 ppm/°C, 1206 Z-Foil).**
  **Deviation from the 0.01 % target in `board_spec.md` §3/§Resolved:** the firm requirement is
  ≤10 ppm/°C, which 0.2 ppm/°C beats ~50×; this is a **ratiometric** design (R_ref measured per
  board), so tempco/drift — not initial tolerance — dominates. The ±0.01 % grade of the same
  VSMP1206 series is a drop-in (identical footprint) if untrimmed absolute tolerance is wanted.
- **LDO = TI LP2985-5.0 (`LP2985IM5X-5.0/NOPB`), SOT-23-5** — real, low-noise, KiCad-verified
  pinout. Spec §4 says the LDO is non-critical (ratiometric rejects rail noise); treat the exact
  LDO as a power-stage choice. 3.3 V grade is a drop-in.
- **1N4148W (`1N4148W-7-F`), SOD-123** — optional reverse-V clamp, REF200 datasheet Fig. 17a.
- **Phoenix MKDS series designators** as MPN (`MKDS 1,5/4-5,08`, `MKDS 1,5/2-5,08`) rather than
  fabricated numeric order codes.

**Open issues / risks:**
- **SHARED WORKING TREE (setup deviation from PARALLEL_PLAN).** Tracks A–D are running in ONE
  working directory (no `git worktree` per track). The checked-out branch is shared via
  `.git/HEAD`; during this session it was switched to `trackD` by a concurrent session, and
  `sim/**` (B) and `test/**` (C) appeared as untracked files. I committed Track A **via git
  plumbing** (`read-tree`/`write-tree`/`commit-tree`/`update-ref refs/heads/trackA`) so HEAD was
  never moved and no other track's files were touched. This works but is racy — **integration
  should move to real per-track worktrees, or serialize commits.**
- LDO exact part/pinout is a sound real default but should be reconfirmed against the finally
  chosen LDO before schematic sign-off.
- R_ref tolerance grade (0.01 vs 0.02 %) to finalize at order time.
- 3D `model` paths use `${KIPRJMOD}/../libraries/3dmodels/…`; verify they resolve once the
  `hardware/` KiCad project exists (Track E creates the `.kicad_pro`).

**Next action (for integration / Track E):** Merge `trackA` first. Track E builds the schematic
using nickname `ref200-rtd` for both symbols and footprints; place REF200AU in Mode B (pin 8/7→
+5 V, pin 1/2→R_ref→RTD, pin 6→GND, pins 3/4/5 NC), R_Precision for R_ref, LP2985-5.0 for power,
Screw_Terminal_01x04 per RTD + 01x02 for power in.

**Commit:** trackA @ 227ca2f (libraries + lib-tables + datasheets; this hash line added in
the immediate follow-up commit).
