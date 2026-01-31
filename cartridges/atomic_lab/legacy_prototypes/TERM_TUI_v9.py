import curses
from curses import textpad
import json
import os
import math
import textwrap
import random

# --- CONFIGURATION ---
REPO_DIR = "TERM_Repository"

# Color Pair IDs
PAIR_RED = 1
PAIR_BRASS = 2
PAIR_SILVER = 3
PAIR_GREY = 4
PAIR_ALERT = 5     
PAIR_REACTION = 6  
PAIR_ELECTRON = 7  
PAIR_NUCLEUS = 8   

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
        self.inspector_scroll = 0 # New scroll state for deep data
        
        # Feature State
        self.compare_a = None 
        self.compare_b = None
        self.fusion_result = None
        self.lab_z = 1; self.lab_n = 0; self.lab_e = 1
        
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
            curses.init_pair(PAIR_ELECTRON, 51, -1) 
            curses.init_pair(PAIR_NUCLEUS, 15, -1)  
        except:
            # Fallback
            curses.init_pair(PAIR_RED, curses.COLOR_RED, -1)
            curses.init_pair(PAIR_BRASS, curses.COLOR_YELLOW, -1)
            curses.init_pair(PAIR_SILVER, curses.COLOR_WHITE, -1)
            curses.init_pair(PAIR_GREY, curses.COLOR_MAGENTA, -1)
            curses.init_pair(PAIR_ALERT, curses.COLOR_BLACK, curses.COLOR_RED)
            curses.init_pair(PAIR_REACTION, curses.COLOR_WHITE, curses.COLOR_RED)
            curses.init_pair(PAIR_ELECTRON, curses.COLOR_CYAN, -1)
            curses.init_pair(PAIR_NUCLEUS, curses.COLOR_WHITE, -1)

        curses.curs_set(0)
        self.loop()

    def safe_addstr(self, y, x, string, attr=0):
        try:
            if y >= self.height or x >= self.width: return
            if x + len(string) > self.width: string = string[:self.width - x]
            if y == self.height - 1 and x + len(string) == self.width: string = string[:-1]
            self.stdscr.addstr(y, x, string, attr)
        except curses.error: pass

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

    def get_prop_fuzzy(self, props, keys):
        for k, v in props.items():
            if any(x in k for x in keys): return v, k
        return None, None

    # --- DRAWING ---
    def draw_header(self):
        title = " T.E.R.M. v1.9 [DEEP DATA] "
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
            if self.scroll_idx + i == self.selected_idx:
                style = curses.color_pair(PAIR_ALERT) | curses.A_BOLD
                prefix = "> "
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
        props = data.get("properties", {})
        z = self.elements[self.selected_idx]['z']

        # Box
        self.stdscr.attron(curses.color_pair(PAIR_BRASS))
        try: textpad.rectangle(self.stdscr, 1, 0, self.height-2, self.width-1)
        except: pass
        self.stdscr.attroff(curses.color_pair(PAIR_BRASS))

        # Header
        name = data.get("name", "Unknown").upper()
        self.safe_addstr(1, 2, f" {z:03d} | {name} ", curses.color_pair(PAIR_RED) | curses.A_BOLD)
        y = 3
        
        # Primary Stats
        mass, mk = self.get_prop_fuzzy(props, ['weight', 'mass'])
        self.safe_addstr(y, 2, "MASS:", curses.color_pair(PAIR_GREY)|curses.A_BOLD)
        self.safe_addstr(y, 8, str(mass), curses.color_pair(PAIR_SILVER))
        y += 1
        
        config, ck = self.get_prop_fuzzy(props, ['config', 'electron_con'])
        if config:
            self.safe_addstr(y, 2, "CONFIG:", curses.color_pair(PAIR_GREY)|curses.A_BOLD)
            self.safe_addstr(y, 10, str(config), curses.color_pair(PAIR_ELECTRON))
            y += 2

        # Description
        summary = data.get("summary", "No data.")
        lines = textwrap.wrap(summary, self.width - 4)
        for i, line in enumerate(lines):
            if y >= self.height - 6: break # Reserve space for deep data
            self.safe_addstr(y, 2, line, curses.color_pair(PAIR_SILVER))
            y += 1
        y += 1
        
        # DEEP DATA SCROLLER
        self.safe_addstr(y, 1, "─"* (self.width-2), curses.color_pair(PAIR_BRASS))
        self.safe_addstr(y, 2, " DEEP DATA (↑/↓ to scroll) ", curses.color_pair(PAIR_BRASS)|curses.A_REVERSE)
        y += 1
        
        # Filter keys already shown
        shown_keys = [mk, ck]
        deep_keys = sorted([k for k in props.keys() if k not in shown_keys and k is not None])
        
        avail_rows = (self.height - 2) - y
        if avail_rows > 0 and deep_keys:
            # Scroll logic
            if self.inspector_scroll > len(deep_keys) - avail_rows:
                self.inspector_scroll = max(0, len(deep_keys) - avail_rows)
                
            visible_keys = deep_keys[self.inspector_scroll : self.inspector_scroll + avail_rows]
            
            for i, key in enumerate(visible_keys):
                val = str(props[key])
                label = key.replace("_", " ").title()
                line = f"{label}: {val}"
                if len(line) > self.width - 4: line = line[:self.width-5] + "…"
                self.safe_addstr(y+i, 2, line, curses.color_pair(PAIR_GREY))

    def draw_compare(self):
        d1 = self.get_details(self.compare_a)
        d2 = self.get_details(self.compare_b)
        if not d1 or not d2: return
        mid_x = self.width // 2
        for y in range(1, self.height-1): self.safe_addstr(y, mid_x, "│", curses.color_pair(PAIR_RED))

        def print_col(data, z, start_x, max_w):
            name = data.get("name", "??")
            header = f"{z} {name.upper()}"
            self.safe_addstr(1, start_x, header[:max_w], curses.color_pair(PAIR_BRASS) | curses.A_BOLD)
            y = 3
            props = data.get("properties", {})
            targets = [("MASS", ["weight", "mass"]), ("PHASE", ["phase", "state"]),
                       ("DENSITY", ["density"]), ("MELT", ["melting"]),
                       ("BOIL", ["boiling"]), ("CONFIG", ["config", "electron"]),
                       ("DISCOVERED", ["discovery", "discoverer"])] # Added discovery
            for label, keywords in targets:
                val, _ = self.get_prop_fuzzy(props, keywords)
                self.safe_addstr(y, start_x, label, curses.color_pair(PAIR_GREY))
                if len(str(val)) > max_w: val = str(val)[:max_w-1] + "…"
                self.safe_addstr(y+1, start_x, str(val), curses.color_pair(PAIR_SILVER))
                y += 3
        print_col(d1, self.elements[self.compare_a]['z'], 1, mid_x - 1)
        print_col(d2, self.elements[self.compare_b]['z'], mid_x + 1, mid_x - 2)

    def draw_fusion(self):
        if not self.fusion_result: return
        el1, el2, el_new = self.fusion_result
        cy = self.height // 2
        self.stdscr.attron(curses.color_pair(PAIR_BRASS))
        try: textpad.rectangle(self.stdscr, cy-4, 2, cy+4, self.width-3)
        except: pass
        self.stdscr.attroff(curses.color_pair(PAIR_BRASS))
        self.safe_addstr(cy-2, 4, "FUSION EVENT DETECTED", curses.color_pair(PAIR_RED) | curses.A_BOLD)
        eq = f"{el1['name']} ({el1['z']}) + {el2['name']} ({el2['z']})"
        self.safe_addstr(cy, 4, eq, curses.color_pair(PAIR_SILVER))
        self.safe_addstr(cy+1, 4, "      \/      ", curses.color_pair(PAIR_BRASS))
        res_txt = f"{el_new['name'].upper()} ({el_new['z']})" if el_new else "UNSTABLE / UNKNOWN"
        self.safe_addstr(cy+2, 4, res_txt, curses.color_pair(PAIR_REACTION) | curses.A_BOLD)

    def draw_lab(self):
        cy = self.height // 2 - 2; cx = self.width // 2
        el_data = next((e for e in self.elements if e['z'] == self.lab_z), None)
        name = el_data['name'].upper() if el_data else f"UNKNOWN-{self.lab_z}"
        self.safe_addstr(1, 2, f"LABORATORY MODE", curses.color_pair(PAIR_RED) | curses.A_BOLD)
        mass_num = self.lab_z + self.lab_n; charge = self.lab_z - self.lab_e
        ratio = self.lab_n / self.lab_z if self.lab_z > 0 else 0
        stable = "STABLE"
        if self.lab_z > 83 or ratio < 1.0 or ratio > 1.6: stable = "UNSTABLE"
        if self.lab_z == 1 and self.lab_n == 0: stable = "STABLE"
        s_color = PAIR_SILVER if stable == "STABLE" else PAIR_RED
        self.safe_addstr(3, 2, f"ELEMENT: {name}", curses.color_pair(PAIR_BRASS))
        self.safe_addstr(4, 2, f"MASS:    {mass_num}", curses.color_pair(PAIR_SILVER))
        self.safe_addstr(5, 2, f"CHARGE:  {charge:+d}", curses.color_pair(PAIR_ELECTRON))
        self.safe_addstr(6, 2, f"STATUS:  {stable}", curses.color_pair(s_color) | curses.A_BOLD)
        nuc_str = f"[{self.lab_z}p|{self.lab_n}n]"
        self.safe_addstr(cy, cx - len(nuc_str)//2, nuc_str, curses.color_pair(PAIR_NUCLEUS) | curses.A_BOLD)
        rem_e = self.lab_e; shells = []
        for cap in [2, 8, 18, 32, 50]:
            if rem_e <= 0: break
            take = min(rem_e, cap); shells.append(take); rem_e -= take
        for i, count in enumerate(shells):
            radius = 3 + (i * 2)
            if count > 0:
                for e_idx in range(count):
                    theta = math.radians(e_idx * (360/count) + (i*45))
                    ex = cx + int(radius * 2 * math.cos(theta)); ey = cy + int(radius * math.sin(theta))
                    self.safe_addstr(ey, ex, "e", curses.color_pair(PAIR_ELECTRON))
        help_y = self.height - 4
        self.safe_addstr(help_y, 2, "CONTROLS:", curses.color_pair(PAIR_GREY))
        self.safe_addstr(help_y+1, 2, "←/→: Protons   ↑/↓: Neutrons", curses.color_pair(PAIR_SILVER))
        self.safe_addstr(help_y+2, 2, "[ / ]: Electrons   q: Exit Lab", curses.color_pair(PAIR_SILVER))

    def draw_drawer(self):
        dh = 6; sy = max(0, self.height - dh)
        for y in range(sy, self.height): self.safe_addstr(y, 0, " " * self.width, curses.color_pair(PAIR_ALERT))
        self.safe_addstr(sy, 0, "▄" * self.width, curses.color_pair(PAIR_RED))
        opts = ["[S]earch", "[C]ompare", "[F]usion", "[L]ab", "[E]xit"]
        for i, opt in enumerate(opts): self.safe_addstr(sy + 1 + i, 2, opt, curses.color_pair(PAIR_ALERT) | curses.A_BOLD)

    # --- LOOP ---
    def run_fusion(self):
        if len(self.elements) < 2: return
        e1 = random.choice(self.elements); e2 = random.choice(self.elements)
        new_z = e1['z'] + e2['z']
        res = next((e for e in self.elements if e['z'] == new_z), None)
        self.fusion_result = (e1, e2, res); self.view_mode = "FUSION"

    def loop(self):
        while True:
            self.stdscr.erase()
            self.draw_header()
            if self.view_mode == "BROWSE": self.draw_list()
            elif self.view_mode == "INSPECT": self.draw_inspector()
            elif self.view_mode == "FUSION": self.draw_fusion()
            elif self.view_mode == "COMPARE_VIEW": self.draw_compare()
            elif self.view_mode == "LAB": self.draw_lab()
            if self.drawer_open: self.draw_drawer()
            if self.view_mode == "SEARCH": self.safe_addstr(self.height-1, 0, f"SEARCH: {self.search_buffer}", curses.color_pair(PAIR_BRASS))

            try: c = self.stdscr.getch()
            except: break

            if c == ord('q') and self.view_mode == "BROWSE": break
            if c == ord('q') and self.view_mode == "LAB": self.view_mode = "BROWSE"; continue

            if self.view_mode == "SEARCH":
                if c == 10:
                    target = self.search_buffer.lower()
                    for i, el in enumerate(self.elements):
                        if target in el['name'].lower() or str(el['z']) == target:
                            self.selected_idx = i; self.scroll_idx = i; break
                    self.view_mode = "BROWSE"; self.search_buffer = ""
                elif c == 27: self.view_mode = "BROWSE"
                elif c in [127, curses.KEY_BACKSPACE]: self.search_buffer = self.search_buffer[:-1]
                elif 32 <= c <= 126: self.search_buffer += chr(c)
                continue

            if self.view_mode == "LAB":
                if c == curses.KEY_RIGHT: self.lab_z = min(118, self.lab_z + 1)
                elif c == curses.KEY_LEFT: self.lab_z = max(1, self.lab_z - 1)
                elif c == curses.KEY_UP: self.lab_n += 1
                elif c == curses.KEY_DOWN: self.lab_n = max(0, self.lab_n - 1)
                elif c == ord(']'): self.lab_e += 1
                elif c == ord('['): self.lab_e = max(0, self.lab_e - 1)
                continue

            # VIEW SPECIFIC NAVIGATION
            if self.view_mode == "BROWSE":
                if c == curses.KEY_UP: self.selected_idx = max(0, self.selected_idx - 1)
                elif c == curses.KEY_DOWN: self.selected_idx = min(len(self.elements)-1, self.selected_idx + 1)
            elif self.view_mode == "INSPECT":
                # Scroll deep data
                if c == curses.KEY_UP: self.inspector_scroll = max(0, self.inspector_scroll - 1)
                elif c == curses.KEY_DOWN: self.inspector_scroll += 1
            
            if c == 10:
                if self.view_mode == "BROWSE":
                    if self.compare_a is not None: self.compare_b = self.selected_idx; self.view_mode = "COMPARE_VIEW"
                    else: self.view_mode = "INSPECT"; self.inspector_scroll = 0 # Reset scroll
                elif self.view_mode in ["INSPECT", "FUSION"]: self.view_mode = "BROWSE"
                elif self.view_mode == "COMPARE_VIEW": self.view_mode = "BROWSE"; self.compare_a = None; self.compare_b = None

            elif c == ord('o'): self.drawer_open = not self.drawer_open
            
            if self.drawer_open:
                if c == ord('s'): self.view_mode = "SEARCH"; self.drawer_open = False
                elif c == ord('f'): self.run_fusion(); self.drawer_open = False
                elif c == ord('c'): self.compare_a = self.selected_idx; self.drawer_open = False
                elif c == ord('l'):
                    sel = self.elements[self.selected_idx]; self.lab_z = sel['z']
                    self.lab_n = int(sel['z'] * 1.1); self.lab_e = sel['z']
                    self.view_mode = "LAB"; self.drawer_open = False
                elif c == ord('e'): self.drawer_open = False

            self.stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(TERM_TUI)
