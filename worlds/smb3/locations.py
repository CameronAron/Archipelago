from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Location

if TYPE_CHECKING:
    from .world import SMB3World


LOCATION_NAME_TO_ID = {
    "World 1-1 Clear": 2000,
    "World 1-2 Clear": 2001,
    "World 1-3 Clear": 2002,
    "World 1-4 Clear": 2003,
    "World 1-5 Clear": 2004,
    "World 1-6 Clear": 2005,
    "World 1 Fortress Clear": 2006,
    "World 1 Castle Clear": 2007,
}

SHUFFLED_LOCATION_NAMES = {
    "World 1-1 Clear",
    "World 1-2 Clear",
    "World 1-3 Clear",
    "World 1-4 Clear",
    "World 1-5 Clear",
    "World 1-6 Clear",
    "World 1 Fortress Clear",
}


class SMB3Location(Location):
    game = "Super Mario Bros. 3"


def create_locations(world: SMB3World) -> None:
    overworld = world.get_region("Overworld")
    overworld.add_locations(LOCATION_NAME_TO_ID, SMB3Location)

    castle = world.get_location("World 1 Castle Clear")
    castle.place_locked_item(world.create_event("Beat World 1 Castle"))