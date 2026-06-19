from collections.abc import Mapping
from typing import Any

from worlds.AutoWorld import World
from BaseClasses import ItemClassification

from . import items, locations, regions, rules, web
from .options import SMB3Options


class SMB3World(World):
    """
    Archipelago integration for Super Mario Bros. 3.

    Step 2 scope: all 8 worlds (71 shuffled checks + World 1 Castle goal).
    Starting world is always World 1 for now; Step 3 will randomise this.
    """

    game = "Super Mario Bros. 3"
    web  = web.SMB3WebWorld()

    options_dataclass = SMB3Options
    options: SMB3Options

    item_name_to_id     = items.ITEM_NAME_TO_ID
    location_name_to_id = locations.LOCATION_NAME_TO_ID

    origin_region_name = "Overworld"

    # ─── Generation lifecycle ─────────────────────────────────────────────────

    def generate_early(self) -> None:
        # Starting world is always 0 (World 1) in this slice.
        # Step 3 will turn this into a randomised slot option.
        self.starting_world: int = 0

    def create_regions(self) -> None:
        regions.create_regions(self)
        locations.create_locations(self)

    def set_rules(self) -> None:
        rules.set_rules(self)

    def create_items(self) -> None:
        items.create_items(self)

    # ─── Item factory helpers ─────────────────────────────────────────────────

    def create_item(self, name: str) -> items.SMB3Item:
        return items.create_item(self, name)

    def create_event(self, name: str) -> items.SMB3Item:
        return items.SMB3Item(
            name,
            ItemClassification.progression,
            items.ITEM_NAME_TO_ID[name],
            self.player,
        )

    def get_filler_item_name(self) -> str:
        return items.get_filler_item_name(self)

    # ─── Slot data ────────────────────────────────────────────────────────────

    def fill_slot_data(self) -> Mapping[str, Any]:
        return {
            "starting_world": self.starting_world,
        }
