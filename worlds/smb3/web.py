from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld


class SMB3WebWorld(WebWorld):
    game = "Super Mario Bros. 3"
    theme = "grass"

    setup_en = Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up Super Mario Bros. 3 for Archipelago.",
        "English",
        "setup_en.md",
        "setup/en",
        ["CameronAron"],
    )

    tutorials = [setup_en]