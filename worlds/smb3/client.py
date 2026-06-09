from __future__ import annotations

import logging
import struct
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
    P_METER_ADDR,
    PROGRESS_FLAGS_ADDR,
    PROGRESS_FLAGS_SIZE,
    INVENTORY_ADDR,
    INVENTORY_SIZE,
    AP_SENTINEL_ADDR,
    AP_SENTINEL_VALUE,
    AP_SENTINEL_SIZE,
    AP_RECEIVED_INDEX_ADDR,
    AP_RECEIVED_INDEX_SIZE,
    AP_STARTING_WORLD_ADDR,
    PROGRESS_FLAGS_BY_WORLD,
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
        self.logged_hash: bool = False
        self.warned_not_connected: bool = False

        # ── AP SRAM tracking ────────────────────────────────────────────────
        # Index into ctx.items_received up to which items have already been
        # *physically* applied to the game (inventory slots written, lives
        # added).  Persisted to and loaded from the AP SRAM block so that
        # reconnecting to the server does not re-deliver items that were
        # already handed to the player in a previous session.
        self.received_index: int = 0

        # True once setup_ap_sram() has finished for this connection session.
        self.ap_sram_ready: bool = False

        # ── Per-session game state ──────────────────────────────────────────
        # Items whose byte values couldn't be written because the inventory
        # was full; retried one at a time each tick.
        self.pending_inventory_items: list[str] = []

        # In-memory access flags rebuilt from the *full* items_received list
        # on every tick (Pass 1 of process_received_items).  These are cheap
        # boolean flips — no SRAM writes — so rebuilding them every tick is
        # safe and avoids any stale-flag bugs on reconnect.
        self.has_p_meter_unlock: bool = False
        self.has_fortress_access: bool = False
        self.has_castle_access: bool = False

        # Cache to avoid hammering Lua with identical state updates.
        self.last_sent_lua_state: tuple[bool, bool, bool] | None = None

        # AP-chosen starting world (0-indexed).  Populated from slot_data.
        # Always 0 in the current World 1 slice; used properly in Step 2.
        self.starting_world: int = 0

    # ─── BizHawkClient overrides ──────────────────────────────────────────────

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        try:
            system_bus_size = await bizhawk.get_memory_size(ctx.bizhawk_ctx, SYSTEM_BUS_DOMAIN)
            rom_size        = await bizhawk.get_memory_size(ctx.bizhawk_ctx, ROM_DOMAIN)
        except bizhawk.RequestFailedError:
            return False

        # Sanity-check that the system bus is large enough to contain the
        # inventory region (rules out wrong systems / ROMs).
        if system_bus_size <= (INVENTORY_ADDR + INVENTORY_SIZE):
            return False

        if rom_size <= 0:
            return False

        try:
            rom_hash = await bizhawk.get_hash(ctx.bizhawk_ctx)
            if not self.logged_hash:
                logger.info(f"SMB3 ROM hash: {rom_hash}")
                self.logged_hash = True
        except bizhawk.RequestFailedError:
            pass

        ctx.game            = self.game
        ctx.items_handling  = 0b111   # receive all items (local + remote + starting)
        ctx.want_slot_data  = True
        ctx.watcher_timeout = 0.125   # poll at ~8 Hz

        # Reset all per-connection state.  received_index will be restored from
        # AP SRAM by setup_ap_sram() on the first game_watcher tick.
        self.previous_world           = None
        self.pending_inventory_items  = []
        self.has_p_meter_unlock       = False
        self.has_fortress_access      = False
        self.has_castle_access        = False
        self.last_sent_lua_state      = None
        self.starting_world           = 0
        self.received_index           = 0
        self.ap_sram_ready            = False

        return True

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        if ctx.server is None:
            if not self.warned_not_connected:
                logger.warning("SMB3: Not connected to Archipelago server. Checks will not send.")
                self.warned_not_connected = True
            return

        self.warned_not_connected = False

        if ctx.slot is None:
            return

        # Pull starting_world from slot_data as soon as it arrives.
        if ctx.slot_data and "starting_world" in ctx.slot_data:
            self.starting_world = int(ctx.slot_data["starting_world"])

        # One-time per-connection setup: read or initialise the AP SRAM block.
        # We return immediately after so that any SRAM writes can settle before
        # the first real read pass on the following tick.
        if not self.ap_sram_ready:
            await self.setup_ap_sram(ctx)
            return

        try:
            reads = await bizhawk.read(
                ctx.bizhawk_ctx,
                [
                    (CURRENT_WORLD_ADDR,  1,                   SYSTEM_BUS_DOMAIN),
                    (LIVES_ADDR,          1,                   SYSTEM_BUS_DOMAIN),
                    (P_METER_ADDR,        1,                   SYSTEM_BUS_DOMAIN),
                    (PROGRESS_FLAGS_ADDR, PROGRESS_FLAGS_SIZE, SYSTEM_BUS_DOMAIN),
                    (INVENTORY_ADDR,      INVENTORY_SIZE,      SYSTEM_BUS_DOMAIN),
                ],
            )
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: BizHawk read failed.")
            return

        current_world  = reads[0][0]
        lives          = reads[1][0]
        p_meter        = reads[2][0]
        progress_flags = reads[3]
        inventory      = reads[4]

        # Thread updated lives/inventory through the processing chain so each
        # stage sees the result of the previous one's writes.
        lives, inventory = await self.process_received_items(ctx, lives, inventory)
        inventory        = await self.sanitize_inventory(ctx, inventory)
        inventory        = await self.process_pending_inventory(ctx, inventory)

        await self.push_lua_state(ctx)
        await self.enforce_p_meter_lock(ctx, p_meter)
        await self.check_overworld_locations(ctx, current_world, progress_flags)
        await self.check_goal(ctx, current_world)

        self.previous_world = current_world

    # ─── AP SRAM management ───────────────────────────────────────────────────

    async def setup_ap_sram(self, ctx: "BizHawkClientContext") -> None:
        """
        Called once per connection session on the first game_watcher tick.

        Reads the AP sentinel from SRAM to decide whether this is a fresh save
        (no sentinel → write the full initial block) or a resumed session
        (sentinel present → load the persisted received_index).

        Sets self.ap_sram_ready = True on success so the check is skipped on
        subsequent ticks.
        """
        try:
            result = await bizhawk.read(
                ctx.bizhawk_ctx,
                [(AP_SENTINEL_ADDR, AP_SENTINEL_SIZE, SYSTEM_BUS_DOMAIN)],
            )
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: Could not read AP SRAM sentinel — will retry next tick.")
            return

        sentinel = bytes(result[0])

        if sentinel != AP_SENTINEL_VALUE:
            logger.info("SMB3: AP sentinel absent — initialising AP SRAM block.")
            await self._init_ap_sram(ctx)
            self.received_index = 0
        else:
            # Restore the persisted received_index so physical item delivery
            # resumes from the right position without re-delivering old items.
            try:
                idx_result = await bizhawk.read(
                    ctx.bizhawk_ctx,
                    [(AP_RECEIVED_INDEX_ADDR, AP_RECEIVED_INDEX_SIZE, SYSTEM_BUS_DOMAIN)],
                )
                self.received_index = struct.unpack_from("<H", bytes(idx_result[0]))[0]
                logger.info(
                    f"SMB3: AP SRAM loaded — resuming from received_index {self.received_index}."
                )
            except bizhawk.RequestFailedError:
                logger.warning("SMB3: Could not read AP_RECEIVED_INDEX — defaulting to 0.")
                self.received_index = 0

        self.ap_sram_ready = True

    async def _init_ap_sram(self, ctx: "BizHawkClientContext") -> None:
        """
        Writes the AP SRAM block with initial values for a new game:
            AP_SENTINEL_ADDR        ← "AP3\\x00"
            AP_RECEIVED_INDEX_ADDR  ← 0x0000  (u16 little-endian)
            AP_STARTING_WORLD_ADDR  ← self.starting_world
        """
        try:
            await bizhawk.write(
                ctx.bizhawk_ctx,
                [
                    (AP_SENTINEL_ADDR,
                     AP_SENTINEL_VALUE,
                     SYSTEM_BUS_DOMAIN),

                    (AP_RECEIVED_INDEX_ADDR,
                     struct.pack("<H", 0),
                     SYSTEM_BUS_DOMAIN),

                    (AP_STARTING_WORLD_ADDR,
                     bytes([self.starting_world]),
                     SYSTEM_BUS_DOMAIN),
                ],
            )
            logger.info(
                f"SMB3: AP SRAM initialised "
                f"(starting_world={self.starting_world}, World {self.starting_world + 1})."
            )
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: Failed to write AP SRAM initial block.")

    async def _persist_received_index(self, ctx: "BizHawkClientContext") -> None:
        """Writes the current received_index to AP SRAM (AP_RECEIVED_INDEX_ADDR)."""
        try:
            await bizhawk.write(
                ctx.bizhawk_ctx,
                [(AP_RECEIVED_INDEX_ADDR,
                  struct.pack("<H", self.received_index),
                  SYSTEM_BUS_DOMAIN)],
            )
        except bizhawk.RequestFailedError:
            logger.warning(
                f"SMB3: Failed to persist received_index={self.received_index} to SRAM."
            )

    # ─── Item processing ──────────────────────────────────────────────────────

    async def process_received_items(
        self,
        ctx: "BizHawkClientContext",
        lives: int,
        inventory: bytes,
    ) -> tuple[int, bytes]:
        """
        Processes ctx.items_received in two passes.

        ── Pass 1 — flag restoration (full list, no game writes) ─────────────
        Scans every item in items_received (including already-applied ones)
        to rebuild the in-memory access flags:
            has_p_meter_unlock, has_fortress_access, has_castle_access.

        This is idempotent and cheap (boolean assignments only), so it always
        runs in full.  It ensures flags are always correct after a reconnect,
        even before any new items have arrived from the server.

        ── Pass 2 — physical delivery (new items only) ───────────────────────
        Applies items at index >= self.received_index:
            • Inventory items  → byte written into the first empty SRAM slot.
            • Life items       → added to the lives counter (capped at 99).
            • Access/event items → handled entirely in Pass 1; no game write.

        After each item, received_index is incremented and persisted to AP SRAM
        so that reconnecting resumes from the correct position without
        re-delivering items that were already given to the player.

        Returns the updated (lives, inventory) so the caller's view stays
        consistent with what has actually been written to the game.
        """
        # ── Pass 1: rebuild in-memory access flags ────────────────────────────
        # Reset first so a disconnected/revoked item is handled correctly.
        self.has_p_meter_unlock  = False
        self.has_fortress_access = False
        self.has_castle_access   = False

        for network_item in ctx.items_received:
            item_name = ITEM_CODE_TO_NAME.get(network_item.item)
            if item_name == "P-Meter Unlock":
                self.has_p_meter_unlock = True
            elif item_name == "World 1 Fortress Access":
                self.has_fortress_access = True
            elif item_name == "World 1 Castle Access":
                self.has_castle_access = True

        # ── Pass 2: physically apply items we haven't delivered yet ───────────
        while self.received_index < len(ctx.items_received):
            network_item = ctx.items_received[self.received_index]
            item_name    = ITEM_CODE_TO_NAME.get(network_item.item)

            if item_name is None:
                logger.warning(f"SMB3: Unknown item code: {network_item.item}")
                self.received_index += 1
                await self._persist_received_index(ctx)
                continue

            await self.show_item_popup(ctx, item_name)

            if item_name in INVENTORY_ITEM_VALUES:
                inventory = await self.give_inventory_item(ctx, inventory, item_name)

            elif item_name in LIFE_ITEM_VALUES:
                lives = await self.give_lives(ctx, lives, LIFE_ITEM_VALUES[item_name])

            elif item_name in (
                "P-Meter Unlock",
                "World 1 Fortress Access",
                "World 1 Castle Access",
                "Beat World 1 Castle",
            ):
                # In-memory flags set in Pass 1; event item needs no game write.
                pass

            else:
                logger.warning(f"SMB3: No physical handler for item: {item_name}")

            self.received_index += 1
            await self._persist_received_index(ctx)

        return lives, inventory

    # ─── Inventory management ─────────────────────────────────────────────────

    async def give_inventory_item(
        self,
        ctx: "BizHawkClientContext",
        inventory: bytes,
        item_name: str,
    ) -> bytes:
        """
        Writes item_name's byte value into the first empty (0x00) inventory slot.
        Returns the updated inventory.  If all 28 slots are occupied the item
        is queued in pending_inventory_items to be retried next tick.
        """
        item_value     = INVENTORY_ITEM_VALUES[item_name]
        inventory_list = list(inventory)

        for i, slot in enumerate(inventory_list):
            if slot == 0x00:
                try:
                    await bizhawk.write(
                        ctx.bizhawk_ctx,
                        [(INVENTORY_ADDR + i, bytes([item_value]), SYSTEM_BUS_DOMAIN)],
                    )
                except bizhawk.RequestFailedError:
                    logger.warning(f"SMB3: Failed to write inventory item {item_name}.")
                    return inventory

                inventory_list[i] = item_value
                return bytes(inventory_list)

        # Inventory full — queue for next tick.
        self.pending_inventory_items.append(item_name)
        logger.info(f"SMB3: Inventory full — queued {item_name} for retry.")
        return inventory

    async def give_lives(
        self,
        ctx: "BizHawkClientContext",
        current_lives: int,
        amount: int,
    ) -> int:
        """Adds *amount* lives to the counter, capped at 99.  Returns the new value."""
        new_lives = min(current_lives + amount, 99)
        try:
            await bizhawk.write(
                ctx.bizhawk_ctx,
                [(LIVES_ADDR, bytes([new_lives]), SYSTEM_BUS_DOMAIN)],
            )
        except bizhawk.RequestFailedError:
            logger.warning(f"SMB3: Failed to write lives (+{amount}).")
            return current_lives
        return new_lives

    async def process_pending_inventory(
        self,
        ctx: "BizHawkClientContext",
        inventory: bytes,
    ) -> bytes:
        """
        Retries the first item in pending_inventory_items.  If a slot has freed
        up since last tick the write will succeed and the item is dequeued.
        """
        if not self.pending_inventory_items:
            return inventory

        next_item     = self.pending_inventory_items[0]
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
        """
        Removes Warp Whistles (byte value 0x0C) from the inventory using a
        guarded write (atomic check-then-clear).  Whistles skip to worlds 5–8
        and would bypass the goal structure if left in the player's possession.
        """
        write_list     = []
        guard_list     = []
        inventory_list = list(inventory)

        for i, slot in enumerate(inventory_list):
            if slot == 0x0C:
                addr = INVENTORY_ADDR + i
                write_list.append((addr, bytes([0x00]), SYSTEM_BUS_DOMAIN))
                guard_list.append((addr, bytes([0x0C]), SYSTEM_BUS_DOMAIN))
                inventory_list[i] = 0x00

        if not write_list:
            return inventory

        try:
            success = await bizhawk.guarded_write(
                ctx.bizhawk_ctx,
                write_list,
                guard_list,
            )
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: Failed to sanitize whistle from inventory.")
            return inventory

        return bytes(inventory_list) if success else inventory

    # ─── Lua state sync ───────────────────────────────────────────────────────

    async def push_lua_state(self, ctx: "BizHawkClientContext") -> None:
        """
        Sends the current access flags to the Lua connector (SMB3_SET_STATE)
        so its frame-start gate can allow or block entry to locked map nodes.
        Only transmits when the state has actually changed to avoid unnecessary
        round-trips.
        """
        state_tuple = (
            self.has_fortress_access,
            self.has_castle_access,
            self.has_p_meter_unlock,
        )

        if self.last_sent_lua_state == state_tuple:
            return

        try:
            await bizhawk.send_requests(
                ctx.bizhawk_ctx,
                [
                    {
                        "type":             "SMB3_SET_STATE",
                        "fortress_access":  self.has_fortress_access,
                        "castle_access":    self.has_castle_access,
                        "p_meter_unlock":   self.has_p_meter_unlock,
                        "enabled":          True,
                    }
                ],
            )
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: Failed to push Lua state.")
            return

        self.last_sent_lua_state = state_tuple

    # ─── P-Meter enforcement ──────────────────────────────────────────────────

    async def enforce_p_meter_lock(
        self,
        ctx: "BizHawkClientContext",
        current_p_meter: int,
    ) -> None:
        """
        Actively zeroes the P-Meter register each tick if the player hasn't
        received P-Meter Unlock.  The Lua connector enforces the same lock
        every frame start; this Python-side check (~8 Hz) acts as a fallback.
        """
        if self.has_p_meter_unlock or current_p_meter == 0:
            return

        try:
            await bizhawk.write(
                ctx.bizhawk_ctx,
                [(P_METER_ADDR, bytes([0x00]), SYSTEM_BUS_DOMAIN)],
            )
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: Failed to enforce P-Meter lock.")

    # ─── Check / goal detection ───────────────────────────────────────────────

    async def check_overworld_locations(
        self,
        ctx: "BizHawkClientContext",
        current_world: int,
        progress_flags: bytes,
    ) -> None:
        """
        Reads completion bits from the current world's buffered SRAM snapshot
        and sends any newly set locations to the AP server.

        SMB3 reuses the same 64-byte completion buffer for each overworld map,
        so the same byte/bit can mean different checks in different worlds.
        The current world counter selects the correct per-map table.
        """
        locations_to_send: list[int] = []
        progress_flags_for_world = PROGRESS_FLAGS_BY_WORLD.get(current_world, {})

        for location_id, (offset, mask) in progress_flags_for_world.items():
            if location_id not in ctx.missing_locations:
                continue
            if progress_flags[offset] & mask:
                locations_to_send.append(location_id)

        if locations_to_send:
            await ctx.send_msgs(
                [{"cmd": "LocationChecks", "locations": locations_to_send}]
            )

    async def check_goal(
        self,
        ctx: "BizHawkClientContext",
        current_world: int,
    ) -> None:
        """
        Detects goal completion by watching for the world counter to advance
        from 0 → 1.  This happens when the game executes INC $0727 at the end
        of the World 1 Castle sequence (confirmed at PRG bank 30, offset 0x3D0A1).
        """
        if ctx.finished_game:
            return

        if self.previous_world is None:
            return

        if not (self.previous_world == 0 and current_world == 1):
            return

        messages: list[dict] = []

        if CASTLE_LOCATION_ID in ctx.missing_locations:
            messages.append(
                {"cmd": "LocationChecks", "locations": [CASTLE_LOCATION_ID]}
            )

        messages.append(
            {"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}
        )

        await ctx.send_msgs(messages)
        ctx.finished_game = True
        logger.info("SMB3: World 1 Castle cleared — goal complete.")

    # ─── Display ─────────────────────────────────────────────────────────────

    async def show_item_popup(
        self,
        ctx: "BizHawkClientContext",
        item_name: str,
    ) -> None:
        """Queues a BizHawk OSD message when an item is received."""
        try:
            await bizhawk.display_message(
                ctx.bizhawk_ctx,
                f"Received: {item_name}",
            )
        except bizhawk.RequestFailedError:
            logger.warning(f"SMB3: Failed to display popup for {item_name}.")
