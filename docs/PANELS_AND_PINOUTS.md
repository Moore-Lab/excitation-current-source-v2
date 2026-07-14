# rev-G — enclosure, panels, and cable pinouts

Board: **100.0 × 159.5 mm**, slides into a **Hammond 1455N1601** (103×53×160, clear anodized,
DigiKey HM979-ND) on the lowest card slot. No mounting holes — the slots carry the board;
**2.5 mm component/outer-copper keepouts along both 159.5 mm edges** (slot engagement) are
respected by the layout. End panels (103×53×1.5 Al) are machined per the DXFs in
`reports/review/panel-sensor.dxf` / `panel-daq.dxf` — **verify the H0=9.54 mm board-top
datum against the physical enclosure before cutting** (Hammond publishes no slot tolerances).

## Sensor end (board x=0): 4× Phoenix PT 1,5/5-3,5-H (push-in, 26–16 AWG, use ferrules)

Per RTD block, pins top→bottom as seen on the panel (pin 1 at each block's north end):

| Pin | Function |
|---|---|
| 1 | Force + (MID) |
| 2 | Sense + |
| 3 | Sense − |
| 4 | Force − (GND return) |
| 5 | **Cable shield** (AGND; land the cryostat STP shield here, one end only) |

Blocks are PT **push-in** (not screw): ferruled wires insert directly through the panel
cutout; the release actuator is on top — remove the end panel (4 screws) for full access.
RTD1=J1, RTD2=J2, RTD3=J3, spare=J7 (top→bottom on the panel).

## DAQ end (board x=159.5)

**RJ45 (J4, Amphenol RJHSE-5380, shielded)** → LabJack T7 AIN via CAT6a S/FTP patch cable
(cut one end, land in the T7/CB37 screw terminals). T568B mapping — each channel rides one
physical twisted pair:

| Channel | RJ45 pins | T568B pair color |
|---|---|---|
| CH1 (T7±) | 1 / 2 | orange (wht-org / org) |
| CH2 | 3 / 6 | green (wht-grn / grn) |
| CH3 | 4 / 5 | blue (blu / wht-blu) |
| CH4 | 7 / 8 | brown (wht-brn / brn) |

Cable **shield → AGND at the board end only** (via the jack shield tails); leave the
pigtail-end shield unterminated. The jack's EMI fingers bond the enclosure panel at the
cutout — this is the **single chassis-ground point** by design.

**I²C/power pigtail (J5, Molex PicoBlade 53048-0410; mate = pre-made pigtail
2181120404, 425 mm, or 2181120402, 225 mm — NO crimping)** → cut the flying-lead end to
length and land in the T7 screw terminals. ⚠ **Pin numbers are deliberately reversed**
(rev-G routing). Identify wire 1 by the pin-1 mark on the pigtail housing / the header's
pin-1 pad (square), then:

| PicoBlade pin | Net | T7 terminal |
|---|---|---|
| 1 | SCL | FIO (I²C SCL) |
| 2 | SDA | FIO (I²C SDA) |
| 3 | GND | GND |
| 4 | VS | VS |

This cable carries the **common-mode reference and the ADS1115 supply — it must be
connected whenever measuring** (the analog cable has no ground conductor).

**Power (J6, Phoenix PT 1,5/2-3,5-H):** pin 1 = +5 V, pin 2 = GND (bench supply).

## Bench-probing note

The 2×5 header is gone; probe the filtered nets at the T7-end pigtail/breakout. The
unfiltered `CHn_SENSE±` test points (TP1–TP12) are unchanged on the board.
