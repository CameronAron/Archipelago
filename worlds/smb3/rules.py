from __future__ import annotations

from typing import TYPE_CHECKING

from worlds.generic.Rules import set_rule

if TYPE_CHECKING:
    from BaseClasses import CollectionState

    from .world import SMB3World


def _has_world_access(state: CollectionState, world: SMB3World, world_number: int) -> bool:
    """Return whether AP logic allows the player to enter the given world."""
    return world.starting_world == world_number - 1 or state.has(
        f"World {world_number} Unlock",
        world.player,
    )


POST_FORTRESS_LEVELS = {
    "World 1-5 Clear",
    "World 1-6 Clear",
}


def _make_level_rule(world: SMB3World, world_number: int):
    return lambda state: _has_world_access(state, world, world_number)


def _make_post_fortress_level_rule(world: SMB3World, world_number: int):
    return lambda state: (
        _has_world_access(state, world, world_number)
        and state.has(f"World {world_number} Fortress Access", world.player)
    )


def _make_fortress_rule(world: SMB3World, world_number: int):
    return lambda state: (
        _has_world_access(state, world, world_number)
        and state.has(f"World {world_number} Fortress Access", world.player)
    )


def _make_castle_rule(world: SMB3World, world_number: int):
    return lambda state: (
        _has_world_access(state, world, world_number)
        and state.has(f"World {world_number} Fortress Access", world.player)
        and state.has(f"World {world_number} Castle Access", world.player)
    )


def _world_number_from_location_name(location_name: str) -> int:
    return int(location_name.split(maxsplit=2)[1].split("-", maxsplit=1)[0])


def set_rules(world: SMB3World) -> None:
    for location_name in world.location_name_to_id:
        location = world.get_location(location_name)
        world_number = _world_number_from_location_name(location_name)

        if " Castle " in location_name:
            set_rule(location, _make_castle_rule(world, world_number))
        elif " Fortress" in location_name:
            set_rule(location, _make_fortress_rule(world, world_number))
        elif location_name in POST_FORTRESS_LEVELS:
            set_rule(location, _make_post_fortress_level_rule(world, world_number))
        else:
            set_rule(location, _make_level_rule(world, world_number))

    world.multiworld.completion_condition[world.player] = (
        lambda state: state.has("Beat World 1 Castle", world.player)
    )
