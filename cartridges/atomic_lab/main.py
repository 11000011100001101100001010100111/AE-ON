# @://nsible/cartridges/atomic_lab/main [LAUNCHER]
# -----------------------------------------------------------------------------
# AE-ON CARTRIDGE LAUNCHER
# -----------------------------------------------------------------------------
import curses
import sys
import os

# Add current directory to path so pal_core can resolve dependencies
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pal_core import TERM_TUI

if __name__ == "__main__":
    curses.wrapper(TERM_TUI)

# @://nsible/end_transmission [0t-strict]
