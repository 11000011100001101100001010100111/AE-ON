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
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) TERM_Bot/4.0'}
        
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)

    def clean_text(self, text):
        if not text: return ""
        text = re.sub(r'\[.*?\]', '', text) 
        text = text.replace('\xa0', ' ').replace('\u200b', '')
        return text.strip()

    def safe_get(self, url):
        try:
            return requests.get(url, headers=self.headers, timeout=10)
        except: return None

    def fetch_master_index(self):
        print(f"[*] Connecting to Master Index...")
        response = self.safe_get(self.master_list_url)
        if not response: return

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'wikitable'}) 
        rows = table.find_all('tr')[1:] 
        
        print("[*] Updating Profiles & Fetching Descriptions...")

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

                print(f"[>] Updating {name}...")
                self.update_profile(name, element_url, element_dir)
                time.sleep(0.5) 

            except Exception as e:
                print(f" [!] Error on {raw_z}: {e}")

    def update_profile(self, name, url, save_dir):
        """Fetches profile + NEW Summary extraction."""
        response = self.safe_get(url)
        if not response: return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Parse Infobox (Existing Logic)
        infobox = soup.find('table', {'class': 'infobox'})
        properties = {}
        if infobox:
            for tr in infobox.find_all('tr'):
                th = tr.find('th')
                td = tr.find('td')
                if th and td:
                    key = self.clean_text(th.text).lower().replace(" ", "_")
                    val = self.clean_text(td.text)
                    if any(x in key for x in ['weight', 'mass', 'config', 'electron', 'melting', 'boiling', 'density', 'phase']):
                        properties[key] = val

        # 2. NEW: Fetch Summary (First non-empty paragraph)
        summary_text = "No description available."
        # Logic: Find the first <p> that isn't empty and doesn't just contain coordinates/metadata
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            txt = self.clean_text(p.text)
            if len(txt) > 50: # Arbitrary filter to skip "Coordinates:..." lines
                summary_text = txt
                break

        # 3. Merge & Save
        profile_data = {
            "name": name, 
            "url": url, 
            "summary": summary_text, # <--- NEW FIELD
            "properties": properties
        }
        
        self.save_asset(save_dir, "profile.json", profile_data)

    def save_asset(self, directory, filename, data):
        path = os.path.join(directory, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    bot = TERM_Harvester()
    bot.fetch_master_index()
