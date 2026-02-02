# @://nsible/cartridges/atomic_lab/init [ENTRY POINT]
import curses
import os
import sys

# Ensure local modules (pal_core) are discoverable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import the TUI class
try:
    from .pal_core import TERM_TUI
except ImportError:
    from pal_core import TERM_TUI

def run(args=None):
    """Nexus Cartridge Entry Point"""
    try:
        curses.wrapper(TERM_TUI)
    except Exception as e:
        print(f"ATOMIC LAB CRASH: {e}")
