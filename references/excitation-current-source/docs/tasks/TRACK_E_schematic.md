# TRACK E — Schematic Capture (Wave 1)

You are a Claude Code session running **Track E** — the schematic for the REF200 RTD board.
This is **Wave 1**: it depends on Track A (libraries, merged) and the resolved design in
`board_spec.md`. Run this session **interactively** (not as a background agent — background jobs
can't approve permission prompts) and in your **own `git worktree`** off `integration` (a shared
working tree caused branch collisions in Wave 0).

## Orientation (read first)
`CLAUDE.md`; `docs/board_spec.md` — especially **"Resolved configuration"** (200 µA / Mode A),
§1 unit cell, §2 REF200 pinout, §5 AIN budget, §6 layout/wiring; `docs/BOARD_DEV_CHECKLIST.md`
Phase 1; `docs/DIRECTORY_MANAGEMENT.md` (naming); `docs/sessions/trackA.md` (library nicknames,
exact MPNs, and the Mode-A strap note); then write your log at `docs/sessions/trackE.md`.

## Locked design point (do NOT re-open — decided through Session 003)
Pt100 · **3 channels** · **200 µA** · **REF200 Mode A** (both sources paralleled, 1 chip/channel
→ **3× REF200**) · **R_ref = 100 Ω** (`R_Precision`, Vishay VSMP1206) · **full-differential
4-wire** (12 of 14 AIN) · T7 **±0.1 V** range · V_ref = 20 mV, V_RTD = 16–31 mV.

## Owned paths (write ONLY here)
`hardware/ref200-rtd.kicad_pro`, `hardware/ref200-rtd.kicad_sch` (+ any hierarchical sheet
`.kicad_sch`). You **consume** `libraries/` via the existing `hardware/{sym,fp}-lib-table`
(nickname `ref200-rtd`) — do not edit libraries.

## Must NOT touch
`libraries/**`, `sim/**`, `test/**`, `scripts/**`, shared docs (read-only except
`docs/sessions/trackE.md`). Do not edit the lib-tables (Track A owns them).

## What to capture
Per channel (×3), as a repeated unit cell (hierarchical sheet recommended):
- **REF200 in Mode A:** pins **8 + 7 → +5 V rail**; pins **1 + 2 → TOP node** (→ R_ref);
  **pin 6 → GND**; pins **3/4/5 NC** (mirror unused). (board_spec §2, Fig. 19a.)
- **R_ref (`R_Precision` 100 Ω) on top**, TOP→R_ref→MID. RTD on the **bottom** (4-wire):
  MID = Force+ to the RTD; **Sense+/Sense−** Kelvin at the RTD terminals; **Force− → star GND**.
- **Full-differential AIN:** V_ref pair = (TOP, MID); V_RTD pair = (Sense+, Sense−). 4 AIN/ch.
- **Per-channel sense RC BEFORE the mux:** ~**100–200 Ω matched** series per line + **0.1 µF**
  differential (NOT 1 kΩ — 20 nA T7 bias × 1 kΩ = 20 µV/line; board_spec §6).
- Optional **1N4148W** reverse clamp per source (board_spec §2, datasheet Fig. 17a).
Shared:
- **Power:** LP2985-5.0 LDO → clean +5 V rail, decoupling per its datasheet; input from existing
  supply; **no DC-DC buck**. `PWR_FLAG` on rail and GND.
- **Connectors:** one **4-pos screw terminal per RTD** (Force+/Sense+/Sense−/Force−) ×3 + a
  **2-pos** power-in. **Star ground** symbol where all Force− returns + LDO GND + T7 GND meet.
- **Test points** (board_spec §6 / checklist Phase 3): each channel's TOP (V_ref+), MID, Sense+,
  Sense−, the rail, and GND.
- Per-channel-scoped net labels (`CH1_FORCE+`, `CH1_SENSE+`, …).
- Every symbol fully fielded (Value, Footprint `ref200-rtd:…`, MPN, Manufacturer, Datasheet).

Offset nulling is handled in firmware/bench (Track C reads a zero/short per channel) — no special
schematic parts are required, but if a hardware zeroing provision is desired, note it in your log.

## Gate (Phase 1)
`bash scripts/run_gates` (or `kicad-cli sch erc --exit-code-violations --severity-error` with the
full KiCad path `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`). **ERC must be 0 errors**; justify
or fix every warning. Write the report to `reports/erc/erc_e.json`.

## Done when
Schematic complete and matches board_spec §1–§2 topology (REF200 Mode A, RTD at the bottom,
Force/Sense separated to the connector), every symbol fielded, **ERC 0 errors** (report committed),
`docs/sessions/trackE.md` written. Commit on branch `trackE` in your worktree; **do not merge** —
integration pulls you in (then Wave 2 / Track F does layout).
