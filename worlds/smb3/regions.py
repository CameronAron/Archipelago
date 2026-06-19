from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Region

if TYPE_CHECKING:
    from .world import SMB3World


def create_regions(world: SMB3World) -> None:
    overworld = Region("Overworld", world.player, world.multiworld)
    world.multiworld.regions.append(overworld)