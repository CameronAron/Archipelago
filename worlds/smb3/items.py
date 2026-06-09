from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification

from .constants import (
    CASTLE_ACCESS_ITEM_NAMES,
    FORTRESS_ACCESS_ITEM_NAMES,
    ITEM_CODE_TO_NAME,
    WORLD_UNLOCK_ITEM_NAMES,
)
from .locations import SHUFFLED_LOCATION_NAMES

if TYPE_CHECKING:
    from .world import SMB3World


ITEM_NAME_TO_ID = {name: item_id for item_id, name in ITEM_CODE_TO_NAME.items()}

PROGRESSION_ITEMS = {
    "P-Meter Unlock",
    "Beat World 1 Castle",
    *WORLD_UNLOCK_ITEM_NAMES,
    *FORTRESS_ACCESS_ITEM_NAMES,
    *CASTLE_ACCESS_ITEM_NAMES,
}

FILLER_ITEMS = [
    "Mushroom",
    "Fire Flower",
    "Leaf",
    "Frog Suit",
    "Tanooki Suit",
    "Hammer Suit",
    "Star",
    "1-Up",
    "3-Up",
]


class SMB3Item(Item):
    game = "Super Mario Bros. 3"


def create_item(world: SMB3World, name: str) -> SMB3Item:
    if name in PROGRESSION_ITEMS:
        classification = ItemClassification.progression
    else:
        classification = ItemClassification.filler

    return SMB3Item(name, classification, ITEM_NAME_TO_ID[name], world.player)


def get_filler_item_name(world: SMB3World) -> str:
    return world.random.choice(FILLER_ITEMS)


def create_items(world: SMB3World) -> None:
    progression_item_names = [
        "P-Meter Unlock",
        *FORTRESS_ACCESS_ITEM_NAMES,
        *CASTLE_ACCESS_ITEM_NAMES,
    ]

    progression_item_names.extend(
        item_name
        for world_index, item_name in enumerate(WORLD_UNLOCK_ITEM_NAMES)
        if world_index != world.starting_world
    )

    itempool = [world.create_item(item_name) for item_name in progression_item_names]
    remaining_slots = len(SHUFFLED_LOCATION_NAMES) - len(itempool)

    for _ in range(remaining_slots):
        itempool.append(world.create_item(world.get_filler_item_name()))

    world.multiworld.itempool += itempool
