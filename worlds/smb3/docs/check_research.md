# SMB3 Archipelago — Flag Research

## Source
Flags derived from SMB3 disassembly:
  byte_offset = W<N>_ByScrCol[tile_index]
  mask        = ROW_TO_MASK[ByRowType & 0xF0]
  where ROW_TO_MASK = {0x20:0x80, 0x30:0x40, 0x40:0x20, 0x50:0x10,
                       0x60:0x08, 0x70:0x04, 0x80:0x02, other:0x01}

World 1 values confirmed against original implementation.
Worlds 2-8 derived from disassembly — validate in BizHawk by clearing
each level and watching $7D00-$7D3F while CURRENT_WORLD_ADDR matches.

## World 1 (confirmed)
| Location | Offset | Mask |
|---|---|---|
| 1-1 | 0x04 | 0x80 |
| 1-2 | 0x08 | 0x80 |
| 1-3 | 0x0A | 0x80 |
| 1-4 | 0x0A | 0x20 |
| Fortress | 0x06 | 0x08 |
| 1-5 | 0x04 | 0x01 |
| 1-6 | 0x08 | 0x01 |

## Castle detection
World 1 Castle Clear: CURRENT_WORLD_ADDR 0→1 (counter transition)
World 2 Castle Clear: CURRENT_WORLD_ADDR 1→2 (goal)

## Still needed
- Post-fortress level identification for Worlds 2-8
- Toad House / N-Spade / Spade panel flags
- Worlds 3-8 castle detection methods
