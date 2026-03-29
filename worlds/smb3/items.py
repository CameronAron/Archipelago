from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification
from .locations import SHUFFLED_LOCATION_NAMES

if TYPE_CHECKING:
    from .world import SMB3World


ITEM_NAME_TO_ID = {
    "P-Meter Unlock": 1000,
    "World 1 Fortress Access": 1001,
    "World 1 Castle Access": 1002,
    "Mushroom": 1003,
    "Fire Flower": 1004,
    "Leaf": 1005,
    "Frog Suit": 1006,
    "Tanooki Suit": 1007,
    "Hammer Suit": 1008,
    "Star": 1009,
    "1-Up": 1010,
    "3-Up": 1011,
    "Beat World 1 Castle": 1012,
}

PROGRESSION_ITEMS = {
    "P-Meter Unlock",
    "World 1 Fortress Access",
    "World 1 Castle Access",
    "Beat World 1 Castle",
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
    itempool: list[SMB3Item] = [
        world.create_item("P-Meter Unlock"),
        world.create_item("World 1 Fortress Access"),
        world.create_item("World 1 Castle Access"),
    ]

    remaining_slots = len(SHUFFLED_LOCATION_NAMES) - len(itempool)

    for _ in range(remaining_slots):
        itempool.append(world.create_item(world.get_filler_item_name()))

    world.multiworld.itempool += itempool