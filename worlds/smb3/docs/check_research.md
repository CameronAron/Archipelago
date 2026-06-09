# SMB3 Check Research Notes

This note records the current first pass at expanding clear checks beyond World 1
using the bundled `Super Mario Bros. 3 (USA).nes` ROM.

## Confidence level

The later-world flag mappings should be treated as **candidate data**, not final
verified memory research.  The World 1 bits were sanity-checked against the
current implementation and the World 1 fortress mapping.  For Worlds 2 through 8,
I extracted overworld tile coordinates from the bundled ROM and converted those
coordinates to `$7D00` byte/bit candidates using the observed World 1 pattern.
That is enough to guide the next implementation step, but it is not enough to be
fully confident without emulator-side validation.

Before relying on these mappings for release, each candidate should be validated
in BizHawk by clearing the relevant node, watching `$7D00-$7D3F`, and confirming
that exactly the expected bit changes while the current world counter at `$0727`
matches the intended world.

## SRAM completion buffer hypothesis

The game appears to store overworld completion state in the 64-byte per-player
buffer at `$7D00`.  Each byte maps to a 16x16-tile column of the current
overworld map; horizontal maps use columns `0x00` through `0x3F`.  Bits `7`
through `1` map to rows `0` through `6`; bit `0` is used for the bottom course
row.  Because this buffer is reused for each loaded map, client-side check
detection must combine `$0727` (the current world index) with the byte/bit pair.

## ROM map data used

The bundled USA ROM's overworld maps are stored as eight `0xFF`-terminated maps
at file offsets `0x185BA` through `0x19071`.  Each map is nine rows tall and
varies from one to four 16-column screens wide:

| World | ROM offset | Columns |
| --- | ---: | ---: |
| 1 | `0x185BA` | 16 |
| 2 | `0x1864B` | 32 |
| 3 | `0x1876C` | 48 |
| 4 | `0x1891D` | 32 |
| 5 | `0x18A3E` | 32 |
| 6 | `0x18B5F` | 48 |
| 7 | `0x18D10` | 32 |
| 8 | `0x18E31` | 64 |

Numbered levels were identified from their map tile values (`0x03` = level 1,
`0x04` = level 2, and so on within each world).  Fortresses were identified from
the ROM map-clear tile value `0x67`; the World 2 pyramid uses `0x68`.  The World
1 fortress result matches the previously used `0x06 / 0x08` flag, which is a
useful sanity check for the row/column conversion, but it does not replace full
runtime validation for the later worlds.

## Current implementation scope

The implemented expansion adds AP locations and client-side SRAM flag detection
for:

- numbered levels in Worlds 2 through 8,
- fortress clears in Worlds 2 through 8,
- the World 2 pyramid.

The logic layer now also contains progression items for world unlocks and per-
world fortress/castle access.  Fortress clear checks require that world's
fortress access item, and castle checks require both that world's fortress and
castle access items.  Only World 1 currently has a castle-clear check; later
castle/airship/Bowser checks still need dedicated detection work.

The following remain future work because they need separate runtime research or
non-SRAM event detection:

- airship clears / world-transition checks for Worlds 2 through 7,
- World 8 tank, battleship, hand trap, and Bowser clear checks,
- runtime overworld-node gate coordinates beyond the existing World 1 Lua gate,
- persistent per-world clear-state restore when warping between worlds,
- level randomization, optional checks, entrance randomization, traps, and
  configurable goals.
