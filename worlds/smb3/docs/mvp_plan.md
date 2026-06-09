# SMB3 MVP Implementation Plan

This is the working plan for the full SMB3 Archipelago MVP described by the
maintainer.  It complements `check_research.md`, which tracks the current SRAM
clear-flag research.

## Existing connector

This repository currently includes the SMB3 BizHawk Lua connector at
`data/lua/connector_smb3.lua`.  Some notes or external checkouts may refer to it
as `data/lua/smb3_connector.lua`; verify the filename in the checkout before
writing setup instructions or client-side launch helpers.

The connector is useful for per-frame enforcement and AP-client-to-emulator
requests, but the planned warp/persistence MVP probably should not rely on Lua
alone.  Lua can write RAM at runtime, but it cannot safely add new permanent game
logic to the ROM by itself.

## Why a ROM patch is likely needed

The manual warp and persistent per-world clear-state features need stronger
control than the current World 1 vertical slice:

- initialize a random starting world in a stable way,
- warp to any AP-unlocked world on command,
- restore that world's already-cleared level flags into the game's active
  `$7D00-$7D3F` completion buffer,
- avoid replay requirements after returning to a previously visited world,
- block world/fortress/castle barriers consistently in-game,
- keep all of this stable across save/load and AP reconnects.

The current Python client can write RAM and SRAM through BizHawk, and the Lua
connector can enforce simple per-frame gates.  For the MVP, however, an AP patch
file should eventually install a small ROM hook or custom routine so these state
changes happen at predictable game-safe points instead of relying only on external
writes while the game may be in the middle of overworld logic.

## Proposed MVP stages

1. **Validated check table**
   - Keep the current later-world clear flags as candidate data.
   - Validate each candidate in BizHawk by clearing the corresponding level and
     recording the exact `$7D00-$7D3F` bit transition for that world.

2. **Generation options**
   - Add a starting-world option that can choose a random world from 1 through 7.
   - Keep World 8 out of random starts until Bowser/World 8 routing is designed.
   - Add goal options later: Bowser, number of worlds cleared, number of levels
     cleared, or other custom goals.

3. **Access items and AP logic**
   - Use `World N Unlock` items to determine which worlds can be warped to.
   - Use `World N Fortress Access` and `World N Castle Access` items for that
     world's barrier logic.
   - Add later-world castle/airship/Bowser checks only after their clear events
     are researched and validated.

4. **Manual warp command**
   - Add an AP client command such as `/smb3_warp 4`.
   - The command should reject locked worlds and unsafe game states.
   - The client should send a connector request or write to a patch-owned command
     mailbox in SRAM/RAM; the ROM patch should perform the actual transition at a
     safe overworld point.

5. **Persistent per-world clear state**
   - Reserve AP SRAM space for eight 64-byte clear-state buffers, one per world.
   - When a clear check is detected, copy the changed bit into that world's AP
     clear-state buffer.
   - When warping into a world, restore that world's AP clear-state buffer into
     the active game completion buffer before the overworld map becomes playable.

6. **Optional features after MVP**
   - Optional checks: Toad Houses, Spade/Poker tiles, Hammer Bros., etc.
   - Level entrance randomization.
   - Traps and other filler effects.
   - More configurable goals.

## PyYAML / pytest note

`python -m pytest worlds/smb3/test` imports the wider Archipelago package, and
that package imports `yaml` from PyYAML through `Utils.py`.  The dependency is
already declared in the repository's `requirements.txt` as `PyYAML==6.0.3`.

To solve the local test error, install the project requirements in the Python
environment used for tests, for example:

```bash
python -m pip install -r requirements.txt
```

or, for this specific missing module only:

```bash
python -m pip install PyYAML==6.0.3
```

Impact: the missing dependency does not mean the SMB3 code is definitely broken;
it means pytest cannot even import the test harness, so the SMB3 tests did not
run.  That is a validation gap.  In a fully provisioned development environment
or CI job with requirements installed, the same tests should be run again.
