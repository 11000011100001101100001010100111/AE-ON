import sys
import os

CORE_DOCS = {
    "SYS": """
NAME
    sys - System Diagnostics

SYNOPSIS
    sys

DESCRIPTION
    Reports Kernel, Power, Crypto, and Cartridge status.
""",
    "NAV": """
NAME
    Navigation - Chrono-Deck Control

SYNOPSIS
    slip <N> | push <N> | live

DESCRIPTION
    Traverse session history.
    slip <N> : Go back N lines.
    push <N> : Go forward N lines.
    live     : Snap to present.
""",
    "REFRACT": """
NAME
    refract - Context Engine

SYNOPSIS
    refract

DESCRIPTION
    Generates the Cognitive Seed for AI synchronization.
""",
    "METEOR": """
NAME
    meteor (alias: slap) - Atmospheric Data

SYNOPSIS
    meteor | slap

DESCRIPTION
    Fetches real-time weather/atmospheric data via the Sensory Bridge.
""",
    "SIGNAL": """
NAME
    signal - ArchX Comms

SYNOPSIS
    signal <message>

DESCRIPTION
    Appends a message to the Neural Link.
""",
    "LINK": """
NAME
    link - Neural History

SYNOPSIS
    link

DESCRIPTION
    Displays the last few entries of the Neural Link comms log.
""",
    "CRYPTO": """
NAME
    enc / dec - Birdsong Cryptography

SYNOPSIS
    enc <text> | dec <token>

DESCRIPTION
    Encrypts or Decrypts text using the active Birdsong key.
""",
    "SAVE": """
NAME
    save - Git Diplomat

SYNOPSIS
    save

DESCRIPTION
    Commits changes to the Lattice history.
"""
}

def render_page(title, content):
    os.system('clear')
    print(f"\033[33m┌──[ MAN PAGE: {title} ]{'─' * 40}┐\033[0m")
    lines = content.strip().split('\n')
    for line in lines:
        if any(line.strip().startswith(x) for x in ["NAME", "SYNOPSIS", "DESCRIPTION", "EXAMPLES"]):
            print(f"\033[36m{line}\033[0m") 
        else:
            print(f"  {line}")
    print(f"\033[33m└{'─' * 60}┘\033[0m")
    input("\033[90m[PRESS ENTER]\033[0m")

def show_index(cartridges):
    os.system('clear')
    print(f"\033[33m┌──[ Æ-ON SYSTEM MANUAL ]{'─' * 40}┐\033[0m")
    print("\n\033[31m  CORE COMMANDS:\033[0m")
    
    # Sort and columnize
    keys = sorted(CORE_DOCS.keys())
    for i in range(0, len(keys), 2):
        c1 = keys[i]
        c2 = keys[i+1] if i+1 < len(keys) else ""
        print(f"   {c1:<15} {c2}")

    print("\n\033[31m  CARTRIDGES:\033[0m")
    if not cartridges:
        print("   (None Mounted)")
    else:
        for name in cartridges:
            print(f"   - {name}")
    print(f"\n\033[33m└{'─' * 60}┘\033[0m")
    print("USAGE: help <topic>")

def open_manual(topic, cartridges):
    topic = topic.upper()
    if topic in CORE_DOCS:
        render_page(topic, CORE_DOCS[topic])
        return
    if topic.lower() in cartridges:
        render_page(topic, f"NAME\n    {topic.lower()} - Cartridge\n\nSTATUS\n    Active")
        return
    print(f"\033[31m[!] NO MANUAL ENTRY FOR: {topic}\033[0m")
    time.sleep(1)
