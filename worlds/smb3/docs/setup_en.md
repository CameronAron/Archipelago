# Super Mario Bros. 3 Archipelago Setup Guide

## What you need

- The Archipelago Laucher
- BizHawk
- A valid USA 1.0 Super Mario Bros. 3 ROM
- The SMB3 APWorld/LUA connector files for this world

## Current Status
This guide is for an in-progress world implementation.

----------------------------------------

Step 1 - Install the SMB3 world

1. Open the Archipelago launcher and click "Install AP World"
2. Locate and open the smb3.apworld file in this folder when the dialogue box opens

----------------------------------------

Step 2 - Move the connector_smb3.lua file

1. Move the "connector_smb3.lua" file that came included in this folder to the YourArchipelagoInstall/data/lua folder

----------------------------------------

Step 3 - Setup BizHawk

1. Open BizHawk
2. Load the SMB3 USA 1.0 ROM
3. Go to:
   Tools → Lua Console
4. Click "Script → Open Script"
5. Select:
   connector_smb3.lua

----------------------------------------

Step 4 - Generate game

1. Generate a game in the Archipelago Launcher by creating your own YAML in the options creator
2. After generating a game, host the game on your machine or on the archipelago.gg site

----------------------------------------

Step 5 - Connect to the game

1. Run Archipelago Launcher
2. Open BizHawk Client
3. Enter the server address and your slot name
4. Click Connect

IMPORTANT:
You must connect to the server or checks will NOT send.

----------------------------------------

Notes:
- Fortress and Castle may be locked until you receive access items
- P-Meter will not work until unlocked
- If something seems broken, make sure you are using SMB3 USA 1.0
