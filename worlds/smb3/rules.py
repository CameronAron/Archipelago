from __future__ import annotations

from typing import TYPE_CHECKING

from worlds.generic.Rules import set_rule

if TYPE_CHECKING:
    from .world import SMB3World


def set_rules(world: SMB3World) -> None:
    fortress = world.get_location("World 1 Fortress Clear")
    level_1_5 = world.get_location("World 1-5 Clear")
    level_1_6 = world.get_location("World 1-6 Clear")
    castle = world.get_location("World 1 Castle Clear")

    set_rule(
        fortress,
        lambda state: state.has("World 1 Fortress Access", world.player),
    )

    set_rule(
        level_1_5,
        lambda state: state.has("World 1 Fortress Access", world.player),
    )

    set_rule(
        level_1_6,
        lambda state: state.has("World 1 Fortress Access", world.player),
    )

    set_rule(
        castle,
        lambda state: (
            state.has("World 1 Fortress Access", world.player)
            and state.has("World 1 Castle Access", world.player)
        ),
    )

    world.multiworld.completion_condition[world.player] = (
        lambda state: state.has("Beat World 1 Castle", world.player)
    )