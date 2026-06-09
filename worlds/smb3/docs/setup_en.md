# Super Mario Bros. 3 Archipelago Setup Guide

## What you need

- A working Archipelago source checkout
- BizHawk
- A valid USA 1.0 Super Mario Bros. 3 ROM
- The SMB3 client/connector files for this world

## Current Status

This guide is for an in-progress world implementation.
Full play instructions will be expanded as development continues.

## Connector note

This checkout includes the SMB3 BizHawk Lua connector at `data/lua/connector_smb3.lua`. Some older notes may call it `data/lua/smb3_connector.lua`; use the filename that exists in your checkout.


## Running tests from source

Install the repository requirements before running SMB3 tests. The test harness imports `yaml`, which is provided by `PyYAML==6.0.3` in `requirements.txt`.
