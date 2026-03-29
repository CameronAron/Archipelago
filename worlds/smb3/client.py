from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from NetUtils import ClientStatus

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

from .constants import (
    GAME_NAME,
    SYSTEM_NAME,
    SYSTEM_BUS_DOMAIN,
    ROM_DOMAIN,
    CURRENT_WORLD_ADDR,
    LIVES_ADDR,
    OVERWORLD_Y_ADDR,
    OVERWORLD_X_ADDR,
    INPUT_PRESSED_ADDR,
    INPUT_HELD_ADDR,
    P_METER_ADDR,
    PROGRESS_FLAGS_ADDR,
    PROGRESS_FLAGS_SIZE,
    INVENTORY_ADDR,
    INVENTORY_SIZE,
    WORLD_1_PROGRESS_FLAGS,
    CASTLE_LOCATION_ID,
    ITEM_CODE_TO_NAME,
    INVENTORY_ITEM_VALUES,
    LIFE_ITEM_VALUES,
)

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext


logger = logging.getLogger("Client")


class SMB3BizHawkClient(BizHawkClient):
    game = GAME_NAME
    system = SYSTEM_NAME
    patch_suffix = None

    def __init__(self) -> None:
        self.previous_world: int | None = None
        self.logged_hash = False
        self.warned_not_connected = False

        self.received_index = 0
        self.pending_inventory_items: list[str] = []
        self.has_p_meter_unlock = False
        self.has_fortress_access = False
        self.has_castle_access = False

        self.last_sent_lua_state: tuple[bool, bool, bool] | None = None

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        try:
            system_bus_size = await bizhawk.get_memory_size(ctx.bizhawk_ctx, SYSTEM_BUS_DOMAIN)
            rom_size = await bizhawk.get_memory_size(ctx.bizhawk_ctx, ROM_DOMAIN)
        except bizhawk.RequestFailedError:
            return False

        if system_bus_size <= (INVENTORY_ADDR + INVENTORY_SIZE):
            return False

        if rom_size <= 0:
            return False

        try:
            rom_hash = await bizhawk.get_hash(ctx.bizhawk_ctx)
            if not self.logged_hash:
                #logger.info(f"SMB3 development ROM hash: {rom_hash}")
                self.logged_hash = True
        except bizhawk.RequestFailedError:
            pass

        ctx.game = self.game
        ctx.items_handling = 0b111
        ctx.want_slot_data = True
        ctx.watcher_timeout = 0.125

        self.received_index = 0
        self.pending_inventory_items = []
        self.has_p_meter_unlock = False
        self.has_fortress_access = False
        self.has_castle_access = False
        self.last_sent_lua_state = None

        self.previous_world = None
        return True

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        if ctx.server is None:
            if not self.warned_not_connected:
                logger.warning("SMB3: Not connected to an Archipelago server. Checks will not send.")
                self.warned_not_connected = True
            return

        if ctx.slot is None:
            return

        try:
            reads = await bizhawk.read(
                ctx.bizhawk_ctx,
                [
                    (CURRENT_WORLD_ADDR, 1, SYSTEM_BUS_DOMAIN),
                    (LIVES_ADDR, 1, SYSTEM_BUS_DOMAIN),
                    (OVERWORLD_Y_ADDR, 1, SYSTEM_BUS_DOMAIN),
                    (OVERWORLD_X_ADDR, 1, SYSTEM_BUS_DOMAIN),
                    (INPUT_PRESSED_ADDR, 1, SYSTEM_BUS_DOMAIN),
                    (INPUT_HELD_ADDR, 1, SYSTEM_BUS_DOMAIN),
                    (P_METER_ADDR, 1, SYSTEM_BUS_DOMAIN),
                    (PROGRESS_FLAGS_ADDR, PROGRESS_FLAGS_SIZE, SYSTEM_BUS_DOMAIN),
                    (INVENTORY_ADDR, INVENTORY_SIZE, SYSTEM_BUS_DOMAIN),
                ],
            )
        except bizhawk.RequestFailedError:
            logger.warning("SMB3 BizHawk read failed.")
            return

        current_world = reads[0][0]
        lives = reads[1][0]
        overworld_y = reads[2][0]
        overworld_x = reads[3][0]
        input_pressed = reads[4][0]
        input_held = reads[5][0]
        p_meter = reads[6][0]
        progress_flags = reads[7]
        inventory = reads[8]

        await self.process_received_items(ctx, lives, inventory)
        inventory = await self.sanitize_inventory(ctx, inventory)
        inventory = await self.process_pending_inventory(ctx, inventory)
        await self.push_lua_state(ctx)
        await self.enforce_p_meter_lock(ctx, p_meter)
        await self.check_world_1_locations(ctx, progress_flags)
        await self.check_goal(ctx, current_world)

        self.previous_world = current_world

    async def push_lua_state(self, ctx: "BizHawkClientContext") -> None:
        state_tuple = (
            self.has_fortress_access,
            self.has_castle_access,
            self.has_p_meter_unlock,
        )

        if self.last_sent_lua_state == state_tuple:
            return

        #logger.info(
        #    "SMB3: Pushing Lua state - "
        #    f"fortress={self.has_fortress_access}, "
        #    f"castle={self.has_castle_access}, "
        #    f"p_meter={self.has_p_meter_unlock}"
        #)

        try:
            await bizhawk.send_requests(
                ctx.bizhawk_ctx,
                [
                    {
                        "type": "SMB3_SET_STATE",
                        "fortress_access": self.has_fortress_access,
                        "castle_access": self.has_castle_access,
                        "p_meter_unlock": self.has_p_meter_unlock,
                        "enabled": True,
                    }
                ],
            )
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: Failed to push Lua state")
            return

        self.last_sent_lua_state = state_tuple

    async def check_world_1_locations(self, ctx: "BizHawkClientContext", progress_flags: bytes) -> None:
        locations_to_send: list[int] = []

        for location_id, (offset, mask) in WORLD_1_PROGRESS_FLAGS.items():
            if location_id not in ctx.missing_locations:
                continue

            if progress_flags[offset] & mask:
                locations_to_send.append(location_id)

        if not locations_to_send:
            return

        await ctx.send_msgs(
            [
                {
                    "cmd": "LocationChecks",
                    "locations": locations_to_send,
                }
            ]
        )

    async def check_goal(self, ctx: "BizHawkClientContext", current_world: int) -> None:
        if ctx.finished_game:
            return

        if self.previous_world is None:
            return

        if not (self.previous_world == 0 and current_world == 1):
            return

        messages = []

        if CASTLE_LOCATION_ID in ctx.missing_locations:
            messages.append(
                {
                    "cmd": "LocationChecks",
                    "locations": [CASTLE_LOCATION_ID],
                }
            )

        messages.append(
            {
                "cmd": "StatusUpdate",
                "status": ClientStatus.CLIENT_GOAL,
            }
        )

        await ctx.send_msgs(messages)
        ctx.finished_game = True
        logger.info("World 1 Castle cleared. Goal sent.")

    async def process_received_items(
        self,
        ctx: "BizHawkClientContext",
        lives: int,
        inventory: bytes,
    ) -> None:
        while self.received_index < len(ctx.items_received):
            network_item = ctx.items_received[self.received_index]
            item_name = ITEM_CODE_TO_NAME.get(network_item.item)

            if item_name is None:
                logger.warning(f"SMB3: Unknown item code received: {network_item.item}")
                self.received_index += 1
                continue

            #logger.info(f"SMB3: Applying item: {item_name}")
            await self.show_item_popup(ctx, item_name)

            if item_name == "P-Meter Unlock":
                self.has_p_meter_unlock = True

            elif item_name == "World 1 Fortress Access":
                self.has_fortress_access = True

            elif item_name == "World 1 Castle Access":
                self.has_castle_access = True

            elif item_name in INVENTORY_ITEM_VALUES:
                inventory = await self.give_inventory_item(ctx, inventory, item_name)

            elif item_name in LIFE_ITEM_VALUES:
                lives = await self.give_lives(ctx, lives, LIFE_ITEM_VALUES[item_name])

            elif item_name == "Beat World 1 Castle":
                # This is the locked goal item from the castle location.
                # It should not change game state.
                pass

            else:
                logger.warning(f"SMB3: No handler for item: {item_name}")

            self.received_index += 1

    async def give_inventory_item(
        self,
        ctx: "BizHawkClientContext",
        inventory: bytes,
        item_name: str,
    ) -> bytes:
        item_value = INVENTORY_ITEM_VALUES[item_name]

        inventory_list = list(inventory)

        for i, slot_value in enumerate(inventory_list):
            if slot_value == 0x00:
                write_address = INVENTORY_ADDR + i

                try:
                    await bizhawk.write(
                        ctx.bizhawk_ctx,
                        [
                            (write_address, bytes([item_value]), SYSTEM_BUS_DOMAIN),
                        ],
                    )
                except bizhawk.RequestFailedError:
                    logger.warning(f"SMB3: Failed to write inventory item {item_name}")
                    return inventory

                inventory_list[i] = item_value
                #logger.info(f"SMB3: Inserted {item_name} into inventory slot {i}")
                return bytes(inventory_list)

        self.pending_inventory_items.append(item_name)
        logger.info(f"SMB3: Inventory full, queued {item_name}")
        return inventory

    async def give_lives(
        self,
        ctx: "BizHawkClientContext",
        current_lives: int,
        amount: int,
    ) -> int:
        new_lives = min(current_lives + amount, 99)

        try:
            await bizhawk.write(
                ctx.bizhawk_ctx,
                [
                    (LIVES_ADDR, bytes([new_lives]), SYSTEM_BUS_DOMAIN),
                ],
            )
        except bizhawk.RequestFailedError:
            logger.warning(f"SMB3: Failed to write lives (+{amount})")
            return current_lives

        #logger.info(f"SMB3: Added {amount} life/lives. {current_lives} -> {new_lives}")
        return new_lives

    async def enforce_p_meter_lock(
        self,
        ctx: "BizHawkClientContext",
        current_p_meter: int,
    ) -> None:
        if self.has_p_meter_unlock:
            return

        if current_p_meter == 0:
            return

        try:
            await bizhawk.write(
                ctx.bizhawk_ctx,
                [
                    (P_METER_ADDR, bytes([0x00]), SYSTEM_BUS_DOMAIN),
                ],
            )
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: Failed to enforce P-Meter lock")

    async def process_pending_inventory(
        self,
        ctx: "BizHawkClientContext",
        inventory: bytes,
    ) -> bytes:
        if not self.pending_inventory_items:
            return inventory

        next_item = self.pending_inventory_items[0]
        new_inventory = await self.give_inventory_item(ctx, inventory, next_item)

        if new_inventory != inventory:
            self.pending_inventory_items.pop(0)
            return new_inventory

        return inventory

    async def sanitize_inventory(
        self,
        ctx: "BizHawkClientContext",
        inventory: bytes,
    ) -> bytes:
        write_list = []
        guard_list = []
        inventory_list = list(inventory)

        for i, slot_value in enumerate(inventory_list):
            if slot_value == 0x0C:
                address = INVENTORY_ADDR + i

                write_list.append((address, bytes([0x00]), SYSTEM_BUS_DOMAIN))
                guard_list.append((address, bytes([0x0C]), SYSTEM_BUS_DOMAIN))

                inventory_list[i] = 0x00

        if not write_list:
            return inventory

        try:
            write_result = await bizhawk.guarded_write(
                ctx.bizhawk_ctx,
                write_list,
                guard_list,
            )
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: Failed to sanitize whistle from inventory")
            return inventory

        if write_result:
            #logger.info("SMB3: Removed unsupported whistle(s) from inventory")
            return bytes(inventory_list)

        return inventory
    
    async def show_item_popup(self, ctx: "BizHawkClientContext", item_name: str) -> None:
        try:
            await bizhawk.display_message(
                ctx.bizhawk_ctx,
                f"Received: {item_name}",
            )
        except bizhawk.RequestFailedError:
            logger.warning(f"SMB3: Failed to display item popup for {item_name}")
    
    