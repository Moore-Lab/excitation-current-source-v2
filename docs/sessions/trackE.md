# Track E — Schematic Capture (session log)

Per-track log, newest entry on top. Schema mirrors `docs/SESSION_LOG.md`.

---

## Track E — 2026-06-22 — Capture full hierarchical schematic, ERC-clean

**Tooling:** KiCad **10.0.3** (`kicad-cli` at `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`).
ngspice/python not needed for Track E. Schematic files are `version 20251024` (v10 format).

**Branch / commit at start:** `trackE` @ `a69b330` — branched off a freshly-created
post-Track-A `integration`. (Setup: an `integration` branch already existed at `d54eb69`
without A; I created `integration`→merge `trackA` (`--no-ff`, commit `a69b330`), moved
`integration` to that merge, restored `main` to `d54eb69` after an accidental merge-on-main,
then branched `trackE`. Topology now: `main`@d54eb69, `integration`@a69b330 (A merged),
`trackE`@a69b330.)

**State before:** Track A libraries present (10 symbols / 10 footprints in `libraries/`,
`hardware/{sym,fp}-lib-table` local-only). `hardware/` had **no** schematic or project file.
board_spec Resolved inputs locked: **Pt100, 3 channels** → 3 unit cells, 2 ADS1115 (0x48/0x49).

**Objective:** Capture the full schematic from `board_spec.md`, ERC-clean, using only the
project-local `rtd-readout` library; export BOM + netlist; satisfy the Track E "Done when".

**Brief vs. assignment note:** my handoff named `docs/tasks/TRACK_E_libraries.md` (does not
exist — tracks were renumbered; "libraries" is now Track A). Lucas confirmed the intent is
**Track E = Schematic Capture** (`TRACK_E_schematic.md`).

**Actions:**
1. Verified env + Track A completeness (KiCad 10.0.3 matches A's pin; A's silent-fatal items —
   CRD polarity pin1=K, ADS1115 VSSOP-10 pinout — already verified in `trackA.md`).
2. **Method de-risking** (KiCad has *no* CLI/stable API to author schematics, only to ERC/
   export): extracted exact v10 syntax from KiCad's own demos (`complex_hierarchy`,
   `simulation/subsheets`, `amplifier-ac`). Empirically confirmed the symbol→sheet pin
   transform: for a symbol at `(at Px Py 0)` (no mirror), a library pin at `(sx,sy)` lands at
   sheet `(Px+sx, Py-sy)`. Built a throwaway spike + ran ERC to confirm: (a) a global label
   placed exactly on a pin endpoint connects with no wire; (b) stock `power:PWR_FLAG` drives
   power nets; (c) all component origins must sit on the **1.27 mm** grid or pins go off-grid.
3. Authored a deterministic generator (kept out-of-tree in `C:\tmp\gen.ps1` + `genlib.ps1`;
   **not** a committed deliverable — the `.kicad_sch` files are the source of truth from here).
   It embeds **verbatim** copies of the `rtd-readout` symbols into each sheet's `lib_symbols`
   (so the ERC lib-mismatch check passes) and connects every pin by a global label at its
   endpoint; power nets driven by one stock `PWR_FLAG` each.
4. Generated the hierarchy and ran the gates.

**Files touched (owned deliverables):**
- `hardware/rtd-readout.kicad_sch` (root: 5 child sheets, title block)
- `hardware/unit_cell_ch1.kicad_sch`, `…ch2…`, `…ch3…`
- `hardware/acquisition.kicad_sch` (2× ADS1115 + decoupling + I²C pull-ups + I²C connector)
- `hardware/power_io.kicad_sch` (power-in, T7 analog connector, bulk caps, PWR_FLAGs)
- `hardware/rtd-readout.kicad_pro` (project file)
- `sim/netlists/rtd-readout.net` (handoff for Track B — see Decisions re: ownership)
- Evidence (untracked, regenerable, Track-D-owned dirs): `reports/erc/erc_kickoff.json`,
  `reports/bom/rtd-readout-bom.csv`, `reports/netlist/`, `reports/rtd-readout.pdf`.

**Design captured (per board_spec signal chain):**
- **3 unit cells** (CH1–3): CRD `D n` anode→`+5V`, cathode→`CHn_TOP`; `R_ref Rn` across
  `CHn_TOP`→`CHn_MID`; `Conn_RTD_4W Jn` Force+←`CHn_MID`, Force−→`GND` (star), Sense± →
  `CHn_SENSE±`; test points on each TOP and MID.
- **Acquisition:** `U1`=ADS1115 0x48 (ADDR→GND), AIN0/1=CH1 TOP/MID, AIN2/3=CH2 TOP/MID;
  `U2`=0x49 (ADDR→VS), AIN0/1=CH3 TOP/MID, **AIN2/3 spare = no-connect**; both VDD→`VS`,
  GND→`GND`, SDA/SCL bussed; `R4`/`R5` 4.7 kΩ pull-ups to `VS`; `C1`/`C2` 0.1 µF per-chip
  decoupling; `J5`=Conn_T7_I2C; SDA/SCL test points. ALERT/RDY unused = no-connect.
- **Power/IO:** `J6`=Conn_Power (+VIN→`+5V`, GND); `J4`=Conn_T7_Analog (3 Sense± pairs + 2
  AGND→GND); `C3`/`C4` 10 µF bulk on `+5V`/`VS`; PWR_FLAGs on `+5V`/`GND`/`VS`; rail + GND
  test points. Only V_RTD (Sense±) leaves as analog; V_ref stays on-board to the ADS1115s.

**Validation (with numbers):**
- **ERC: 0 errors / 0 warnings** — `kicad-cli sch erc --severity-error` exit 0
  (`reports/erc/erc_kickoff.json`); a warning-inclusive run is also 0/0.
- **BOM cross-check vs board_spec** (`reports/bom/rtd-readout-bom.csv`): CRD **D1–D3 = 3**
  (= channels) ✓; R_ref **R1–R3 = 3** ✓; ADS1115 **U1,U2 = 2** (= ceil(3/2)) ✓; I²C pull-ups
  **R4,R5 = 2** ✓; decoupling **C1,C2** + bulk **C3,C4** present ✓; RTD conns **J1–J3 = 3** ✓;
  test points **TP1–TP10 = 10** ✓. Every instance fully fielded (MPN/Manufacturer carried).
- **Netlist node-level check** (21 nets): `+5V`={3 CRD anodes,J6,C3,TP9}; each `CHn_TOP`=
  {CRDn.K,Rn.1,ADS IN+,TP}; each `CHn_MID`={Rn.2,Jn.Force+,ADS IN−,TP}; `GND`(15)= includes
  3 RTD Force− + U1.ADDR (→0x48); `VS`(9)= includes U2.ADDR (→0x49); SDA/SCL = {both ADS, J5,
  pull-up, TP}; Sense pairs → J4. 4 no-connects exactly = U1/U2 ALERT + U2 AIN2/AIN3. ✓
- **PDF render** exit 0 (`reports/rtd-readout.pdf`) — full 6-page hierarchy parses & plots.

**Decisions (rationale + spec ref):**
- **Connectivity by global label, not drawn wires** — KiCad has no schematic-authoring API,
  so files are generated; labels-on-pin-endpoints give a guaranteed-correct netlist without
  fragile wire geometry. Electrically identical; a human can prettify in Eeschema later. The
  `.kicad_sch` is the canonical source from now on (generator is a one-time aid).
- **ACCEPTED DEVIATION — Hierarchy = root + 3 separate `unit_cell_chN` sheets** (not one sheet
  reused ×3), deviating from the brief's "unit_cell sheet (×N)". Reason: distinct per-channel
  **global** nets (`CHn_*`) require distinct sheets; one reused sheet would need sheet-pin/
  hierarchical-label plumbing per instance, far more error-prone to hand-author. Same parts/
  counts, ERC-clean. (`PARALLEL_PLAN.md` allows the E1/E2 split; this is a finer split.)
  **Status: accepted** by Lucas (2026-06-22) and at integration review for this frozen
  3-channel board. **Consequence (recorded):** there is no single source unit cell — a future
  change to the unit cell must be applied **to all three `unit_cell_chN.kicad_sch` sheets by
  hand**. A one-line note to this effect is in the root `rtd-readout.kicad_sch` (title-block
  `comment 2` + an on-canvas `(text ...)` note) so the next reader isn't surprised.
- **AGND ≡ GND (single net)** — board_spec calls for analog/digital ground **partition with a
  single-point tie**; that tie is a **layout** construct (Track F), so schematically it is one
  `GND` net. J4 AGND pins and all returns are on `GND`. — board_spec §Layout-critical points.
- **No on-board LDO** — board_spec specifies the 5 V rail comes in (`+VIN`) and the ADS1115s
  run from the T7's `VS` (3.3–5 V); it does **not** call for on-board regulation. `+5V`
  (analog rail, CRDs) and `VS` (digital, ADS+pull-ups) are separate domains, each PWR_FLAG-
  driven. — board_spec §ADS1115, §Board as the hub.
- **R_ref = 910 Ω, pull-ups = 4.7 kΩ, bulk = 10 µF, decoupling = 0.1 µF** — board_spec §R_ref
  (V_ref ≈200 mV in ADS ±0.256 V) and §ADS1115 (4.7 kΩ typ, per-chip decoupling).
- **Netlist written to `sim/netlists/`** — the Track E "Done when" explicitly requires this
  handoff for Track B's Wave-3 re-point, overriding the Wave-0 "don't touch sim/" guard for
  this one generated artifact. Flagged here for the integrator.

**Open issues / risks:**
- Schematic is **label-connected** (no drawn wires/junctions); visually it reads as labelled
  pin stubs, not a traditional drawing. Functionally complete and ERC/BOM/netlist-correct, but
  if Lucas wants a "pretty" schematic for review, that's GUI cleanup (purely cosmetic).
- `reports/` gate artifacts (erc/bom/netlist/pdf) were **removed** from the worktree per the
  integration-review housekeeping note (they sit in Track D's owned dirs and are regenerable);
  the tree is clean for merge. ERC 0/0 re-confirmed before this commit. Track D / the
  integrator regenerates committed gate snapshots.
- ERC is 0/0 with default severities; if Track F's later edits change pin usage, re-run ERC.

**Next action:** Integrator: merge `trackE` into `integration` after A (done) — gates re-run
clean. Then **Track F** (layout) off post-E `integration`: respect star-ground at the RTD
Force− returns, keep the I²C/`VS` digital side away from the `CHn_TOP/MID` taps and Sense
pairs, ADS1115 next to its two R_ref pairs, light RC on Sense at the T7 input.

**Commit:** `6c807e0` (schematic + libs + netlist + log); this hash recorded in a follow-up.
