from __future__ import annotations
import logging, struct
from typing import TYPE_CHECKING
from NetUtils import ClientStatus
import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient
from .constants import (
    GAME_NAME, SYSTEM_NAME, SYSTEM_BUS_DOMAIN, ROM_DOMAIN,
    CURRENT_WORLD_ADDR, LIVES_ADDR, P_METER_ADDR,
    PROGRESS_FLAGS_ADDR, PROGRESS_FLAGS_SIZE, INVENTORY_ADDR, INVENTORY_SIZE,
    AP_SENTINEL_ADDR, AP_SENTINEL_VALUE, AP_SENTINEL_SIZE,
    AP_RECEIVED_INDEX_ADDR, AP_RECEIVED_INDEX_SIZE, AP_STARTING_WORLD_ADDR,
    ACCESS_ITEM_NAMES, FORTRESS_ACCESS_ITEM_NAMES, CASTLE_ACCESS_ITEM_NAMES,
    WORLD_UNLOCK_ITEM_NAMES, PROGRESS_FLAGS_BY_WORLD,
    ITEM_CODE_TO_NAME, INVENTORY_ITEM_VALUES, LIFE_ITEM_VALUES,
    WORLD_1_CASTLE_LOCATION_ID, WORLD_2_CASTLE_LOCATION_ID,
)
if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger("Client")

class SMB3BizHawkClient(BizHawkClient):
    game   = GAME_NAME
    system = SYSTEM_NAME
    patch_suffix = None

    def __init__(self) -> None:
        self.previous_world: int | None = None
        self.logged_hash = False
        self.warned_not_connected = False
        self.received_index = 0
        self.ap_sram_ready  = False
        self.pending_inventory_items: list[str] = []
        self.has_p_meter_unlock  = False
        self.has_fortress_access = False   # World 1 (Lua gate)
        self.has_castle_access   = False   # World 1 (Lua gate)
        self.unlocked_worlds:        set[int] = set()
        self.fortress_access_worlds: set[int] = set()
        self.castle_access_worlds:   set[int] = set()
        self.last_sent_lua_state: tuple | None = None
        self.starting_world = 0

    async def validate_rom(self, ctx) -> bool:
        try:
            sz  = await bizhawk.get_memory_size(ctx.bizhawk_ctx, SYSTEM_BUS_DOMAIN)
            rsz = await bizhawk.get_memory_size(ctx.bizhawk_ctx, ROM_DOMAIN)
        except bizhawk.RequestFailedError:
            return False
        if sz <= (INVENTORY_ADDR + INVENTORY_SIZE) or rsz <= 0:
            return False
        try:
            h = await bizhawk.get_hash(ctx.bizhawk_ctx)
            if not self.logged_hash:
                logger.info(f"SMB3 ROM hash: {h}")
                self.logged_hash = True
        except bizhawk.RequestFailedError:
            pass
        ctx.game = self.game; ctx.items_handling = 0b111
        ctx.want_slot_data = True; ctx.watcher_timeout = 0.125
        self.previous_world = None; self.pending_inventory_items = []
        self.has_p_meter_unlock = self.has_fortress_access = self.has_castle_access = False
        self.unlocked_worlds = self.fortress_access_worlds = self.castle_access_worlds = set()
        self.last_sent_lua_state = None; self.starting_world = 0
        self.received_index = 0; self.ap_sram_ready = False
        return True

    async def game_watcher(self, ctx) -> None:
        if ctx.server is None:
            if not self.warned_not_connected:
                logger.warning("SMB3: Not connected to AP server.")
                self.warned_not_connected = True
            return
        self.warned_not_connected = False
        if ctx.slot is None: return
        if ctx.slot_data and "starting_world" in ctx.slot_data:
            self.starting_world = int(ctx.slot_data["starting_world"])
        if not self.ap_sram_ready:
            await self.setup_ap_sram(ctx); return
        try:
            reads = await bizhawk.read(ctx.bizhawk_ctx, [
                (CURRENT_WORLD_ADDR,  1,                   SYSTEM_BUS_DOMAIN),
                (LIVES_ADDR,          1,                   SYSTEM_BUS_DOMAIN),
                (P_METER_ADDR,        1,                   SYSTEM_BUS_DOMAIN),
                (PROGRESS_FLAGS_ADDR, PROGRESS_FLAGS_SIZE, SYSTEM_BUS_DOMAIN),
                (INVENTORY_ADDR,      INVENTORY_SIZE,      SYSTEM_BUS_DOMAIN),
            ])
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: read failed."); return
        current_world  = reads[0][0]; lives = reads[1][0]
        p_meter        = reads[2][0]
        progress_flags = reads[3];   inventory = reads[4]
        lives, inventory = await self.process_received_items(ctx, lives, inventory)
        inventory = await self.sanitize_inventory(ctx, inventory)
        inventory = await self.process_pending_inventory(ctx, inventory)
        await self.push_lua_state(ctx)
        await self.enforce_p_meter_lock(ctx, p_meter)
        await self.check_overworld_locations(ctx, current_world, progress_flags)
        await self.check_castle_transitions(ctx, current_world)
        self.previous_world = current_world

    # ── AP SRAM ───────────────────────────────────────────────────────────────
    async def setup_ap_sram(self, ctx) -> None:
        try:
            r = await bizhawk.read(ctx.bizhawk_ctx,
                                   [(AP_SENTINEL_ADDR, AP_SENTINEL_SIZE, SYSTEM_BUS_DOMAIN)])
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: sentinel read failed, retrying."); return
        if bytes(r[0]) != AP_SENTINEL_VALUE:
            logger.info("SMB3: Initialising AP SRAM block.")
            await self._init_ap_sram(ctx); self.received_index = 0
        else:
            try:
                ir = await bizhawk.read(ctx.bizhawk_ctx,
                    [(AP_RECEIVED_INDEX_ADDR, AP_RECEIVED_INDEX_SIZE, SYSTEM_BUS_DOMAIN)])
                self.received_index = struct.unpack_from("<H", bytes(ir[0]))[0]
                logger.info(f"SMB3: AP SRAM loaded, received_index={self.received_index}")
            except bizhawk.RequestFailedError:
                self.received_index = 0
        self.ap_sram_ready = True

    async def _init_ap_sram(self, ctx) -> None:
        try:
            await bizhawk.write(ctx.bizhawk_ctx, [
                (AP_SENTINEL_ADDR,       AP_SENTINEL_VALUE,              SYSTEM_BUS_DOMAIN),
                (AP_RECEIVED_INDEX_ADDR, struct.pack("<H", 0),           SYSTEM_BUS_DOMAIN),
                (AP_STARTING_WORLD_ADDR, bytes([self.starting_world]),   SYSTEM_BUS_DOMAIN),
            ])
        except bizhawk.RequestFailedError:
            logger.warning("SMB3: AP SRAM init failed.")

    async def _persist_received_index(self, ctx) -> None:
        try:
            await bizhawk.write(ctx.bizhawk_ctx,
                [(AP_RECEIVED_INDEX_ADDR, struct.pack("<H", self.received_index), SYSTEM_BUS_DOMAIN)])
        except bizhawk.RequestFailedError:
            pass

    # ── Item processing ───────────────────────────────────────────────────────
    async def process_received_items(self, ctx, lives, inventory):
        # Pass 1: rebuild all flags (no game writes)
        self.has_p_meter_unlock = False
        self.unlocked_worlds = self.fortress_access_worlds = self.castle_access_worlds = set()
        for ni in ctx.items_received:
            n = ITEM_CODE_TO_NAME.get(ni.item)
            if n == "P-Meter Unlock":            self.has_p_meter_unlock = True
            elif n in WORLD_UNLOCK_ITEM_NAMES:   self.unlocked_worlds.add(WORLD_UNLOCK_ITEM_NAMES.index(n))
            elif n in FORTRESS_ACCESS_ITEM_NAMES: self.fortress_access_worlds.add(FORTRESS_ACCESS_ITEM_NAMES.index(n))
            elif n in CASTLE_ACCESS_ITEM_NAMES:   self.castle_access_worlds.add(CASTLE_ACCESS_ITEM_NAMES.index(n))
        self.has_fortress_access = 0 in self.fortress_access_worlds
        self.has_castle_access   = 0 in self.castle_access_worlds
        # Pass 2: physically deliver new items
        while self.received_index < len(ctx.items_received):
            ni = ctx.items_received[self.received_index]
            n  = ITEM_CODE_TO_NAME.get(ni.item)
            if n is None:
                self.received_index += 1; await self._persist_received_index(ctx); continue
            await self.show_item_popup(ctx, n)
            if n in INVENTORY_ITEM_VALUES:
                inventory = await self.give_inventory_item(ctx, inventory, n)
            elif n in LIFE_ITEM_VALUES:
                lives = await self.give_lives(ctx, lives, LIFE_ITEM_VALUES[n])
            self.received_index += 1
            await self._persist_received_index(ctx)
        return lives, inventory

    async def give_inventory_item(self, ctx, inventory, name):
        val = INVENTORY_ITEM_VALUES[name]; lst = list(inventory)
        for i, s in enumerate(lst):
            if s == 0x00:
                try:
                    await bizhawk.write(ctx.bizhawk_ctx,
                        [(INVENTORY_ADDR + i, bytes([val]), SYSTEM_BUS_DOMAIN)])
                except bizhawk.RequestFailedError:
                    return inventory
                lst[i] = val; return bytes(lst)
        self.pending_inventory_items.append(name); return inventory

    async def give_lives(self, ctx, lives, amount):
        nl = min(lives + amount, 99)
        try:
            await bizhawk.write(ctx.bizhawk_ctx, [(LIVES_ADDR, bytes([nl]), SYSTEM_BUS_DOMAIN)])
        except bizhawk.RequestFailedError:
            return lives
        return nl

    async def process_pending_inventory(self, ctx, inventory):
        if not self.pending_inventory_items: return inventory
        ni = await self.give_inventory_item(ctx, inventory, self.pending_inventory_items[0])
        if ni != inventory: self.pending_inventory_items.pop(0)
        return ni

    async def sanitize_inventory(self, ctx, inventory):
        wl, gl, lst = [], [], list(inventory)
        for i, s in enumerate(lst):
            if s == 0x0C:
                a = INVENTORY_ADDR + i
                wl.append((a, bytes([0x00]), SYSTEM_BUS_DOMAIN))
                gl.append((a, bytes([0x0C]), SYSTEM_BUS_DOMAIN))
                lst[i] = 0x00
        if not wl: return inventory
        try:
            ok = await bizhawk.guarded_write(ctx.bizhawk_ctx, wl, gl)
        except bizhawk.RequestFailedError:
            return inventory
        return bytes(lst) if ok else inventory

    # ── Lua gate sync ─────────────────────────────────────────────────────────
    async def push_lua_state(self, ctx) -> None:
        t = (self.has_fortress_access, self.has_castle_access, self.has_p_meter_unlock)
        if self.last_sent_lua_state == t: return
        try:
            await bizhawk.send_requests(ctx.bizhawk_ctx, [{
                "type":"SMB3_SET_STATE",
                "fortress_access": self.has_fortress_access,
                "castle_access":   self.has_castle_access,
                "p_meter_unlock":  self.has_p_meter_unlock,
                "enabled": True,
            }])
        except bizhawk.RequestFailedError:
            return
        self.last_sent_lua_state = t

    # ── P-Meter lock ──────────────────────────────────────────────────────────
    async def enforce_p_meter_lock(self, ctx, p_meter) -> None:
        if self.has_p_meter_unlock or p_meter == 0: return
        try:
            await bizhawk.write(ctx.bizhawk_ctx,
                [(P_METER_ADDR, bytes([0x00]), SYSTEM_BUS_DOMAIN)])
        except bizhawk.RequestFailedError: pass

    # ── Location checks ───────────────────────────────────────────────────────
    async def check_overworld_locations(self, ctx, current_world, progress_flags) -> None:
        flags = PROGRESS_FLAGS_BY_WORLD.get(current_world)
        if not flags: return
        sends = [lid for lid, (off, msk) in flags.items()
                 if lid in ctx.missing_locations and (progress_flags[off] & msk)]
        if sends:
            await ctx.send_msgs([{"cmd":"LocationChecks","locations":sends}])

    async def check_castle_transitions(self, ctx, current_world) -> None:
        """
        Detects castle completions via world-counter transitions:
          0→1  World 1 Castle Clear  (regular shuffled check)
          1→2  World 2 Castle Clear  (goal)
        """
        if self.previous_world is None: return
        prev = self.previous_world

        # World 1 Castle — regular check, sends location only
        if prev == 0 and current_world == 1:
            if WORLD_1_CASTLE_LOCATION_ID in ctx.missing_locations:
                await ctx.send_msgs([{"cmd":"LocationChecks",
                                       "locations":[WORLD_1_CASTLE_LOCATION_ID]}])

        # World 2 Castle — goal
        if not ctx.finished_game and prev == 1 and current_world == 2:
            msgs = []
            if WORLD_2_CASTLE_LOCATION_ID in ctx.missing_locations:
                msgs.append({"cmd":"LocationChecks",
                             "locations":[WORLD_2_CASTLE_LOCATION_ID]})
            msgs.append({"cmd":"StatusUpdate","status":ClientStatus.CLIENT_GOAL})
            await ctx.send_msgs(msgs)
            ctx.finished_game = True
            logger.info("SMB3: World 2 Castle cleared — goal complete.")

    async def show_item_popup(self, ctx, name) -> None:
        try:
            await bizhawk.display_message(ctx.bizhawk_ctx, f"Received: {name}")
        except bizhawk.RequestFailedError: pass
