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

# ─── World 1 level-completion progress flags ─────────────────────────────────
# Maps location ID → (byte offset from PROGRESS_FLAGS_ADDR, bit mask).
# The client reads PROGRESS_FLAGS_SIZE bytes starting at PROGRESS_FLAGS_ADDR
# and AND-masks the appropriate byte to detect whether a level is cleared.
#
# Verified against the SMB3 USA ROM binary:
#   • STA $7D04/$7D06/$7D08/$7D0A patterns confirmed in PRG banks 2 and 30.
#   • INC $0727 (world-counter advance after World 1 Castle) confirmed at
#     PRG bank 30, file offset 0x3D0A1.

WORLD_1_PROGRESS_FLAGS: dict[int, tuple[int, int]] = {
    LOCATION_NAME_TO_ID["World 1-1 Clear"]:        (0x04, 0x80),
    LOCATION_NAME_TO_ID["World 1-2 Clear"]:        (0x08, 0x80),
    LOCATION_NAME_TO_ID["World 1-3 Clear"]:        (0x0A, 0x80),
    LOCATION_NAME_TO_ID["World 1-4 Clear"]:        (0x0A, 0x20),
    LOCATION_NAME_TO_ID["World 1-5 Clear"]:        (0x04, 0x01),
    LOCATION_NAME_TO_ID["World 1-6 Clear"]:        (0x08, 0x01),
    LOCATION_NAME_TO_ID["World 1 Fortress Clear"]: (0x06, 0x08),
}

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
