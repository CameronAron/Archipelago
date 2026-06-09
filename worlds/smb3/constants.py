from .locations import LOCATION_NAME_TO_ID

GAME_NAME = "Super Mario Bros. 3"
SYSTEM_NAME = "NES"

SYSTEM_BUS_DOMAIN = "System Bus"
RAM_DOMAIN = "RAM"
ROM_DOMAIN = "PRG ROM"

# ─── Runtime RAM (NES internal RAM, $0000–$07FF) ─────────────────────────────

CURRENT_WORLD_ADDR = 0x0727   # u8  — current world index, 0-based (0 = World 1)
LIVES_ADDR         = 0x0736   # u8  — lives counter
OVERWORLD_Y_ADDR   = 0x0075   # u8  — Mario's Y tile coordinate on the overworld map
OVERWORLD_X_ADDR   = 0x0079   # u8  — Mario's X tile coordinate on the overworld map
P_METER_ADDR       = 0x03DD   # u8  — P-Meter fill level (0x00 = empty, 0x08 = full)

# Input registers — read by the Lua connector's frame-start gate;
# reserved here for Step 3 (warp command) and future use.
INPUT_PRESSED_ADDR = 0x00F5   # u8  — buttons pressed this frame
INPUT_HELD_ADDR    = 0x00F7   # u8  — buttons currently held
A_BUTTON_MASK      = 0x80

# ─── Game SRAM (battery-backed PRG RAM via MMC3, $6000–$7FFF) ────────────────
# The game's own save data occupies $7D00–$7DFC at the highest end.

PROGRESS_FLAGS_ADDR = 0x7D00  # base of the 64-byte level-completion flag block
PROGRESS_FLAGS_SIZE = 0x40    # 64 bytes covers all World 1 flags (and room to grow)

INVENTORY_ADDR      = 0x7D80  # base of the 28-slot item inventory
INVENTORY_SIZE      = 0x1C    # 28 slots × 1 byte each

# ─── Archipelago SRAM Block ($7F00–$7F1F, 32 bytes) ──────────────────────────
#
# The game's own SRAM data tops out at around $7DFC.  The region $7E00–$7FFF
# is unused by the ROM and is safe for AP-exclusive use.  We reserve 32 bytes
# starting at $7F00 for Archipelago tracking data.
#
#  Offset  Size  Name                 Description
#  ──────  ────  ───────────────────  ────────────────────────────────────────
#  0x00    4     AP_SENTINEL          Magic bytes "AP3\x00" written on first
#                                     AP initialisation.  If absent the client
#                                     treats the save as fresh and writes the
#                                     whole block from scratch.
#  0x04    2     AP_RECEIVED_INDEX    Little-endian u16.  The number of items
#                                     in ctx.items_received that have already
#                                     been physically applied to game state
#                                     (inventory writes, life additions).
#                                     On reconnect, items below this index are
#                                     skipped for physical delivery but still
#                                     scanned to restore in-memory access flags.
#  0x06    1     AP_STARTING_WORLD    The AP-chosen starting world (0–7).
#                                     Always 0 in the World 1 slice; will be
#                                     randomised in the Step 2 multi-world
#                                     expansion and read here by the client.
#  0x07–0x1F     (reserved)          Available for future use (world unlocks,
#                                     entrance remap table pointer, etc.).
#
# NOTE: The Lua connector (connector_smb3.lua) does NOT read or write this
# block.  All AP SRAM management is handled entirely from the Python client
# via normal BizHawk WRITE requests.

AP_SRAM_BASE            = 0x7F00
AP_SRAM_BLOCK_SIZE      = 0x20   # 32 bytes total

AP_SENTINEL_ADDR        = AP_SRAM_BASE + 0x00
AP_SENTINEL_SIZE        = 4
AP_SENTINEL_VALUE       = bytes([0x41, 0x50, 0x33, 0x00])  # "AP3\0"

AP_RECEIVED_INDEX_ADDR  = AP_SRAM_BASE + 0x04
AP_RECEIVED_INDEX_SIZE  = 2   # little-endian u16

AP_STARTING_WORLD_ADDR  = AP_SRAM_BASE + 0x06
AP_STARTING_WORLD_SIZE  = 1

# ─── Overworld tile coordinates for locked map nodes ─────────────────────────
# Used by smb3_get_locked_node_name() in the Lua connector.

FORTRESS_COORD_Y = 96
FORTRESS_COORD_X = 96
CASTLE_COORD_Y   = 128
CASTLE_COORD_X   = 192

# ─── Overworld level-completion progress flags ────────────────────────────────
# Maps current_world (0-based) -> location ID -> (byte offset, bit mask) in the
# 64-byte PROGRESS_FLAGS_ADDR completion buffer.  Data Crystal documents this
# buffer as one byte per 16x16 map column across up to four horizontal screens;
# bits 7-1 cover rows 0-6 and bit 0 covers the bottom course row.
#
# The numbered-level coordinates below are candidate mappings extracted from
# the bundled SMB3 USA ROM overworld-map data at file offsets 0x185BA-0x19071.
# Fortress and pyramid coordinates use the ROM's map-clear tile positions (0x67
# for fortresses and 0x68 for the World 2 pyramid), matching the already-verified
# World 1 fortress flag at offset 0x06 / mask 0x08.  These later-world mappings
# still need emulator-side validation before they should be treated as final.

PROGRESS_FLAGS_BY_WORLD: dict[int, dict[int, tuple[int, int]]] = {
    0: {
        LOCATION_NAME_TO_ID["World 1-1 Clear"]: (0x04, 0x80),
        LOCATION_NAME_TO_ID["World 1-2 Clear"]: (0x08, 0x80),
        LOCATION_NAME_TO_ID["World 1-3 Clear"]: (0x0A, 0x80),
        LOCATION_NAME_TO_ID["World 1-4 Clear"]: (0x0A, 0x20),
        LOCATION_NAME_TO_ID["World 1-5 Clear"]: (0x04, 0x01),
        LOCATION_NAME_TO_ID["World 1-6 Clear"]: (0x08, 0x01),
        LOCATION_NAME_TO_ID["World 1 Fortress Clear"]: (0x06, 0x08),
    },
    1: {
        LOCATION_NAME_TO_ID["World 2-1 Clear"]: (0x04, 0x20),
        LOCATION_NAME_TO_ID["World 2-2 Clear"]: (0x08, 0x80),
        LOCATION_NAME_TO_ID["World 2-3 Clear"]: (0x0C, 0x40),
        LOCATION_NAME_TO_ID["World 2-4 Clear"]: (0x12, 0x08),
        LOCATION_NAME_TO_ID["World 2-5 Clear"]: (0x10, 0x01),
        LOCATION_NAME_TO_ID["World 2 Fortress Clear"]: (0x08, 0x20),
        LOCATION_NAME_TO_ID["World 2 Pyramid Clear"]: (0x10, 0x04),
    },
    2: {
        LOCATION_NAME_TO_ID["World 3-1 Clear"]: (0x04, 0x20),
        LOCATION_NAME_TO_ID["World 3-2 Clear"]: (0x24, 0x80),
        LOCATION_NAME_TO_ID["World 3-3 Clear"]: (0x08, 0x80),
        LOCATION_NAME_TO_ID["World 3-4 Clear"]: (0x2C, 0x80),
        LOCATION_NAME_TO_ID["World 3-5 Clear"]: (0x0C, 0x20),
        LOCATION_NAME_TO_ID["World 3-6 Clear"]: (0x00, 0x10),
        LOCATION_NAME_TO_ID["World 3-7 Clear"]: (0x04, 0x10),
        LOCATION_NAME_TO_ID["World 3-8 Clear"]: (0x20, 0x10),
        LOCATION_NAME_TO_ID["World 3-9 Clear"]: (0x12, 0x08),
        LOCATION_NAME_TO_ID["World 3 Fortress 1 Clear"]: (0x18, 0x40),
        LOCATION_NAME_TO_ID["World 3 Fortress 2 Clear"]: (0x26, 0x10),
    },
    3: {
        LOCATION_NAME_TO_ID["World 4-1 Clear"]: (0x1C, 0x01),
        LOCATION_NAME_TO_ID["World 4-2 Clear"]: (0x1C, 0x04),
        LOCATION_NAME_TO_ID["World 4-3 Clear"]: (0x18, 0x04),
        LOCATION_NAME_TO_ID["World 4-4 Clear"]: (0x14, 0x01),
        LOCATION_NAME_TO_ID["World 4-5 Clear"]: (0x0C, 0x10),
        LOCATION_NAME_TO_ID["World 4-6 Clear"]: (0x0C, 0x40),
        LOCATION_NAME_TO_ID["World 4 Fortress 1 Clear"]: (0x0E, 0x20),
        LOCATION_NAME_TO_ID["World 4 Fortress 2 Clear"]: (0x14, 0x04),
    },
    4: {
        LOCATION_NAME_TO_ID["World 5-1 Clear"]: (0x02, 0x40),
        LOCATION_NAME_TO_ID["World 5-2 Clear"]: (0x04, 0x80),
        LOCATION_NAME_TO_ID["World 5-3 Clear"]: (0x08, 0x80),
        LOCATION_NAME_TO_ID["World 5-4 Clear"]: (0x1A, 0x02),
        LOCATION_NAME_TO_ID["World 5-5 Clear"]: (0x1E, 0x04),
        LOCATION_NAME_TO_ID["World 5-6 Clear"]: (0x1E, 0x01),
        LOCATION_NAME_TO_ID["World 5-7 Clear"]: (0x1C, 0x01),
        LOCATION_NAME_TO_ID["World 5-8 Clear"]: (0x18, 0x01),
        LOCATION_NAME_TO_ID["World 5-9 Clear"]: (0x16, 0x01),
        LOCATION_NAME_TO_ID["World 5 Fortress 1 Clear"]: (0x04, 0x20),
        LOCATION_NAME_TO_ID["World 5 Fortress 2 Clear"]: (0x14, 0x01),
    },
    5: {
        LOCATION_NAME_TO_ID["World 6-1 Clear"]: (0x16, 0x40),
        LOCATION_NAME_TO_ID["World 6-2 Clear"]: (0x2A, 0x80),
        LOCATION_NAME_TO_ID["World 6-3 Clear"]: (0x0C, 0x20),
        LOCATION_NAME_TO_ID["World 6-4 Clear"]: (0x00, 0x04),
        LOCATION_NAME_TO_ID["World 6-5 Clear"]: (0x0C, 0x04),
        LOCATION_NAME_TO_ID["World 6-6 Clear"]: (0x24, 0x04),
        LOCATION_NAME_TO_ID["World 6-7 Clear"]: (0x14, 0x08),
        LOCATION_NAME_TO_ID["World 6-8 Clear"]: (0x20, 0x02),
        LOCATION_NAME_TO_ID["World 6-9 Clear"]: (0x1C, 0x08),
        LOCATION_NAME_TO_ID["World 6-10 Clear"]: (0x04, 0x01),
        LOCATION_NAME_TO_ID["World 6 Fortress 1 Clear"]: (0x1A, 0x40),
        LOCATION_NAME_TO_ID["World 6 Fortress 2 Clear"]: (0x18, 0x08),
        LOCATION_NAME_TO_ID["World 6 Fortress 3 Clear"]: (0x12, 0x01),
    },
    6: {
        LOCATION_NAME_TO_ID["World 7-1 Clear"]: (0x12, 0x40),
        LOCATION_NAME_TO_ID["World 7-2 Clear"]: (0x13, 0x10),
        LOCATION_NAME_TO_ID["World 7-3 Clear"]: (0x1E, 0x10),
        LOCATION_NAME_TO_ID["World 7-4 Clear"]: (0x1A, 0x20),
        LOCATION_NAME_TO_ID["World 7-5 Clear"]: (0x00, 0x01),
        LOCATION_NAME_TO_ID["World 7-6 Clear"]: (0x03, 0x04),
        LOCATION_NAME_TO_ID["World 7-7 Clear"]: (0x06, 0x04),
        LOCATION_NAME_TO_ID["World 7-8 Clear"]: (0x0A, 0x02),
        LOCATION_NAME_TO_ID["World 7-9 Clear"]: (0x08, 0x01),
        LOCATION_NAME_TO_ID["World 7 Fortress 1 Clear"]: (0x1F, 0x80),
        LOCATION_NAME_TO_ID["World 7 Fortress 2 Clear"]: (0x0C, 0x01),
    },
    7: {
        LOCATION_NAME_TO_ID["World 8-1 Clear"]: (0x34, 0x04),
        LOCATION_NAME_TO_ID["World 8-2 Clear"]: (0x12, 0x02),
        LOCATION_NAME_TO_ID["World 8 Fortress Clear"]: (0x38, 0x04),
    },
}

# Backward-compatible alias for tests and any third-party tooling that imported
# the original World 1-only table.
WORLD_1_PROGRESS_FLAGS = PROGRESS_FLAGS_BY_WORLD[0]


# ─── Progression/access item name groups ──────────────────────────────────────

WORLD_UNLOCK_ITEM_NAMES = tuple(f"World {world} Unlock" for world in range(1, 9))
FORTRESS_ACCESS_ITEM_NAMES = tuple(f"World {world} Fortress Access" for world in range(1, 9))
CASTLE_ACCESS_ITEM_NAMES = tuple(f"World {world} Castle Access" for world in range(1, 9))
ACCESS_ITEM_NAMES = (
    "P-Meter Unlock",
    *WORLD_UNLOCK_ITEM_NAMES,
    *FORTRESS_ACCESS_ITEM_NAMES,
    *CASTLE_ACCESS_ITEM_NAMES,
)

# ─── Item lookup tables ───────────────────────────────────────────────────────

ITEM_CODE_TO_NAME: dict[int, str] = {
    1000: "P-Meter Unlock",
    1001: "World 1 Fortress Access",
    1002: "World 1 Castle Access",
    1003: "Mushroom",
    1004: "Fire Flower",
    1005: "Leaf",
    1006: "Frog Suit",
    1007: "Tanooki Suit",
    1008: "Hammer Suit",
    1009: "Star",
    1010: "1-Up",
    1011: "3-Up",
    1012: "Beat World 1 Castle",
}

_next_item_id = 1013
for _access_item_name in (
    *WORLD_UNLOCK_ITEM_NAMES,
    *FORTRESS_ACCESS_ITEM_NAMES,
    *CASTLE_ACCESS_ITEM_NAMES,
):
    if _access_item_name not in ITEM_CODE_TO_NAME.values():
        ITEM_CODE_TO_NAME[_next_item_id] = _access_item_name
        _next_item_id += 1

del _access_item_name, _next_item_id

# Item name → byte value written into the game's 28-slot SRAM inventory.
# Values confirmed against the SMB3 USA ROM item-render loop in PRG bank 26.
INVENTORY_ITEM_VALUES: dict[str, int] = {
    "Mushroom":     0x01,
    "Fire Flower":  0x02,
    "Leaf":         0x03,
    "Frog Suit":    0x04,
    "Tanooki Suit": 0x05,
    "Hammer Suit":  0x06,
    "Star":         0x09,
    # 0x0C (Warp Whistle) is intentionally excluded; the client sanitises it
    # out of the inventory via a guarded write whenever it appears.
}

# Item name → number of lives added to LIVES_ADDR.
LIFE_ITEM_VALUES: dict[str, int] = {
    "1-Up": 1,
    "3-Up": 3,
}

CASTLE_LOCATION_ID = LOCATION_NAME_TO_ID["World 1 Castle Clear"]
