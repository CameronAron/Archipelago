from .locations import LOCATION_NAME_TO_ID

GAME_NAME   = "Super Mario Bros. 3"
SYSTEM_NAME = "NES"

SYSTEM_BUS_DOMAIN = "System Bus"
RAM_DOMAIN        = "RAM"
ROM_DOMAIN        = "PRG ROM"

# Runtime RAM
CURRENT_WORLD_ADDR = 0x0727   # u8 — 0-based world index (0 = World 1)
LIVES_ADDR         = 0x0736
OVERWORLD_Y_ADDR   = 0x0075
OVERWORLD_X_ADDR   = 0x0079
P_METER_ADDR       = 0x03DD
INPUT_PRESSED_ADDR = 0x00F5
INPUT_HELD_ADDR    = 0x00F7
A_BUTTON_MASK      = 0x80

# Game SRAM
PROGRESS_FLAGS_ADDR = 0x7D00
PROGRESS_FLAGS_SIZE = 0x40    # 64 bytes covers all world flags

INVENTORY_ADDR = 0x7D80
INVENTORY_SIZE = 0x1C

# Archipelago SRAM Block ($7F00–$7F1F)
AP_SRAM_BASE           = 0x7F00
AP_SRAM_BLOCK_SIZE     = 0x20

AP_SENTINEL_ADDR       = AP_SRAM_BASE + 0x00
AP_SENTINEL_SIZE       = 4
AP_SENTINEL_VALUE      = bytes([0x41, 0x50, 0x33, 0x00])  # "AP3\0"

AP_RECEIVED_INDEX_ADDR = AP_SRAM_BASE + 0x04
AP_RECEIVED_INDEX_SIZE = 2

AP_STARTING_WORLD_ADDR = AP_SRAM_BASE + 0x06
AP_STARTING_WORLD_SIZE = 1

# World-1 Lua gate coordinates
FORTRESS_COORD_Y = 96
FORTRESS_COORD_X = 96
CASTLE_COORD_Y   = 128
CASTLE_COORD_X   = 192

# Overworld completion flags
PROGRESS_FLAGS_BY_WORLD: dict[int, dict[int, tuple[int, int]]] = {

    # World 1
    0: {
        LOCATION_NAME_TO_ID["World 1-1 Clear"]:        (0x04, 0x80),
        LOCATION_NAME_TO_ID["World 1-2 Clear"]:        (0x08, 0x80),
        LOCATION_NAME_TO_ID["World 1-3 Clear"]:        (0x0A, 0x80),
        LOCATION_NAME_TO_ID["World 1-4 Clear"]:        (0x0A, 0x20),
        LOCATION_NAME_TO_ID["World 1 Fortress Clear"]: (0x06, 0x08),
        LOCATION_NAME_TO_ID["World 1-5 Clear"]:        (0x04, 0x01),
        LOCATION_NAME_TO_ID["World 1-6 Clear"]:        (0x08, 0x01),
        # "World 1 Castle Clear" detected via counter 0→1
    },

    # World 2
    1: {
        LOCATION_NAME_TO_ID["World 2-2 Clear"]:         (0x08, 0x80),
        LOCATION_NAME_TO_ID["World 2-3 Clear"]:         (0x0C, 0x20),
        LOCATION_NAME_TO_ID["World 2-1 Clear"]:         (0x04, 0x08),
        LOCATION_NAME_TO_ID["World 2 Fortress Clear"]:  (0x08, 0x08),
        LOCATION_NAME_TO_ID["World 2-4 Clear"]:         (0x12, 0x80),
        LOCATION_NAME_TO_ID["World 2-5 Clear"]:         (0x10, 0x02),
        LOCATION_NAME_TO_ID["World 2 Pyramid Clear"]:   (0x14, 0x02),
        # "World 2 Castle Clear" detected via counter 1→2 (goal)
    },

    # World 3
    2: {
        LOCATION_NAME_TO_ID["World 3-3 Clear"]:              (0x08, 0x80),
        LOCATION_NAME_TO_ID["World 3-2 Clear"]:              (0x04, 0x20),
        LOCATION_NAME_TO_ID["World 3-4 Clear"]:              (0x0C, 0x20),
        LOCATION_NAME_TO_ID["World 3 Fortress 1 Clear"]:     (0x08, 0x08),
        LOCATION_NAME_TO_ID["World 3-1 Clear"]:              (0x04, 0x02),
        LOCATION_NAME_TO_ID["World 3-5 Clear"]:              (0x0C, 0x02),
        LOCATION_NAME_TO_ID["World 3-6 Clear"]:              (0x10, 0x80),
        LOCATION_NAME_TO_ID["World 3-7 Clear"]:              (0x14, 0x80),
        LOCATION_NAME_TO_ID["World 3-8 Clear"]:              (0x10, 0x20),
        LOCATION_NAME_TO_ID["World 3-9 Clear"]:              (0x12, 0x08),
        LOCATION_NAME_TO_ID["World 3 Fortress 2 Clear"]:     (0x14, 0x08),
    },

    # World 4
    3: {
        LOCATION_NAME_TO_ID["World 4-6 Clear"]:              (0x0C, 0x20),
        LOCATION_NAME_TO_ID["World 4 Fortress 2 Clear"]:     (0x0E, 0x08),
        LOCATION_NAME_TO_ID["World 4-5 Clear"]:              (0x0C, 0x02),
        LOCATION_NAME_TO_ID["World 4 Fortress 1 Clear"]:     (0x14, 0x20),
        LOCATION_NAME_TO_ID["World 4-3 Clear"]:              (0x18, 0x20),
        LOCATION_NAME_TO_ID["World 4-2 Clear"]:              (0x1C, 0x20),
        LOCATION_NAME_TO_ID["World 4-4 Clear"]:              (0x14, 0x02),
        LOCATION_NAME_TO_ID["World 4-1 Clear"]:              (0x1C, 0x02),
    },

    # World 5
    4: {
        LOCATION_NAME_TO_ID["World 5-2 Clear"]:              (0x04, 0x80),
        LOCATION_NAME_TO_ID["World 5-3 Clear"]:              (0x08, 0x80),
        LOCATION_NAME_TO_ID["World 5-1 Clear"]:              (0x02, 0x20),
        LOCATION_NAME_TO_ID["World 5 Fortress 1 Clear"]:     (0x04, 0x08),
        LOCATION_NAME_TO_ID["World 5 Fortress 2 Clear"]:     (0x18, 0x20),
        LOCATION_NAME_TO_ID["World 5-5 Clear"]:              (0x1E, 0x20),
        LOCATION_NAME_TO_ID["World 5-4 Clear"]:              (0x1A, 0x08),
        LOCATION_NAME_TO_ID["World 5-7 Clear"]:              (0x1C, 0x02),
        LOCATION_NAME_TO_ID["World 5-9 Clear"]:              (0x16, 0x01),
        LOCATION_NAME_TO_ID["World 5-8 Clear"]:              (0x18, 0x01),
        LOCATION_NAME_TO_ID["World 5-6 Clear"]:              (0x1E, 0x01),
    },

    # World 6
    5: {
        LOCATION_NAME_TO_ID["World 6-2 Clear"]:              (0x0A, 0x20),
        LOCATION_NAME_TO_ID["World 6-1 Clear"]:              (0x06, 0x08),
        LOCATION_NAME_TO_ID["World 6 Fortress 1 Clear"]:     (0x0A, 0x08),
        LOCATION_NAME_TO_ID["World 6-3 Clear"]:              (0x0C, 0x02),
        LOCATION_NAME_TO_ID["World 6-6 Clear"]:              (0x14, 0x08),
        LOCATION_NAME_TO_ID["World 6 Fortress 2 Clear"]:     (0x18, 0x08),
        LOCATION_NAME_TO_ID["World 6-8 Clear"]:              (0x1C, 0x08),
        LOCATION_NAME_TO_ID["World 6-4 Clear"]:              (0x10, 0x02),
        LOCATION_NAME_TO_ID["World 6-7 Clear"]:              (0x1C, 0x02),
        LOCATION_NAME_TO_ID["World 6-5 Clear"]:              (0x14, 0x01),
        LOCATION_NAME_TO_ID["World 6-9 Clear"]:              (0x20, 0x20),
        LOCATION_NAME_TO_ID["World 6 Fortress 3 Clear"]:     (0x22, 0x08),
        LOCATION_NAME_TO_ID["World 6-10 Clear"]:             (0x24, 0x02),
    },

    # World 7
    6: {
        LOCATION_NAME_TO_ID["World 7 Fortress 1 Clear"]:     (0x0F, 0x40),
        LOCATION_NAME_TO_ID["World 7-1 Clear"]:              (0x02, 0x10),
        LOCATION_NAME_TO_ID["World 7-4 Clear"]:              (0x0A, 0x04),
        LOCATION_NAME_TO_ID["World 7-2 Clear"]:              (0x03, 0x01),
        LOCATION_NAME_TO_ID["World 7-3 Clear"]:              (0x0E, 0x01),
        LOCATION_NAME_TO_ID["World 7-6 Clear"]:              (0x13, 0x40),
        LOCATION_NAME_TO_ID["World 7-7 Clear"]:              (0x16, 0x40),
        LOCATION_NAME_TO_ID["World 7-8 Clear"]:              (0x1A, 0x10),
        LOCATION_NAME_TO_ID["World 7-5 Clear"]:              (0x10, 0x04),
        LOCATION_NAME_TO_ID["World 7-9 Clear"]:              (0x18, 0x04),
        LOCATION_NAME_TO_ID["World 7 Fortress 2 Clear"]:     (0x1C, 0x04),
    },

    # World 8
    7: {
        LOCATION_NAME_TO_ID["World 8-1 Clear"]:        (0x24, 0x04),
        LOCATION_NAME_TO_ID["World 8 Fortress Clear"]: (0x28, 0x04),
        LOCATION_NAME_TO_ID["World 8-2 Clear"]:        (0x22, 0x01),
    },
}

# Backward-compatible alias
WORLD_1_PROGRESS_FLAGS = PROGRESS_FLAGS_BY_WORLD[0]

# Access item name groups
WORLD_UNLOCK_ITEM_NAMES    = tuple(f"World {w} Unlock"          for w in range(1, 9))
FORTRESS_ACCESS_ITEM_NAMES = tuple(f"World {w} Fortress Access" for w in range(1, 9))
CASTLE_ACCESS_ITEM_NAMES   = tuple(f"World {w} Castle Access"   for w in range(1, 9))

ACCESS_ITEM_NAMES = (
    "P-Meter Unlock",
    *WORLD_UNLOCK_ITEM_NAMES,
    *FORTRESS_ACCESS_ITEM_NAMES,
    *CASTLE_ACCESS_ITEM_NAMES,
)

# Item codes
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
    1012: "Beat World 2 Castle",   # goal event item
}

_next_id = 1013
for _name in (*WORLD_UNLOCK_ITEM_NAMES, *FORTRESS_ACCESS_ITEM_NAMES, *CASTLE_ACCESS_ITEM_NAMES):
    if _name not in ITEM_CODE_TO_NAME.values():
        ITEM_CODE_TO_NAME[_next_id] = _name
        _next_id += 1
del _name, _next_id

# Physical item tables
INVENTORY_ITEM_VALUES: dict[str, int] = {
    "Mushroom":     0x01,
    "Fire Flower":  0x02,
    "Leaf":         0x03,
    "Frog Suit":    0x04,
    "Tanooki Suit": 0x05,
    "Hammer Suit":  0x06,
    "Star":         0x09,
}

LIFE_ITEM_VALUES: dict[str, int] = {
    "1-Up": 1,
    "3-Up": 3,
}

# Castle location IDs used by the client
WORLD_1_CASTLE_LOCATION_ID = LOCATION_NAME_TO_ID["World 1 Castle Clear"]
WORLD_2_CASTLE_LOCATION_ID = LOCATION_NAME_TO_ID["World 2 Castle Clear"]
CASTLE_LOCATION_ID         = WORLD_2_CASTLE_LOCATION_ID   # current goal
