import curses
from curses import textpad
import json
import os
import time
import textwrap
import random

# --- CONFIGURATION ---
REPO_DIR = "TERM_Repository"

# Color Pair IDs
PAIR_RED = 1
PAIR_BRASS = 2
PAIR_SILVER = 3
PAIR_GREY = 4
PAIR_ALERT = 5     # Black on Red (Header/Menu)
PAIR_REACTION = 6  # White on Red (Fusion Flash)
PAIR_ATOM = 7      # Cyan/Blue-ish for electron visual (Optional, using Cyan if avail)

class TERM_TUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        self.elements = self.load_data()
        
        # Navigation State
        self.scroll_idx = 0
        self.selected_idx = 0
        self.view_mode = "BROWSE" 
        self.drawer_open = False
        self.search_buffer = ""
        
        # Feature State
        self.compare_a = None 
        self.compare_b = None
        self.fusion_result = None
        
        # Init Colors
        curses.start_color()
        curses.use_default_colors()
        try:
            curses.init_pair(PAIR_RED, 196, -1)     
            curses.init_pair(PAIR_BRASS, 220, -1)   
            curses.init_pair(PAIR_SILVER, 255, -1)  
            curses.init_pair(PAIR_GREY, 240, -1)    
            curses.init_pair(PAIR_ALERT, curses.COLOR_BLACK, 196) 
            curses.init_pair(PAIR_REACTION, curses.COLOR_WHITE, 196)
            curses.init_pair(PAIR_ATOM, curses.COLOR_CYAN, -1)
        except:
            # Fallback
            curses.init_pair(PAIR_RED, curses.COLOR_RED, -1)
            curses.init_pair(PAIR_BRASS, curses.COLOR_YELLOW, -1)
            curses.init_pair(PAIR_SILVER, curses.COLOR_WHITE, -1)
            curses.init_pair(PAIR_GREY, curses.COLOR_MAGENTA, -1)
            curses.init_pair(PAIR_ALERT, curses.COLOR_BLACK, curses.COLOR_RED)
            curses.init_pair(PAIR_REACTION, curses.COLOR_WHITE, curses.COLOR_RED)

        curses.curs_set(0)
        self.loop()

    def safe_addstr(self, y, x, string, attr=0):
        try:
            if y >= self.height or x >= self.width: return
            if x + len(string) > self.width:
                string = string[:self.width - x]
            if y == self.height - 1 and x + len(string) == self.width:
                string = string[:-1]
            self.stdscr.addstr(y, x, string, attr)
        except curses.error:
            pass

    def load_data(self):
        data = []
        if not os.path.exists(REPO_DIR): return []
        dirs = sorted([d for d in os.listdir(REPO_DIR) if os.path.isdir(os.path.join(REPO_DIR, d))])
        for d in dirs:
            try:
                parts = d.split('_')
                z = int(parts[0])
                name = parts[1]
                data.append({"z": z, "name": name, "dir": os.path.join(REPO_DIR, d)})
            except: pass
        return sorted(data, key=lambda x: x['z'])

    def get_details(self, index):
        if index is None or index >= len(self.elements): return None
        path = os.path.join(self.elements[index]['dir'], "profile.json")
        try:
            with open(path, 'r') as f: return json.load(f)
        except: return None

    # --- DRAWING MODULES ---

    def draw_header(self):
        title = " T.E.R.M. v1.5 "
        self.safe_addstr(0, 0, " " * self.width, curses.color_pair(PAIR_ALERT))
        start_x = max(0, (self.width // 2) - (len(title) // 2))
        self.safe_addstr(0, start_x, title, curses.color_pair(PAIR_ALERT) | curses.A_BOLD)

    def draw_list(self):
        max_rows = self.height - 2
        if self.selected_idx < self.scroll_idx:
            self.scroll_idx = self.selected_idx
        elif self.selected_idx >= self.scroll_idx + max_rows:
            self.scroll_idx = self.selected_idx - max_rows + 1

        visible = self.elements[self.scroll_idx : self.scroll_idx + max_rows]

        for i, el in enumerate(visible):
            row_y = 1 + i
            style = curses.color_pair(PAIR_SILVER)
            prefix = "  "
            
            # Selection Highlight
            if self.scroll_idx + i == self.selected_idx:
                style = curses.color_pair(PAIR_ALERT) | curses.A_BOLD
                prefix = "> "
            
            # Compare Selection Logic
            if self.compare_a == (self.scroll_idx + i):
                prefix = "A "
                style = curses.color_pair(PAIR_BRASS) | curses.A_REVERSE

            line = f"{prefix}{el['z']:03d} {el['name'].upper()}"
            
            iso_path = os.path.join(el['dir'], "isotopes.json")
            if os.path.exists(iso_path):
                pad = self.width - len(line) - 2
                if pad > 0: line += " " * pad + "•"
            
            self.safe_addstr(row_y, 0, line, style)

    def draw_inspector(self):
        data = self.get_details(self.selected_idx)
        if not data: return

        self.stdscr.attron(curses.color_pair(PAIR_BRASS))
        try: textpad.rectangle(self.stdscr, 1, 0, self.height-2, self.width-1)
        except: pass
        self.stdscr.attroff(curses.color_pair(PAIR_BRASS))

        name = data.get("name", "Unknown").upper()
        self.safe_addstr(1, 2, f" {name} ", curses.color_pair(PAIR_RED) | curses.A_BOLD)

        props = data.get("properties", {})
        y = 3
        
        # Data Visualizer: Electron Shells (Text Based)
        config = props.get("electron_configuration", "")
        if config:
            self.safe_addstr(y, 2, "CONFIG:", curses.color_pair(PAIR_GREY))
            self.safe_addstr(y, 10, config, curses.color_pair(PAIR_ATOM))
            y += 2

        keys = ['standard_atomic_weight', 'phase', 'density', 'melting_point']
        for k in keys + [x for x in props.keys() if x not in keys and x != "electron_configuration"]:
            if k in props and y < self.height - 3:
                val = str(props[k])
                label = k.replace("_", " ").title() + ":"
                self.safe_addstr(y, 2, label, curses.color_pair(PAIR_GREY) | curses.A_BOLD)
                
                wrap_w = max(10, self.width - 4)
                lines = textwrap.wrap(val, wrap_w)
                for l in lines:
                    if y >= self.height - 3: break
                    self.safe_addstr(y+1, 4, l, curses.color_pair(PAIR_SILVER))
                    y += 1
                y += 1

    def draw_compare(self):
        """Side-by-side comparison with fuzzy matching."""
        d1 = self.get_details(self.compare_a)
        d2 = self.get_details(self.compare_b)
        
        # If data is missing, show error
        if not d1 or not d2: 
            self.safe_addstr(self.height//2, 2, "DATA ERROR: SELECT 2 ELEMENTS", curses.color_pair(PAIR_RED))
            return

        mid_x = self.width // 2
        
        # Draw Separator
        for y in range(1, self.height-1):
            self.safe_addstr(y, mid_x, "│", curses.color_pair(PAIR_RED))

        def print_col(data, start_x, max_w):
            name = data.get("name", "??")[0:max_w]
            self.safe_addstr(1, start_x, name.upper(), curses.color_pair(PAIR_BRASS) | curses.A_BOLD)
            
            y = 3
            props = data.get("properties", {})
            
            # Fuzzy Search Targets
            targets = [
                ("MASS", ["weight", "mass"]),
                ("PHASE", ["phase", "state"]),
                ("DENSITY", ["density"]),
                ("MELT", ["melting"]),
                ("BOIL", ["boiling"]),
                ("CONFIG", ["electron", "config"])
            ]
            
            for label, keywords in targets:
                found_val = "-"
                # Search keys
                for k, v in props.items():
                    if any(kw in k for kw in keywords):
                        found_val = v
                        break
                
                self.safe_addstr(y, start_x, label, curses.color_pair(PAIR_GREY))
                
                # Truncate value
                val_str = str(found_val)
                if len(val_str) > max_w:
                    val_str = val_str[:max_w-1] + "…"
                
                self.safe_addstr(y+1, start_x, val_str, curses.color_pair(PAIR_SILVER))
                y += 3

        print_col(d1, 1, mid_x - 1)
        print_col(d2, mid_x + 1, mid_x - 2)

    def draw_fusion(self):
        if not self.fusion_result: return
        el1, el2, el_new = self.fusion_result
        cy = self.height // 2
        
        self.stdscr.attron(curses.color_pair(PAIR_BRASS))
        try: textpad.rectangle(self.stdscr, cy-4, 2, cy+4, self.width-3)
        except: pass
        self.stdscr.attroff(curses.color_pair(PAIR_BRASS))
        
        self.safe_addstr(cy-2, 4, "FUSION EVENT", curses.color_pair(PAIR_RED) | curses.A_BOLD)
        eq = f"{el1['name']} + {el2['name']}"
        self.safe_addstr(cy, 4, eq, curses.color_pair(PAIR_SILVER))
        
        res_txt = f"{el_new['name'].upper()} ({el_new['z']})" if el_new else "UNSTABLE / UNKNOWN"
        self.safe_addstr(cy+2, 4, res_txt, curses.color_pair(PAIR_REACTION) | curses.A_BOLD)

    def draw_drawer(self):
        dh = 6
        sy = max(0, self.height - dh)
        for y in range(sy, self.height):
            self.safe_addstr(y, 0, " " * self.width, curses.color_pair(PAIR_ALERT))
        self.safe_addstr(sy, 0, "▄" * self.width, curses.color_pair(PAIR_RED))
        
        opts = ["[S]earch", "[C]ompare", "[F]usion", "[E]xit"]
        for i, opt in enumerate(opts):
            self.safe_addstr(sy + 1 + i, 2, opt, curses.color_pair(PAIR_ALERT) | curses.A_BOLD)

    # --- EVENT LOOP ---

    def run_fusion(self):
        if len(self.elements) < 2: return
        e1 = random.choice(self.elements)
        e2 = random.choice(self.elements)
        new_z = e1['z'] + e2['z']
        res = next((e for e in self.elements if e['z'] == new_z), None)
        self.fusion_result = (e1, e2, res)
        self.view_mode = "FUSION"

    def loop(self):
        while True:
            self.stdscr.erase()
            
            self.draw_header()
            
            if self.view_mode == "BROWSE": self.draw_list()
            elif self.view_mode == "INSPECT": self.draw_inspector()
            elif self.view_mode == "FUSION": self.draw_fusion()
            elif self.view_mode == "COMPARE_VIEW": self.draw_compare()
            
            if self.drawer_open: self.draw_drawer()
            if self.view_mode == "SEARCH": 
                self.safe_addstr(self.height-1, 0, f"SEARCH: {self.search_buffer}", curses.color_pair(PAIR_BRASS))

            try: c = self.stdscr.getch()
            except: break

            if c == ord('q') and self.view_mode == "BROWSE": break

            # Search
            if self.view_mode == "SEARCH":
                if c == 10: 
                    target = self.search_buffer.lower()
                    for i, el in enumerate(self.elements):
                        if target in el['name'].lower() or str(el['z']) == target:
                            self.selected_idx = i
                            self.scroll_idx = i
                            break
                    self.view_mode = "BROWSE"
                    self.search_buffer = ""
                elif c == 27: self.view_mode = "BROWSE"
                elif c in [127, curses.KEY_BACKSPACE]: self.search_buffer = self.search_buffer[:-1]
                elif 32 <= c <= 126: self.search_buffer += chr(c)
                continue

            # Navigation
            if c == curses.KEY_UP and self.view_mode == "BROWSE":
                self.selected_idx = max(0, self.selected_idx - 1)
            elif c == curses.KEY_DOWN and self.view_mode == "BROWSE":
                self.selected_idx = min(len(self.elements)-1, self.selected_idx + 1)
            
            # Action (Enter)
            elif c == 10:
                if self.view_mode == "BROWSE":
                    if self.compare_a is not None:
                        # Second selection made, trigger view
                        self.compare_b = self.selected_idx
                        self.view_mode = "COMPARE_VIEW"
                        # DO NOT clear self.compare_a here! Wait until exit.
                    else:
                        self.view_mode = "INSPECT"
                elif self.view_mode in ["INSPECT", "FUSION"]:
                    self.view_mode = "BROWSE"
                elif self.view_mode == "COMPARE_VIEW":
                    # Exit compare view, NOW we clear state
                    self.view_mode = "BROWSE"
                    self.compare_a = None
                    self.compare_b = None

            # Drawer
            elif c == ord('o'): self.drawer_open = not self.drawer_open
            
            if self.drawer_open:
                if c == ord('s'): 
                    self.view_mode = "SEARCH"; self.drawer_open = False
                elif c == ord('f'): 
                    self.run_fusion(); self.drawer_open = False
                elif c == ord('c'):
                    # Start Compare Sequence
                    self.compare_a = self.selected_idx
                    self.drawer_open = False
                    # Remains in BROWSE to pick element B
                elif c == ord('e'): 
                    self.drawer_open = False

            self.stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(TERM_TUI)
