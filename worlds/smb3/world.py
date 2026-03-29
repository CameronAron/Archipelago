from collections.abc import Mapping
from typing import Any

from worlds.AutoWorld import World

from . import items, locations, regions, rules, web
from .options import SMB3Options

from BaseClasses import ItemClassification


class SMB3World(World):
    """
    Archipelago integration for Super Mario Bros. 3.
    This initial implementation is a minimal World 1 vertical slice.
    """

    game = "Super Mario Bros. 3"
    web = web.SMB3WebWorld()

    options_dataclass = SMB3Options
    options: SMB3Options

    item_name_to_id = items.ITEM_NAME_TO_ID
    location_name_to_id = locations.LOCATION_NAME_TO_ID

    origin_region_name = "Overworld"

    def create_regions(self) -> None:
        regions.create_regions(self)
        locations.create_locations(self)

    def create_event(self, name: str) -> items.SMB3Item:
        return items.SMB3Item(
            name,
            ItemClassification.progression,
            items.ITEM_NAME_TO_ID[name],
            self.player,
        )

    def set_rules(self) -> None:
        rules.set_rules(self)

    def create_items(self) -> None:
        items.create_items(self)

    def create_item(self, name: str) -> items.SMB3Item:
        return items.create_item(self, name)

    def get_filler_item_name(self) -> str:
        return items.get_filler_item_name(self)

    def fill_slot_data(self) -> Mapping[str, Any]:
        return {}