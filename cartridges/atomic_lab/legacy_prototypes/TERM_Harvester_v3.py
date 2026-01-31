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
        # Updated User-Agent to look more like a standard browser to avoid blocks
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) TERM_Bot/3.0'}
        
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)

    def clean_text(self, text):
        if not text: return ""
        text = re.sub(r'\[.*?\]', '', text) 
        # Remove non-breaking spaces
        text = text.replace('\xa0', ' ').replace('\u200b', '')
        return text.strip()

    def safe_get(self, url):
        """Wrapper for requests to handle minor network hiccups."""
        try:
            return requests.get(url, headers=self.headers, timeout=10)
        except Exception as e:
            print(f"    [!] Network Error: {e}")
            return None

    def fetch_master_index(self):
        print(f"[*] Connecting to Master Index...")
        response = self.safe_get(self.master_list_url)
        if not response: return

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'wikitable'}) 
        rows = table.find_all('tr')[1:] 
        
        print("[*] Parsing rows...")

        for row in rows:
            cols = row.find_all(['td', 'th'])
            if len(cols) < 3: continue
            
            # --- FIX 1: Robust Row Validation ---
            # Ensure the first column is actually a number (Atomic Z)
            raw_z = self.clean_text(cols[0].text)
            if not raw_z.isdigit():
                continue

            try:
                atomic_num = int(raw_z)
                symbol = self.clean_text(cols[1].text)
                name_tag = cols[2].find('a')
                
                if not name_tag: continue
                
                name = self.clean_text(name_tag.text)
                element_url = self.base_url + name_tag['href']
                
                dir_name = f"{atomic_num:03d}_{name}"
                element_dir = os.path.join(self.root_dir, dir_name)
                
                if not os.path.exists(element_dir):
                    os.makedirs(element_dir)

                print(f"\n[>] {dir_name}")

                # Pass the soup object of the main page to the isotope hunter
                # so we don't have to request the page twice if we need to find links.
                main_page_soup = self.process_profile(name, element_url, element_dir)
                
                # Check if isotopes exist before trying to fetch
                if not os.path.exists(os.path.join(element_dir, "isotopes.json")):
                     self.process_isotopes(name, element_dir, main_page_soup)
                else:
                    print("    [-] Isotopes already exist.")

                time.sleep(0.5) 

            except Exception as e:
                print(f" [!] Error on row {raw_z}: {e}")

    def process_profile(self, name, url, save_dir):
        """Fetches profile and returns the Soup object for further use."""
        response = self.safe_get(url)
        if not response: return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        infobox = soup.find('table', {'class': 'infobox'})
        
        profile_data = {"name": name, "url": url, "properties": {}}
        
        if infobox:
            for tr in infobox.find_all('tr'):
                # --- FIX 2: Safe Infobox Traversal ---
                th = tr.find('th')
                td = tr.find('td')
                
                # Only proceed if BOTH tags exist
                if th and td:
                    key_text = th.text
                    val_text = td.text
                    
                    if key_text and val_text:
                        key = self.clean_text(key_text).lower().replace(" ", "_")
                        val = self.clean_text(val_text)
                        
                        if any(x in key for x in ['weight', 'config', 'electron', 'melting', 'boiling', 'density', 'phase']):
                            profile_data["properties"][key] = val
        
        self.save_asset(save_dir, "profile.json", profile_data)
        return soup

    def process_isotopes(self, name, save_dir, main_page_soup):
        """ Tries to find the isotope page via guessing, then via link hunting. """
        
        # Strategy A: Guess the URL
        iso_url = f"{self.base_url}/wiki/Isotopes_of_{name}"
        response = self.safe_get(iso_url)

        # Strategy B: If Guess fails, hunt for the link in the Main Page
        if not response or response.status_code == 404:
            # print(f"    [~] Standard URL failed. Hunting link in main page...")
            if main_page_soup:
                # Look for "Main article: Isotopes of X"
                # This is usually in a div with class 'hatnote' or similar
                for a in main_page_soup.find_all('a', href=True):
                    if "Isotopes_of" in a['href'] and name in a['href']:
                        iso_url = self.base_url + a['href']
                        # print(f"    [!] Found Isotope Link: {iso_url}")
                        response = self.safe_get(iso_url)
                        break
        
        if not response or response.status_code != 200:
            print(f"    [!] Could not locate Isotope table for {name}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        isotopes_list = []
        target_table = None

        # --- FIX 3: Loose Table Matching ---
        # Look for ANY table that mentions "Decay" or "Half-life" or "Symbol" in headers
        for t in tables:
            header_text = t.text[:500].lower() # Check first 500 chars
            if "nuclide" in header_text or "symbol" in header_text or "neutron" in header_text:
                target_table = t
                break
        
        if target_table:
            for row in target_table.find_all('tr')[1:]:
                cols = row.find_all(['td', 'th']) # Isotopes often use TH for the symbol
                if len(cols) > 1:
                    row_data = [self.clean_text(c.text) for c in cols]
                    isotopes_list.append(row_data)
            
            payload = {
                "source_url": iso_url,
                "raw_table_data": isotopes_list
            }
            self.save_asset(save_dir, "isotopes.json", payload)
        else:
            print(f"    [!] Page found, but no recognized table structure.")

    def save_asset(self, directory, filename, data):
        path = os.path.join(directory, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"    [+] Saved: {filename}")

if __name__ == "__main__":
    bot = TERM_Harvester()
    bot.fetch_master_index()
