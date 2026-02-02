import os

# THE CLEAN SOURCE CODE (CLIP 042 ARCHITECTURE)
code = r'''import sys, os, time, threading, readline, atexit, shutil, curses
from datetime import datetime
from core import system, gitter, power, birdsong, refract
from meteor import station
from nexus import cart_loader, man

class NexusShell:
    def __init__(self):
        self.active = True
        self.chronicle = []
        self.max_history = 500
        self.slip_offset = 0
        self.input_buffer = ""
        self.dirty_deck = True
        
        # SYSTEMS
        self.sys_core = system.AeonLattice()
        self.wx_station = station.WeatherStation()
        self.diplomat = gitter.Diplomat()
        self.pwr_core = power.PowerCore()
        self.refractor = refract.GemRefract()
        self.cart_loader = cart_loader.CartridgeLoader()
        self.cartridges = self.cart_loader.scan_and_load()
        
        try: self.birdsong = birdsong.Birdsong(); self.crypto_active = True
        except: self.crypto_active = False

        self.hist_file = os.path.join(os.path.expanduser("~"), ".nexus_history")
        try: readline.read_history_file(self.hist_file)
        except: pass

    def log(self, text):
        for line in text.split('\n'):
            if line.strip(): self.chronicle.append(line)
        if len(self.chronicle) > self.max_history:
            self.chronicle = self.chronicle[-self.max_history:]
        self.dirty_deck = True

    def get_modulated_view(self, height):
        total = len(self.chronicle)
        end = total - self.slip_offset
        start = max(0, end - height)
        slice_data = self.chronicle[start:end]
        return slice_data, start

    def draw_header(self, stdscr, cols):
        now = datetime.now()
        
        # CYCLE DELTA (42.13m)
        cycle_len_sec = 42.34 * 60 
        fence_threshold_min = 42.13
        curr_time = time.time()
        pos_in_cycle_sec = curr_time % cycle_len_sec
        cycle_delta = pos_in_cycle_sec / 60.0
        
        if cycle_delta > fence_threshold_min:
            delta_str = "φ [||]" 
        else:
            delta_str = f"φ {cycle_delta:05.2f}"

        zn_cycle = f"Zn[30].{now.strftime('%j')}.{now.strftime('%H%M')}"
        lvl, st = self.pwr_core.get_status_string()
        
        try:
            # Color Pairs (Setup in main loop)
            C_RED = curses.color_pair(1)
            C_BRASS = curses.color_pair(2) | curses.A_BOLD
            C_SILVER = curses.color_pair(3)
            C_CYAN = curses.color_pair(4)
            C_BAT = C_RED if st == "CRITICAL" else C_SILVER
            cart_str = f"C:{len(self.cartridges)}"

            stdscr.move(0, 0)
            stdscr.clrtoeol()
            
            stdscr.addstr("┌──[ ", C_RED)
            stdscr.addstr("Æ-ON", C_SILVER)
            stdscr.addstr(" ]", C_RED)
            
            stdscr.addstr("──[ ", C_RED)
            stdscr.addstr(zn_cycle, C_BRASS)
            stdscr.addstr(" ]", C_RED)
            
            stdscr.addstr("──[ ", C_RED)
            stdscr.addstr(delta_str, C_BRASS)
            stdscr.addstr(" ]", C_RED)
            
            stdscr.addstr("──[ ", C_RED)
            stdscr.addstr(f"BAT:{lvl}%", C_BAT)
            stdscr.addstr(" ]", C_RED)
            
            stdscr.addstr("──[ ", C_RED)
            stdscr.addstr(cart_str, C_CYAN)
            stdscr.addstr(" ]──┐", C_RED)
        except: pass

    def draw_deck(self, stdscr, rows, cols):
        stdscr.erase()
        self.draw_header(stdscr, cols)
        
        # FOOTER
        ft_line = "─" * (cols - 12)
        try:
            stdscr.addstr(rows-2, 0, f"└──[ ", curses.color_pair(1))
            stdscr.addstr("NEXUS", curses.color_pair(4))
            stdscr.addstr(f" ]{ft_line}┘", curses.color_pair(1))
        except: pass

        # PROMPT
        prompt_char = ">>" if self.slip_offset == 0 else "<<"
        try:
            stdscr.addstr(rows-1, 0, f"{prompt_char} ", curses.color_pair(1))
            stdscr.addstr(self.input_buffer, curses.color_pair(3))
        except: pass

        # CHRONICLE
        vp_height = rows - 5 
        view_data, start_idx = self.get_modulated_view(vp_height)
        
        start_row = 2
        for i, line in enumerate(view_data):
            if not line: continue
            
            abs_id = start_idx + i 
            id_tag = f"[{abs_id:03}]"
            
            color = curses.color_pair(3)
            if self.slip_offset == 0 and i == len(view_data)-1:
                color = curses.color_pair(2)
            
            try:
                stdscr.addstr(start_row + i, 1, id_tag, curses.color_pair(3))
                stdscr.addstr("│", curses.color_pair(1))
                stdscr.addstr(f" {line[:cols-10]}", color)
            except: pass

    def handle_command(self, cmd_raw):
        self.log(f"> {cmd_raw.upper()}")
        parts = cmd_raw.split(" ")
        cmd = parts[0].lower()
        
        if cmd in ["exit", "salud"]: self.active = False
        elif cmd == "slip": self.slip_offset += int(parts[1]) if len(parts)>1 else 10; self.dirty_deck = True
        elif cmd == "push": self.slip_offset = max(0, self.slip_offset - (int(parts[1]) if len(parts)>1 else 10)); self.dirty_deck = True
        elif cmd == "live": self.slip_offset = 0; self.dirty_deck = True
        elif cmd == "sys":
            self.log(f"KERNEL: OPTIMAL | CORE: AeonLattice")
            self.log(f"CARTS:  {len(self.cartridges)}")
        
        elif cmd in ["save", "help", "refract", "enc", "dec", "signal", "link", "meteor", "slap"] or cmd in self.cartridges:
            curses.endwin()
            try:
                if cmd == "save":
                    ch = self.diplomat.get_status()
                    if ch:
                        print("CHANGES:"); [print(f" {c}") for c in ch]; print("")
                        m = input("MSG: ").strip()
                        if m: r=self.diplomat.execute_save(m); print(f"SYNC: {r}"); self.log(f"SYNC: {r}")
                    else: print("CLEAN.")
                elif cmd == "help":
                    if len(parts)>1: man.open_manual(parts[1], self.cartridges)
                    else: man.show_index(self.cartridges)
                elif cmd == "refract": self.refractor.generate_seed()
                elif cmd == "meteor" or cmd == "slap": print(self.wx_station.slap_data()); self.log(self.wx_station.slap_data())
                elif cmd == "signal": self.refractor.write_signal("ARCHX", " ".join(parts[1:])); self.log("SENT.")
                elif cmd in self.cartridges: self.cartridges[cmd].run(parts[1:])
                
                input("\n[PRESS ENTER]")
            except Exception as e:
                print(f"ERR: {e}")
                input("[PRESS ENTER]")
            
            self.stdscr = curses.initscr()
            curses.noecho(); curses.cbreak(); self.stdscr.keypad(True); self.setup_colors()
            self.dirty_deck = True

    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_WHITE, -1)
        curses.init_pair(4, curses.COLOR_CYAN, -1)

    def main_loop(self, stdscr):
        self.stdscr = stdscr
        self.setup_colors()
        curses.curs_set(1)
        
        stdscr.nodelay(True) 
        stdscr.timeout(10) # 10ms Polling
        
        self.log("System Online. Latency Optimized.")
        last_hum_time = 0
        
        while self.active:
            rows, cols = stdscr.getmaxyx()
            
            if self.dirty_deck:
                self.draw_deck(stdscr, rows, cols)
                stdscr.refresh()
                self.dirty_deck = False
            
            elif time.time() - last_hum_time > 0.1:
                self.draw_header(stdscr, cols)
                try: stdscr.move(rows-1, len(self.input_buffer) + 3)
                except: pass
                stdscr.refresh()
                last_hum_time = time.time()

            try: key = stdscr.getch()
            except: key = -1
            
            if key != -1:
                self.dirty_deck = True
                if key == 10 or key == 13:
                    self.handle_command(self.input_buffer.strip())
                    self.input_buffer = ""
                elif key == 27:
                    self.active = False
                elif key == curses.KEY_BACKSPACE or key == 127:
                    self.input_buffer = self.input_buffer[:-1]
                elif 32 <= key <= 126:
                    self.input_buffer += chr(key)

    def ignite(self):
        curses.wrapper(self.main_loop)

if __name__ == "__main__":
    shell = NexusShell()
    shell.ignite()
'''

print("REPAIRING SHELL...")
with open('nexus/shell.nxs', 'w') as f:
    f.write(code.strip())
print("REPAIR COMPLETE. REBOOTING.")
