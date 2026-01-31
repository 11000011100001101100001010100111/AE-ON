import os
import requests
from bs4 import BeautifulSoup
import json
import re
import time
import sys

# ANSI Colors for the Live Dashboard
C_RESET = "\033[0m"
C_RED = "\033[38;5;196m"
C_BRASS = "\033[38;5;220m"
C_GREEN = "\033[38;5;46m"
C_GREY = "\033[38;5;240m"
C_CLEAR = "\033[H\033[J" # Clear Screen code

class TERM_Harvester:
    def __init__(self):
        self.root_dir = "TERM_Repository"
        self.base_url = "https://en.wikipedia.org"
        self.master_list_url = "https://en.wikipedia.org/wiki/List_of_chemical_elements"
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) TERM_Bot/5.0'}
        self.states = {} # Tracks status: pending, working, done, error
        self.total_elements = 0
        self.processed_count = 0
        
        if not os.path.exists(self.root_dir): os.makedirs(self.root_dir)
        self.init_states()

    # --- DASHBOARD VISUALS ---
    def init_states(self):
        # Map Z to Symbol for the dashboard grid
        self.element_map = {
             1:'H',   2:'He',  3:'Li',  4:'Be',  5:'B',   6:'C',   7:'N',   8:'O',
             9:'F',  10:'Ne', 11:'Na', 12:'Mg', 13:'Al', 14:'Si', 15:'P',  16:'S',
            17:'Cl', 18:'Ar', 19:'K',  20:'Ca', 21:'Sc', 22:'Ti', 23:'V',  24:'Cr',
            25:'Mn', 26:'Fe', 27:'Co', 28:'Ni', 29:'Cu', 30:'Zn', 31:'Ga', 32:'Ge',
            33:'As', 34:'Se', 35:'Br', 36:'Kr', 37:'Rb', 38:'Sr', 39:'Y',  40:'Zr',
            41:'Nb', 42:'Mo', 43:'Tc', 44:'Ru', 45:'Rh', 46:'Pd', 47:'Ag', 48:'Cd',
            49:'In', 50:'Sn', 51:'Sb', 52:'Te', 53:'I',  54:'Xe', 55:'Cs', 56:'Ba',
            # Lanthanides
            57:'La', 58:'Ce', 59:'Pr', 60:'Nd', 61:'Pm', 62:'Sm', 63:'Eu', 64:'Gd',
            65:'Tb', 66:'Dy', 67:'Ho', 68:'Er', 69:'Tm', 70:'Yb', 71:'Lu',
            72:'Hf', 73:'Ta', 74:'W',  75:'Re', 76:'Os', 77:'Ir', 78:'Pt', 79:'Au',
            80:'Hg', 81:'Tl', 82:'Pb', 83:'Bi', 84:'Po', 85:'At', 86:'Rn', 87:'Fr',
            88:'Ra',
            # Actinides
            89:'Ac', 90:'Th', 91:'Pa', 92:'U',  93:'Np', 94:'Pu', 95:'Am', 96:'Cm',
            97:'Bk', 98:'Cf', 99:'Es',100:'Fm',101:'Md',102:'No',103:'Lr',
            104:'Rf',105:'Db',106:'Sg',107:'Bh',108:'Hs',109:'Mt',110:'Ds',111:'Rg',
            112:'Cn',113:'Nh',114:'Fl',115:'Mc',116:'Lv',117:'Ts',118:'Og'
        }
        for z in self.element_map: self.states[z] = 'pending'
        self.total_elements = len(self.element_map)

    def draw_dashboard(self, current_action="Initializing..."):
        sys.stdout.write(C_CLEAR)
        print(f"{C_RED}========================================{C_RESET}")
        print(f"{C_BRASS}   TERM HARVESTER v5.0 | DEEPNET{C_RESET}")
        print(f"{C_RED}========================================{C_RESET}")
        print(f" Status: {current_action}")
        print(f" Progress: [{self.processed_count}/{self.total_elements}]")
        print(f"{C_GREY}----------------------------------------{C_RESET}")

        # Portrait-optimized grid layout
        layout = [
            [1, 2], # H, He
            [3, 4, 5, 6, 7, 8, 9, 10], # Period 2
            [11,12,13,14,15,16,17,18], # Period 3
            [19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36], # Period 4
            [37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54], # Period 5
            [55,56, 57,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86], # Period 6 (w/ La placeholder)
            [87,88, 89,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118], # Period 7
            [], # Spacer
            [58,59,60,61,62,63,64,65,66,67,68,69,70,71], # Lanthanides
            [90,91,92,93,94,95,96,97,98,99,100,101,102,103] # Actinides
        ]

        for row in layout:
            line = ""
            for z in row:
                sym = self.element_map.get(z, '??')
                state = self.states.get(z, 'pending')
                
                color = C_GREY
                if state == 'working': color = C_BRASS
                elif state == 'done': color = C_GREEN
                elif state == 'error': color = C_RED
                
                # Pad symbol to 3 chars centered
                sym_pad = f"{sym:^3}"
                line += f"{C_GREY}[{color}{sym_pad}{C_GREY}]{C_RESET} "
            print(line)
            if not row: print("") # Print spacer line

        print(f"{C_RED}========================================{C_RESET}")
        sys.stdout.flush()

    # --- UTILITIES ---
    def clean_text(self, text):
        if not text: return ""
        text = re.sub(r'\[.*?\]', '', text) # Remove citations
        text = text.replace('\xa0', ' ').replace('\u200b', '')
        return text.strip()

    def safe_get(self, url):
        try: return requests.get(url, headers=self.headers, timeout=10)
        except: return None

    # --- CORE LOGIC ---
    def fetch_master_index(self):
        self.draw_dashboard("Connecting to Wikipedia...")
        response = self.safe_get(self.master_list_url)
        if not response:
            self.draw_dashboard("Connection Failed.")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'wikitable'}) 
        rows = table.find_all('tr')[1:] 
        
        self.draw_dashboard("Indexing Elements...")

        for row in rows:
            cols = row.find_all(['td', 'th'])
            if len(cols) < 3: continue
            raw_z = self.clean_text(cols[0].text)
            if not raw_z.isdigit(): continue

            try:
                atomic_num = int(raw_z)
                symbol = self.clean_text(cols[1].text)
                name_tag = cols[2].find('a')
                if not name_tag: continue
                
                name = self.clean_text(name_tag.text)
                element_url = self.base_url + name_tag['href']
                
                dir_name = f"{atomic_num:03d}_{name}"
                element_dir = os.path.join(self.root_dir, dir_name)
                if not os.path.exists(element_dir): os.makedirs(element_dir)

                # Update State & Draw
                self.states[atomic_num] = 'working'
                self.draw_dashboard(f"Harvesting {name}...")
                
                success = self.update_profile(name, element_url, element_dir)
                
                self.states[atomic_num] = 'done' if success else 'error'
                self.processed_count += 1
                time.sleep(0.2) # Rate limit

            except Exception as e:
                self.states[int(raw_z)] = 'error'
                self.processed_count += 1

        self.draw_dashboard("COMPLETE. Data secured.")

    def update_profile(self, name, url, save_dir):
        response = self.safe_get(url)
        if not response: return False
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. DEEPNET Infobox Scrape
        infobox = soup.find('table', {'class': 'infobox'})
        properties = {}
        if infobox:
            for tr in infobox.find_all('tr'):
                th = tr.find('th')
                td = tr.find('td')
                if th and td:
                    # Cleanup Key
                    key = self.clean_text(th.text).lower().replace(" ", "_")
                    key = re.sub(r'[^a-z0-9_]', '', key) # Keep only valid chars
                    
                    # Cleanup Value (Aggressive)
                    val = self.clean_text(td.text)
                    
                    # Filter out obviously bad keys/values
                    if len(key) > 2 and len(val) > 0 and "image" not in key and ".ogg" not in val:
                         properties[key] = val

        # 2. Fetch Summary
        summary_text = "No description available."
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            txt = self.clean_text(p.text)
            if len(txt) > 60: 
                summary_text = txt
                break

        # 3. Merge & Save
        profile_data = {
            "name": name, 
            "url": url, 
            "summary": summary_text,
            "properties": properties
        }
        
        path = os.path.join(save_dir, "profile.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=4, ensure_ascii=False)
        return True

if __name__ == "__main__":
    bot = TERM_Harvester()
    bot.fetch_master_index()
