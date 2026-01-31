import curses
import json
import os
import time

# --- CONFIGURATION ---
REPO_DIR = "TERM_Repository"
# Colors are initialized in main()
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
        self.view_mode = "BROWSE" # BROWSE, INSPECT, DRAWER, COMPARE, SEARCH
        self.drawer_open = False
        self.search_buffer = ""
        self.compare_slots = [None, None]
        
        # Init Colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(PAIR_RED, curses.COLOR_RED, -1)
        curses.init_pair(PAIR_BRASS, curses.COLOR_YELLOW, -1)
        curses.init_pair(PAIR_SILVER, curses.COLOR_WHITE, -1)
        curses.init_pair(PAIR_GREY, curses.COLOR_BLACK, -1) # Usually renders as dark grey if bold
        curses.init_pair(PAIR_ALERT, curses.COLOR_BLACK, curses.COLOR_RED) # Black text on Red bg

        # Hide cursor
        curses.curs_set(0)
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
                # Format: "001_Hydrogen"
                z_str, name = d.split('_')
                z = int(z_str)
                data.append({"z": z, "name": name, "dir": os.path.join(REPO_DIR, d)})
            except:
                pass
        return sorted(data, key=lambda x: x['z'])

    def get_element_details(self, index):
        """Fetches full profile for inspection."""
        if index >= len(self.elements): return None
        path = os.path.join(self.elements[index]['dir'], "profile.json")
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return None

    def draw_header(self):
        title = " T.E.R.M. v1.0 "
        # Draw top bar
        self.stdscr.attron(curses.color_pair(PAIR_RED) | curses.A_BOLD)
        self.stdscr.addstr(0, 0, "█" * self.width)
        # Center title
        start_x = max(0, (self.width // 2) - (len(title) // 2))
        self.stdscr.addstr(0, start_x, title, curses.color_pair(PAIR_ALERT))
        self.stdscr.attroff(curses.color_pair(PAIR_RED) | curses.A_BOLD)

    def draw_list(self):
        """Draws the scrollable element list."""
        max_rows = self.height - 4 # Reserve space for header/footer
        start_row = 2
        
        # Scroll logic
        if self.selected_idx < self.scroll_idx:
            self.scroll_idx = self.selected_idx
        elif self.selected_idx >= self.scroll_idx + max_rows:
            self.scroll_idx = self.selected_idx - max_rows + 1

        visible_items = self.elements[self.scroll_idx : self.scroll_idx + max_rows]

        for i, el in enumerate(visible_items):
            actual_idx = self.scroll_idx + i
            row_y = start_row + i
            
            # Styling
            if actual_idx == self.selected_idx:
                style = curses.color_pair(PAIR_ALERT) | curses.A_BOLD
                prefix = "> "
            else:
                style = curses.color_pair(PAIR_SILVER)
                prefix = "  "

            # Render Line: "  001 Hydrogen"
            line = f"{prefix}{el['z']:03d} {el['name'].upper()}"
            # Padding
            line = line.ljust(self.width - 2)
            self.stdscr.addstr(row_y, 1, line[:self.width-2], style)

    def draw_inspector(self):
        """Draws the single element detail view."""
        data = self.get_element_details(self.selected_idx)
        if not data: return

        # Box
        self.stdscr.attron(curses.color_pair(PAIR_BRASS))
        curses.textpad.rectangle(self.stdscr, 1, 0, self.height-2, self.width-1)
        self.stdscr.attroff(curses.color_pair(PAIR_BRASS))

        # Title
        name = data.get("name", "Unknown").upper()
        self.stdscr.addstr(2, 2, f" {name} ", curses.color_pair(PAIR_RED) | curses.A_BOLD)

        # Props
        props = data.get("properties", {})
        y = 4
        for k, v in props.items():
            if y > self.height - 4: break
            key_txt = k.replace("_", " ").title()
            
            self.stdscr.addstr(y, 2, f"{key_txt}:", curses.color_pair(PAIR_GREY) | curses.A_BOLD)
            # Wrap value if too long
            val_str = str(v)
            if len(key_txt) + len(val_str) + 4 > self.width:
                val_str = val_str[:self.width - len(key_txt) - 5] + "..."
            
            self.stdscr.addstr(y, len(key_txt) + 4, val_str, curses.color_pair(PAIR_SILVER))
            y += 1
            
        # Isotope Indicator
        iso_path = os.path.join(self.elements[self.selected_idx]['dir'], "isotopes.json")
        if os.path.exists(iso_path):
            self.stdscr.addstr(self.height-3, 2, "[ISOTOPES: AVAILABLE]", curses.color_pair(PAIR_BRASS))

    def draw_drawer(self):
        """Draws the 'Operations Drawer' overlay at the bottom."""
        drawer_height = 8
        start_y = self.height - drawer_height
        
        # Draw background block
        for y in range(start_y, self.height):
            self.stdscr.addstr(y, 0, " " * self.width, curses.color_pair(PAIR_ALERT))
            
        # Border line
        self.stdscr.addstr(start_y, 0, "▄" * self.width, curses.color_pair(PAIR_RED))
        
        # Menu Options
        options = [" [S]earch ", " [C]ompare ", " [F]usion Sim ", " [E]xit Drawer "]
        for i, opt in enumerate(options):
            self.stdscr.addstr(start_y + 1 + i, 2, opt, curses.color_pair(PAIR_ALERT) | curses.A_BOLD)

    def draw_search(self):
        """Draws search bar overlay."""
        self.stdscr.addstr(self.height-3, 2, f"SEARCH: {self.search_buffer}_", curses.color_pair(PAIR_BRASS))

    def loop(self):
        while True:
            self.stdscr.erase()
            
            # --- RENDER STACK ---
            self.draw_header()
            
            if self.view_mode == "BROWSE":
                self.draw_list()
            elif self.view_mode == "INSPECT":
                self.draw_inspector()
            
            if self.drawer_open:
                self.draw_drawer()

            if self.view_mode == "SEARCH":
                self.draw_search()

            # --- INPUT HANDLING ---
            c = self.stdscr.getch()

            # Global Quit
            if c == ord('q') and not self.view_mode == "SEARCH":
                break

            # Search Input Logic
            if self.view_mode == "SEARCH":
                if c == 10: # Enter
                    # Execute Search
                    target = self.search_buffer.lower()
                    for i, el in enumerate(self.elements):
                        if target in el['name'].lower() or target == str(el['z']):
                            self.selected_idx = i
                            self.scroll_idx = i
                            break
                    self.view_mode = "BROWSE"
                    self.drawer_open = False
                    self.search_buffer = ""
                elif c == 27: # ESC
                    self.view_mode = "BROWSE"
                    self.search_buffer = ""
                elif c == 127: # Backspace
                    self.search_buffer = self.search_buffer[:-1]
                elif 32 <= c <= 126:
                    self.search_buffer += chr(c)
                continue

            # Navigation
            if c == curses.KEY_UP:
                if self.view_mode == "BROWSE":
                    self.selected_idx = max(0, self.selected_idx - 1)
            elif c == curses.KEY_DOWN:
                if self.view_mode == "BROWSE":
                    self.selected_idx = min(len(self.elements) - 1, self.selected_idx + 1)
            
            # Context Actions
            elif c == 10: # ENTER
                if self.drawer_open:
                    pass # Menu selection logic todo
                else:
                    if self.view_mode == "BROWSE":
                        self.view_mode = "INSPECT"
                    elif self.view_mode == "INSPECT":
                        self.view_mode = "BROWSE"
            
            elif c == ord('o'): # Open Drawer
                self.drawer_open = not self.drawer_open
            
            # Drawer Shortcuts
            if self.drawer_open:
                if c == ord('s'):
                    self.view_mode = "SEARCH"
                    # Keep drawer visible or hide it? Let's hide to show search bar
                    self.drawer_open = False 
                elif c == ord('e'):
                    self.drawer_open = False

            # Refresh
            self.stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(TERM_TUI)
