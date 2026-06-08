from collections.abc import Mapping
from typing import Any

from worlds.AutoWorld import World

from . import items, locations, regions, rules, web
from .options import SMB3Options

from BaseClasses import ItemClassification


class SMB3World(World):
    """
    Archipelago integration for Super Mario Bros. 3.

    Current scope: World 1 vertical slice (7 checks + goal).
    Step 1 adds the AP SRAM foundation and reconnect-safety.
    Full multi-world expansion follows in Step 2.
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
        """
        Per-slot pre-generation setup.

        Starting world is always World 1 (index 0) in this slice.
        In Step 2 this will become a randomised option drawn from whichever
        worlds are enabled, and the value will drive both the game's world
        counter initialisation and the initial map node setup.
        """
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
        """
        Data sent to the client on connect.  The client reads starting_world
        to initialise the AP SRAM block and (in Step 2) to set the in-game
        world counter when a new AP save is detected.
        """
        return {
            "starting_world": self.starting_world,
        }
