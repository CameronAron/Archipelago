from __future__ import annotations
from typing import TYPE_CHECKING
from BaseClasses import Location
if TYPE_CHECKING:
    from .world import SMB3World

LOCATION_NAME_TO_ID: dict[str, int] = {
    "World 1-1 Clear":2000,"World 1-2 Clear":2001,"World 1-3 Clear":2002,
    "World 1-4 Clear":2003,"World 1-5 Clear":2004,"World 1-6 Clear":2005,
    "World 1 Fortress Clear":2006,"World 1 Castle Clear":2007,
    "World 2-1 Clear":2008,"World 2-2 Clear":2009,"World 2-3 Clear":2010,
    "World 2-4 Clear":2011,"World 2-5 Clear":2012,
    "World 2 Fortress Clear":2013,"World 2 Pyramid Clear":2014,
    "World 2 Castle Clear":2072,
    "World 3-1 Clear":2015,"World 3-2 Clear":2016,"World 3-3 Clear":2017,
    "World 3-4 Clear":2018,"World 3-5 Clear":2019,"World 3-6 Clear":2020,
    "World 3-7 Clear":2021,"World 3-8 Clear":2022,"World 3-9 Clear":2023,
    "World 3 Fortress 1 Clear":2024,"World 3 Fortress 2 Clear":2025,
    "World 4-1 Clear":2026,"World 4-2 Clear":2027,"World 4-3 Clear":2028,
    "World 4-4 Clear":2029,"World 4-5 Clear":2030,"World 4-6 Clear":2031,
    "World 4 Fortress 1 Clear":2032,"World 4 Fortress 2 Clear":2033,
    "World 5-1 Clear":2034,"World 5-2 Clear":2035,"World 5-3 Clear":2036,
    "World 5-4 Clear":2037,"World 5-5 Clear":2038,"World 5-6 Clear":2039,
    "World 5-7 Clear":2040,"World 5-8 Clear":2041,"World 5-9 Clear":2042,
    "World 5 Fortress 1 Clear":2043,"World 5 Fortress 2 Clear":2044,
    "World 6-1 Clear":2045,"World 6-2 Clear":2046,"World 6-3 Clear":2047,
    "World 6-4 Clear":2048,"World 6-5 Clear":2049,"World 6-6 Clear":2050,
    "World 6-7 Clear":2051,"World 6-8 Clear":2052,"World 6-9 Clear":2053,
    "World 6-10 Clear":2054,"World 6 Fortress 1 Clear":2055,
    "World 6 Fortress 2 Clear":2056,"World 6 Fortress 3 Clear":2057,
    "World 7-1 Clear":2058,"World 7-2 Clear":2059,"World 7-3 Clear":2060,
    "World 7-4 Clear":2061,"World 7-5 Clear":2062,"World 7-6 Clear":2063,
    "World 7-7 Clear":2064,"World 7-8 Clear":2065,"World 7-9 Clear":2066,
    "World 7 Fortress 1 Clear":2067,"World 7 Fortress 2 Clear":2068,
    "World 8-1 Clear":2069,"World 8-2 Clear":2070,"World 8 Fortress Clear":2071,
}
# World 2 Castle Clear (2072) is locked — holds the goal event, not shuffled
SHUFFLED_LOCATION_NAMES: frozenset[str] = frozenset(
    n for n in LOCATION_NAME_TO_ID if n != "World 2 Castle Clear"
)
class SMB3Location(Location):
    game = "Super Mario Bros. 3"
def create_locations(world: "SMB3World") -> None:
    world.get_region("Overworld").add_locations(LOCATION_NAME_TO_ID, SMB3Location)
    world.get_location("World 2 Castle Clear").place_locked_item(
        world.create_event("Beat World 2 Castle"))
