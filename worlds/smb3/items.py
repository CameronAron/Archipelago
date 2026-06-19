from __future__ import annotations
from typing import TYPE_CHECKING
from BaseClasses import Item, ItemClassification
from .constants import (CASTLE_ACCESS_ITEM_NAMES, FORTRESS_ACCESS_ITEM_NAMES,
                        ITEM_CODE_TO_NAME, WORLD_UNLOCK_ITEM_NAMES)
from .locations import SHUFFLED_LOCATION_NAMES
if TYPE_CHECKING:
    from .world import SMB3World

ITEM_NAME_TO_ID: dict[str, int] = {n: c for c, n in ITEM_CODE_TO_NAME.items()}

PROGRESSION_ITEMS: frozenset[str] = frozenset({
    "P-Meter Unlock", "Beat World 2 Castle",
    *WORLD_UNLOCK_ITEM_NAMES, *FORTRESS_ACCESS_ITEM_NAMES, *CASTLE_ACCESS_ITEM_NAMES,
})

FILLER_ITEMS = ["Mushroom","Fire Flower","Leaf","Frog Suit",
                "Tanooki Suit","Hammer Suit","Star","1-Up","3-Up"]

class SMB3Item(Item):
    game = "Super Mario Bros. 3"

def create_item(world: "SMB3World", name: str) -> SMB3Item:
    cls = ItemClassification.progression if name in PROGRESSION_ITEMS else ItemClassification.filler
    return SMB3Item(name, cls, ITEM_NAME_TO_ID[name], world.player)

def get_filler_item_name(world: "SMB3World") -> str:
    return world.random.choice(FILLER_ITEMS)

def create_items(world: "SMB3World") -> None:
    prog = [
        "P-Meter Unlock",
        *FORTRESS_ACCESS_ITEM_NAMES,   # 8 fortress access items
        *CASTLE_ACCESS_ITEM_NAMES,     # 8 castle access items (all back in pool)
        *(n for i, n in enumerate(WORLD_UNLOCK_ITEM_NAMES) if i != world.starting_world),
    ]
    pool = [create_item(world, n) for n in prog]
    remaining = len(SHUFFLED_LOCATION_NAMES) - len(pool)
    if remaining < 0:
        raise ValueError(f"SMB3: pool ({len(pool)}) > shuffled locs ({len(SHUFFLED_LOCATION_NAMES)})")
    for _ in range(remaining):
        pool.append(create_item(world, get_filler_item_name(world)))
    world.multiworld.itempool += pool
