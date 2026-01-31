import curses
from curses import textpad  # <--- CRITICAL FIX
import json
import os
import time
import textwrap

# --- CONFIGURATION ---
REPO_DIR = "TERM_Repository"

# Color Pair IDs
PAIR_RED = 1
PAIR_BRASS = 2
PAIR_SILVER = 3
PAIR_GREY = 4
PAIR_ALERT = 5

class TERM_TUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        self.elements = self.load_data()
        self.scroll_idx = 0
        self.selected_idx = 0
        self.view_mode = "BROWSE" # Modes: BROWSE, INSPECT, SEARCH
        self.drawer_open = False
        self.search_buffer = ""
        
        # Init Colors (Strict @NSIBLE-RED Palette)
        curses.start_color()
        curses.use_default_colors()
        try:
            curses.init_pair(PAIR_RED, 196, -1)     # Deep Red
            curses.init_pair(PAIR_BRASS, 220, -1)   # Gold/Brass
            curses.init_pair(PAIR_SILVER, 255, -1)  # White/Silver
            curses.init_pair(PAIR_GREY, 240, -1)    # Dark Grey
            curses.init_pair(PAIR_ALERT, 0, 196)    # Black on Red
        except:
            # Fallback for standard terminals
            curses.init_pair(PAIR_RED, curses.COLOR_RED, -1)
            curses.init_pair(PAIR_BRASS, curses.COLOR_YELLOW, -1)
            curses.init_pair(PAIR_SILVER, curses.COLOR_WHITE, -1)
            curses.init_pair(PAIR_GREY, curses.COLOR_MAGENTA, -1)
            curses.init_pair(PAIR_ALERT, curses.COLOR_BLACK, curses.COLOR_RED)

        curses.curs_set(0) # Hide cursor
        self.loop()

    def load_data(self):
        """Loads element headers for the list view."""
        data = []
        if not os.path.exists(REPO_DIR):
            return []
        
        # Sort directories by Atomic Number
        dirs = sorted([d for d in os.listdir(REPO_DIR) if os.path.isdir(os.path.join(REPO_DIR, d))])
        
        for d in dirs:
            try:
                parts = d.split('_')
                z = int(parts[0])
                name = parts[1]
                data.append({"z": z, "name": name, "dir": os.path.join(REPO_DIR, d)})
            except:
                pass
        return sorted(data, key=lambda x: x['z'])

    def get_element_details(self, index):
        if index >= len(self.elements): return None
        path = os.path.join(self.elements[index]['dir'], "profile.json")
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return None

    def draw_header(self):
        title = " T.E.R.M. v1.1 "
        # Fill header bg
        self.stdscr.attron(curses.color_pair(PAIR_ALERT))
        self.stdscr.addstr(0, 0, " " * self.width)
        # Center title
        start_x = max(0, (self.width // 2) - (len(title) // 2))
        try:
            self.stdscr.addstr(0, start_x, title)
        except:
            pass # Handle very narrow screens
        self.stdscr.attroff(curses.color_pair(PAIR_ALERT))

    def draw_list(self):
        max_rows = self.height - 2
        start_row = 1
        
        # Scroll Logic
        if self.selected_idx < self.scroll_idx:
            self.scroll_idx = self.selected_idx
        elif self.selected_idx >= self.scroll_idx + max_rows:
            self.scroll_idx = self.selected_idx - max_rows + 1

        visible_items = self.elements[self.scroll_idx : self.scroll_idx + max_rows]

        for i, el in enumerate(visible_items):
            actual_idx = self.scroll_idx + i
            row_y = start_row + i
            
            if actual_idx == self.selected_idx:
                style = curses.color_pair(PAIR_ALERT) | curses.A_BOLD
                prefix = "> "
            else:
                style = curses.color_pair(PAIR_SILVER)
                prefix = "  "

            # Check if isotope data exists for the marker
            iso_path = os.path.join(el['dir'], "isotopes.json")
            marker = "•" if os.path.exists(iso_path) else " "

            line = f"{prefix}{el['z']:03d} {el['name'].upper()}"
            # Right-align the isotope marker
            padding = self.width - len(line) - 2
            if padding > 0:
                line += " " * padding + marker
            
            try:
                self.stdscr.addstr(row_y, 0, line[:self.width], style)
            except:
                pass

    def draw_inspector(self):
        data = self.get_element_details(self.selected_idx)
        if not data: return

        # Draw Border using the imported textpad module
        self.stdscr.attron(curses.color_pair(PAIR_BRASS))
        textpad.rectangle(self.stdscr, 1, 0, self.height-2, self.width-1)
        self.stdscr.attroff(curses.color_pair(PAIR_BRASS))

        # Title
        name = data.get("name", "Unknown").upper()
        self.stdscr.addstr(1, 2, f" {name} ", curses.color_pair(PAIR_RED) | curses.A_BOLD)

        # Properties
        props = data.get("properties", {})
        y = 3
        
        # Priority Keys to show first
        priority_keys = ['standard_atomic_weight', 'phase', 'electron_configuration', 'density', 'melting_point']
        
        # Display Loop
        for key in priority_keys + [k for k in props.keys() if k not in priority_keys]:
            if key in props:
                if y > self.height - 4: break # Safety stop
                
                val = str(props[key])
                label = key.replace("_", " ").title() + ":"
                
                self.stdscr.addstr(y, 2, label, curses.color_pair(PAIR_GREY) | curses.A_BOLD)
                
                # Wrap long text values for narrow screens
                avail_width = self.width - 4
                wrapped_val = textwrap.wrap(val, width=avail_width)
                
                for line in wrapped_val:
                    if y > self.height - 4: break
                    # Indent wrapped value slightly if it's on a new line? 
                    # For TUI, just printing on next line is safer.
                    self.stdscr.addstr(y + 1, 4, line, curses.color_pair(PAIR_SILVER))
                    y += 1
                y += 1 # Extra spacer

    def draw_drawer(self):
        drawer_height = 6
        start_y = self.height - drawer_height
        
        # Draw background
        for y in range(start_y, self.height):
            self.stdscr.addstr(y, 0, " " * self.width, curses.color_pair(PAIR_ALERT))
            
        self.stdscr.addstr(start_y, 0, "▄" * self.width, curses.color_pair(PAIR_RED))
        
        options = ["[S]earch", "[C]ompare", "[F]usion", "[E]xit"]
        for i, opt in enumerate(options):
            self.stdscr.addstr(start_y + 1 + i, 2, opt, curses.color_pair(PAIR_ALERT) | curses.A_BOLD)

    def draw_search_bar(self):
        self.stdscr.addstr(self.height-2, 0, " " * self.width, curses.color_pair(PAIR_BRASS))
        self.stdscr.addstr(self.height-2, 1, f"SEARCH: {self.search_buffer}_", curses.color_pair(PAIR_BRASS) | curses.A_BOLD)

    def loop(self):
        while True:
            self.stdscr.erase()
            
            # --- RENDER ---
            self.draw_header()
            
            if self.view_mode == "BROWSE":
                self.draw_list()
            elif self.view_mode == "INSPECT":
                self.draw_inspector()
            
            if self.drawer_open:
                self.draw_drawer()

            if self.view_mode == "SEARCH":
                self.draw_search_bar()

            # --- INPUT ---
            try:
                c = self.stdscr.getch()
            except KeyboardInterrupt:
                break

            if c == ord('q') and self.view_mode != "SEARCH": break

            # Search Logic
            if self.view_mode == "SEARCH":
                if c == 10: # Enter
                    target = self.search_buffer.lower()
                    for i, el in enumerate(self.elements):
                        if target in el['name'].lower() or target == str(el['z']):
                            self.selected_idx = i
                            self.scroll_idx = i
                            break
                    self.view_mode = "BROWSE"
                    self.search_buffer = ""
                elif c == 27: # Esc
                    self.view_mode = "BROWSE"
                    self.search_buffer = ""
                elif c == 127 or c == curses.KEY_BACKSPACE: # Backspace
                    self.search_buffer = self.search_buffer[:-1]
                elif 32 <= c <= 126:
                    self.search_buffer += chr(c)
                continue

            # Standard Navigation
            if c == curses.KEY_UP:
                if self.view_mode == "BROWSE":
                    self.selected_idx = max(0, self.selected_idx - 1)
            elif c == curses.KEY_DOWN:
                if self.view_mode == "BROWSE":
                    self.selected_idx = min(len(self.elements) - 1, self.selected_idx + 1)
            
            elif c == 10: # Enter
                if self.view_mode == "BROWSE":
                    self.view_mode = "INSPECT"
                elif self.view_mode == "INSPECT":
                    self.view_mode = "BROWSE"
            
            elif c == ord('o'):
                self.drawer_open = not self.drawer_open
            
            if self.drawer_open:
                if c == ord('s'):
                    self.view_mode = "SEARCH"
                    self.drawer_open = False
                elif c == ord('e'):
                    self.drawer_open = False

            self.stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(TERM_TUI)
