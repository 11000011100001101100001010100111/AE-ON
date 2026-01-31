import os
import requests
from bs4 import BeautifulSoup
import json
import re
import time

class TERM_Harvester:
    def __init__(self):
        self.root_dir = "TERM_Repository"
        self.base_url = "https://en.wikipedia.org"
        self.master_list_url = "https://en.wikipedia.org/wiki/List_of_chemical_elements"
        self.headers = {'User-Agent': 'TERM_Bot/2.0 (Asset_Builder)'}
        
        # Ensure root directory exists
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)
            print(f"[@] Created root repository: {self.root_dir}/")

    def clean_text(self, text):
        """Sanitizes text: removes citations [1], [a] and whitespace."""
        if not text: return None
        text = re.sub(r'\[.*?\]', '', text) 
        return text.strip()

    def save_asset(self, directory, filename, data):
        """Writes JSON payload to specific element folder."""
        path = os.path.join(directory, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"    [+] Saved asset: {filename}")

    def fetch_master_index(self):
        print(f"[*] Connecting to Master Index...")
        response = requests.get(self.master_list_url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Locate the main Wiki table
        table = soup.find('table', {'class': 'wikitable'}) 
        rows = table.find_all('tr')[1:] 
        
        for row in rows:
            cols = row.find_all(['td', 'th'])
            if len(cols) < 3: continue
            
            try:
                # 1. Parse Identity
                atomic_num = self.clean_text(cols[0].text)
                symbol = self.clean_text(cols[1].text)
                name_tag = cols[2].find('a')
                name = self.clean_text(name_tag.text)
                element_url = self.base_url + name_tag['href']
                
                # 2. Setup Directory: "001_Hydrogen"
                dir_name = f"{int(atomic_num):03d}_{name}"
                element_dir = os.path.join(self.root_dir, dir_name)
                
                # 3. Check Persistence (Don't repeat steps)
                if os.path.exists(element_dir):
                    print(f"[-] Directory exists for {name}. Skipping...")
                    continue
                
                os.makedirs(element_dir)
                print(f"\n[>] Processing {dir_name}...")

                # 4. Execute Subroutines
                self.process_profile(name, element_url, element_dir)
                self.process_isotopes(name, element_dir)
                
                # Polite Delay
                time.sleep(1.0) 

            except Exception as e:
                print(f" [!] CRITICAL ERROR on row: {e}")

    def process_profile(self, name, url, save_dir):
        """Subroutine A: Main Element Profile"""
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            infobox = soup.find('table', {'class': 'infobox'})
            
            profile_data = {"name": name, "url": url, "properties": {}}
            
            if infobox:
                for tr in infobox.find_all('tr'):
                    th = tr.find('th')
                    td = tr.find('td')
                    if th and td:
                        key = self.clean_text(th.text).lower().replace(" ", "_")
                        val = self.clean_text(td.text)
                        # Basic filtering for massive infoboxes
                        if any(x in key for x in ['weight', 'config', 'electron', 'melting', 'boiling', 'density', 'phase']):
                            profile_data["properties"][key] = val
            
            self.save_asset(save_dir, "profile.json", profile_data)
            
        except Exception as e:
            print(f"    [!] Profile Harvest Failed: {e}")

    def process_isotopes(self, name, save_dir):
        """Subroutine B: The Isotope Hunter"""
        # Logic: Construct standard Wiki URL for isotopes
        iso_url = f"{self.base_url}/wiki/Isotopes_of_{name}"
        
        try:
            response = requests.get(iso_url, headers=self.headers)
            
            # If the page doesn't exist, Wiki returns 404
            if response.status_code != 200:
                print(f"    [!] No specific Isotope page found at {iso_url}")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main isotope table (usually class 'wikitable')
            tables = soup.find_all('table', {'class': 'wikitable'})
            
            isotopes_list = []
            
            # Heuristic: The correct table usually has headers like "Nuclide", "Z", "N"
            target_table = None
            for t in tables:
                headers = [th.text.strip() for th in t.find_all('th')]
                if "Nuclide" in str(headers) or "symbol" in str(headers):
                    target_table = t
                    break
            
            if target_table:
                # Parse rows (Skip header)
                for row in target_table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    # Isotope tables are messy; complex rowspan logic is often needed.
                    # For V1, we grab the raw text of the first column (Symbol) and last (Abundance/Half-life)
                    # to ensure we at least capture the Nuclide designation.
                    if len(cols) > 1:
                        # This is a 'dumb' grab to ensure we get data. 
                        # A 'WikiRefiner' script is needed to parse specific columns later.
                        row_data = [self.clean_text(c.text) for c in cols]
                        isotopes_list.append(row_data)

            payload = {
                "source_url": iso_url,
                "raw_table_data": isotopes_list
            }
            
            self.save_asset(save_dir, "isotopes.json", payload)

        except Exception as e:
            print(f"    [!] Isotope Harvest Failed: {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    bot = TERM_Harvester()
    bot.fetch_master_index()
