# Track F — PCB Layout (session log)

Per-track log, newest entry on top. Schema mirrors `docs/SESSION_LOG.md`.

---

## Track F — 2026-06-22..24 — Lay out + route the board, 4-layer, DRC-clean

**Tooling:** KiCad **10.0.3** (`kicad-cli` + bundled `python.exe` with the `pcbnew` API at
`C:\Program Files\KiCad\10.0\bin\`). **`kicad-cli pcb` cannot author/place/route** (only drc /
export / render / import), so the board was authored with the **`pcbnew` Python API** — the same
"no GUI-automation, script it" situation Track E hit for the schematic. Build scripts are kept
**out-of-tree** in `C:\tmp\f_*.py` (precedent: Track E's generator); the **`.kicad_pcb` is the
committed source of truth**.

**Branch / commit at start:** `trackF` @ `8211249`, branched off `integration` (Tracks A–E
merged). Note: `integration` carries the **label-based** E schematic (the later trackE "wire-up"
drawn-wires pass `d19d202` is *not* in integration, but E proved its netlist is **identical**, so
the PCB is unaffected — layout consumes the netlist, not wire geometry).

**Decisions resolved with Lucas (start of session, AskUserQuestion):**
1. **Scope = full scripted layout to DRC 0/0** (place + route everything by script, zones poured).
2. **Stackup = 4-layer JLCPCB** (sig / GND plane / PWR plane / sig) — internal ground plane makes
   the star-ground + analog/digital partition far cleaner on a precision mixed-signal board.
3. **Mechanical = size-to-fit**, edge connectors, 4× M3 corner mounting holes.

**State before:** no `.kicad_pcb` anywhere; `integration` had the E schematic (3 ch, Pt100) +
Track A footprints (10 in `libraries/footprints/rtd-readout.pretty`). **After:** complete,
fully-routed, DRC-clean 4-layer board.

**Board:** **122 × 82 mm**, 4 copper layers — **F.Cu** (signals) / **In1.Cu = GND plane** /
**In2.Cu = PWR plane** / **B.Cu** (signals). JLCPCB 4-layer design rules written to
`rtd-readout.kicad_pro` (`rules`): min clearance via netclasses **0.13 mm**, min track 0.13,
min via Ø0.45 / drill 0.2, min annular 0.075, edge clearance 0.3, hole-to-hole 0.25. 4× M3
(Ø3.2 NPTH) mounting holes at the corners.

**Netclasses (deliverable):** `SENSE` (V_RTD + V_ref pairs: all `CH*_SENSE*`, `CH*_TOP`,
`CH*_MID`), `POWER` (`+5V`, `VS`, `GND`; 0.5 mm track), `I2C` (`SDA`, `SCL`), `Default` —
defined in `kicad-cli pcb drc`-honored `net_settings` of the `.kicad_pro`. (Note: `pcbnew.SaveBoard`
rewrites `net_settings` to a single default class, so the build script re-patches the four classes
+ name patterns into the `.kicad_pro` after every save.)

**Placement / floorplan (protecting the precision-analog path):**
- **RTD 4-wire connectors J1/J2/J3** down the left edge (wires exit outward).
- **R_ref sits at its ADS AIN pins** — the *only* length-critical net is V_ref (TOP/MID → ADS
  IN±); R/CRD→connector and CRD→+5V carry current and are Kelvin-independent, so they may be long.
  R1 at U1 left pads, **R2 at U1 right pads (flipped 180°)**, R3 at U2 left pads → short V_ref.
- **J4 (T7 analog / sense out) moved next to the RTD connectors (left)** → sense pairs are short,
  local, and never cross the digital side. This freed the board centre for the I²C bus.
- **Analog left / digital right partition**, ADS1115s straddle the boundary (analog inputs face
  the R_ref pairs, I²C/VDD face the digital side). Digital cluster (I²C pull-ups R4/R5, J5, bulk
  C4) on the right; power-in J6 + bulk C3 at the bottom (analog rail).

**Routing (deliberate, per-net — no autorouter):**
- **GND**: In1 plane split into **AGND (5602 mm²) + DGND (2555 mm²)**, both net `GND`, joined by a
  **single In1 tie track** = the spec's single-point analog/digital tie / star ground. SMD GND pads
  drop to In1 by via; TH connector pads reach it directly.
- **+5V / VS**: In2 plane split into **+5V (3571 mm², analog left)** and **VS (4664 mm², digital
  right)** zones.
- **V_ref / sense**: `CH*_TOP/MID` on F.Cu at the ADS; **sense pairs on B.Cu (x ≤ 30, analog
  left)** — `SENSE+` straight on B.Cu, `SENSE-` on F.Cu with a B.Cu comb-in via into J4's minus
  column (the 2×04's stacked-pad geometry forced the split).
- **I²C** kept on the **digital right (x ≥ 60)**: SDA on B.Cu (escape vias clear of the 1.5 mm-wide
  MSOP pads, open-B.Cu trunk, F.Cu bus tail), SCL B.Cu trunk + F.Cu tail — on different layers for
  the rightward run so they never cross.
- **MID force-runs** (connector → R_ref) on B.Cu, clear of the localized sense.
- Key trick: **flipping R2 180°** made its pad order match U1's right-pad order, eliminating the
  CH2 TOP/MID swap-crossing without a jumper.
- 35 vias; 83 F.Cu + 26 B.Cu signal segments + 1 In1 tie.

**Validation (with numbers):**
- **DRC: 0 violations / 0 unconnected** — `kicad-cli pcb drc --exit-code-violations
  --severity-error`, **exit 0**; an all-severity run is also **0/0** (no warnings). Zones refilled.
  (Note: `ZONE_FILLER.Fill` segfaults on an in-memory `CreateEmptyBoard()`; the build saves zones
  unfilled, then `f_fill.py` reloads the board and fills — fill succeeds on a reloaded board.)
- **Schematic ↔ PCB consistency: exact.** All **30/30** components present with correct
  `rtd-readout:` footprint association; **all 21/21 nets match the exported netlist pad-for-pad**
  (`f_consist.py` diff empty). The 4 single-pad no-connects (U1/U2 ALERT, U2 AIN2/3) are isolated
  as expected.
- **Partition verified** (`f_review.py`): 4 copper layers; In1 = 2 GND zones + tie; In2 = +5V & VS
  zones; all 6 sense nets on B.Cu at x ≤ 30; SDA/SCL at x 60–112 — precision sense physically
  separated from I²C.
- **3D render** (top + bottom) reviewed — placement + visible F.Cu routing as designed.

**Decisions (rationale + spec ref):**
- **R_ref adjacent to ADS; J4 left; force/CRD lines may be long** — only the V_ref differential
  (R_ref pads → ADS IN±) is length-critical; the RTD voltage is Kelvin-sensed at the RTD and V_ref
  is sensed at R_ref, so trace R on the force/excitation path doesn't enter the result.
  — board_spec §The measurement, §Layout-critical.
- **Split GND plane + single-point tie; split +5V/VS planes; analog-left/digital-right** — directly
  implements board_spec §Layout-critical (star ground, mixed-signal partition, ADS next to its
  R_ref, I²C away from R_ref taps + sense).
- **Clearance 0.13 mm** (not a tighter or looser value): the ADS1115 MSOP-10 has an inherent
  0.15 mm pad gap (0.5 mm pitch); 0.13 is below that and well within JLCPCB 4-layer capability.

**Open issues / risks / deviations:**
- **DEVIATION — sense-line RC filter (layout priority #6) NOT placed.** The ≈1 kΩ + 0.1 µF
  differential RC at the T7 input is **not in the frozen E schematic**, so the parts are absent
  from the netlist; adding them is a **schematic ECO** (the brief forbids touching `*.kicad_sch`
  — request via integration). **Flag for Lucas:** decide whether to add per-sense-pair RC before
  fab (Track G). Layout has room on the sense pairs near J4 if added.
- **No F.Cu/B.Cu outer ground pours** — the internal In1 GND plane sits directly under F.Cu and
  shields; outer copper pours are an optional EMI improvement, deferred (would need a DRC re-pass).
- **Decoupling C1/C2 ≈ 4–5 mm from the ADS VDD pin** — a routability compromise; the VS plane +
  bulk C4 provide HF decoupling. Acceptable for rev-A; move closer in a respin if bench noise warrants.
- Build scripts are **out-of-tree** (`C:\tmp\f_build.py`, `f_route.py`, `f_fill.py`, helpers); the
  `.kicad_pcb` is canonical. A human can hand-prettify routing/silk in Pcbnew from here.

**Next action:** Integrator — merge `trackF` into `integration` after E (gates re-run clean: ERC
0/0 from E, DRC 0/0 here). Then **Track G** (fab: gerbers/drill/pos/STEP from the `rev-A` tag;
`fab/` is gitignored). Recommend resolving the RC-filter ECO decision before the fab drop.

**Commit:** `__PENDING__` (board + project netclasses + this log); tag **`rev-A`**. Hash recorded
in a follow-up.