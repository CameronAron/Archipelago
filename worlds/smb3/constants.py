from .locations import LOCATION_NAME_TO_ID

GAME_NAME = "Super Mario Bros. 3"
SYSTEM_NAME = "NES"

SYSTEM_BUS_DOMAIN = "System Bus"
RAM_DOMAIN = "RAM"
ROM_DOMAIN = "PRG ROM"

CURRENT_WORLD_ADDR = 0x0727
LIVES_ADDR = 0x0736
OVERWORLD_Y_ADDR = 0x0075
OVERWORLD_X_ADDR = 0x0079
INPUT_HELD_ADDR = 0x00F7
P_METER_ADDR = 0x03DD

PROGRESS_FLAGS_ADDR = 0x7D00
PROGRESS_FLAGS_SIZE = 0x40

INVENTORY_ADDR = 0x7D80
INVENTORY_SIZE = 0x1C

FORTRESS_COORD_Y = 96
FORTRESS_COORD_X = 96
CASTLE_COORD_Y = 128
CASTLE_COORD_X = 192

WORLD_1_PROGRESS_FLAGS = {
    LOCATION_NAME_TO_ID["World 1-1 Clear"]: (0x04, 0x80),
    LOCATION_NAME_TO_ID["World 1-2 Clear"]: (0x08, 0x80),
    LOCATION_NAME_TO_ID["World 1-3 Clear"]: (0x0A, 0x80),
    LOCATION_NAME_TO_ID["World 1-4 Clear"]: (0x0A, 0x20),
    LOCATION_NAME_TO_ID["World 1-5 Clear"]: (0x04, 0x01),
    LOCATION_NAME_TO_ID["World 1-6 Clear"]: (0x08, 0x01),
    LOCATION_NAME_TO_ID["World 1 Fortress Clear"]: (0x06, 0x08),
}

ITEM_CODE_TO_NAME = {
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

INVENTORY_ITEM_VALUES = {
    "Mushroom": 0x01,
    "Fire Flower": 0x02,
    "Leaf": 0x03,
    "Frog Suit": 0x04,
    "Tanooki Suit": 0x05,
    "Hammer Suit": 0x06,
    "Star": 0x09,
}

LIFE_ITEM_VALUES = {
    "1-Up": 1,
    "3-Up": 3,
}

CASTLE_LOCATION_ID = LOCATION_NAME_TO_ID["World 1 Castle Clear"]