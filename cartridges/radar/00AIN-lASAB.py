# AIM-01: LOCATE THE SCATTERED LLAMA & VERIFY BRIDGE
import os
import subprocess

def map_environment():
    home = os.path.expanduser("~")
    print(f"--- MAPPING LLAMA COMPONENTS ---")
    
    # Search for critical components
    search_targets = ['llama-server', 'orion.py', 'backup.sh']
    for root, dirs, files in os.walk(home):
        if 'talon_alta' in root or 'llama.cpp' in root:
            for f in files:
                if f in search_targets or f.endswith('.gguf'):
                    print(f"FOUND: {os.path.join(root, f)}")

    print(f"\n--- VERIFYING VECTOR GAMMA (CLOUD BRIDGE) ---")
    # Testing reachability of the Apps Script endpoint from your image
    g_url = "https://script.google.com/macros/s/AKfycbz.../exec"
    try:
        # Just a headers check, no data sent
        res = subprocess.run(['curl', '-I', '-L', g_url], capture_output=True, text=True)
        if "200" in res.stdout:
            print("BRIDGE STATUS: RE-ESTABLISHABLE")
        else:
            print("BRIDGE STATUS: LINK SEVERED")
    except:
        print("BRIDGE STATUS: OFFLINE")

map_environment()
