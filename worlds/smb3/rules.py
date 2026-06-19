from __future__ import annotations
from typing import TYPE_CHECKING
from worlds.generic.Rules import set_rule
if TYPE_CHECKING:
    from BaseClasses import CollectionState
    from .world import SMB3World

def _has_world_access(state, world, world_number: int) -> bool:
    return (world.starting_world == world_number - 1
            or state.has(f"World {world_number} Unlock", world.player))

def _world_number_from_location_name(name: str) -> int:
    return int(name.split()[1].split("-")[0])

def _level_rule(world, wn):
    return lambda state: _has_world_access(state, world, wn)

def _post_fortress_level_rule(world, wn):
    return lambda state: (_has_world_access(state, world, wn)
                          and state.has(f"World {wn} Fortress Access", world.player))

def _fortress_rule(world, wn):
    return lambda state: (_has_world_access(state, world, wn)
                          and state.has(f"World {wn} Fortress Access", world.player))

def _castle_rule(world, wn):
    return lambda state: (_has_world_access(state, world, wn)
                          and state.has(f"World {wn} Fortress Access", world.player)
                          and state.has(f"World {wn} Castle Access", world.player))

# Post-fortress numbered levels confirmed from World 1 map layout.
# Worlds 2-8 pending overworld map verification.
POST_FORTRESS_LEVELS: frozenset[str] = frozenset({"World 1-5 Clear","World 1-6 Clear"})

def set_rules(world: "SMB3World") -> None:
    for name in world.location_name_to_id:
        loc = world.get_location(name)
        wn  = _world_number_from_location_name(name)
        if " Castle " in name:
            set_rule(loc, _castle_rule(world, wn))
        elif " Fortress" in name:
            set_rule(loc, _fortress_rule(world, wn))
        elif " Pyramid" in name:
            set_rule(loc, _fortress_rule(world, wn))
        elif name in POST_FORTRESS_LEVELS:
            set_rule(loc, _post_fortress_level_rule(world, wn))
        else:
            set_rule(loc, _level_rule(world, wn))

    world.multiworld.completion_condition[world.player] = (
        lambda state: state.has("Beat World 2 Castle", world.player)
    )
