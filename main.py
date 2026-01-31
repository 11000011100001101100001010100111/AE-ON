import sys
import os
import importlib.util
from importlib.machinery import SourceFileLoader

# Æ-ON | D.A.T.A. Protocol
# [UNIVERSAL_LOADER_V3]

ARTIFACT_MAP = {
    'root':  ['.gem'],         # Data Gems
    'core':  ['.tome'],        # Logic Tomes
    'nexus': ['.nxs'],         # Interfaces
    'meteor':['.met']          # Meteorological Data
}

def inject_artifact(module_name, file_path):
    if not os.path.exists(file_path): return None
    try:
        loader = SourceFileLoader(module_name, file_path)
        spec = importlib.util.spec_from_loader(module_name, loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        loader.exec_module(module)
        print(f"\033[90m[+] ASSIMILATED: {module_name:<20} ({os.path.basename(file_path)})\033[0m")
        return module
    except Exception as e:
        print(f"\033[31m[!] FAILED TO LOAD {file_path}: {e}\033[0m")
        return None

def scan_and_load(base_dir):
    print("\033[90m[Æ-ON] SCANNING LATTICE...\033[0m")

    # 1. SCAN ROOT
    for f in os.listdir(base_dir):
        if os.path.isfile(os.path.join(base_dir, f)):
            _, ext = os.path.splitext(f)
            if ext in ARTIFACT_MAP['root']:
                mod_name = f.replace(ext, "")
                inject_artifact(mod_name, os.path.join(base_dir, f))

    # 2. SCAN DIRECTORIES (STRICT ORDER)
    # [CRITICAL] Meteor must load before Nexus so the import works!
    subdirs = ['core', 'meteor', 'nexus'] 
    
    for folder in subdirs:
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path): continue
        
        valid_exts = ARTIFACT_MAP.get(folder, [])
        for f in os.listdir(folder_path):
            _, ext = os.path.splitext(f)
            if ext in valid_exts:
                mod_name = f"{folder}.{f.replace(ext, '')}"
                inject_artifact(mod_name, os.path.join(folder_path, f))

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    scan_and_load(root)

    # 3. VERIFY & IGNITE
    if 'nexus.shell' not in sys.modules:
        print("\033[31m[!] CRITICAL: CORTEX DIED DURING BOOT\033[0m")
        sys.exit(1)

    print(f"\033[32m[I] SYSTEM STABLE. IGNITING...\033[0m")
    import time
    time.sleep(0.5)

    try:
        sys.modules['nexus.shell'].NexusShell().ignite()
    except AttributeError:
        print("\033[31m[!] CRITICAL: SHELL MODULE LOADED BUT CLASS MISSING.\033[0m")
        print("    Check for syntax errors in nexus/shell.nxs")

if __name__ == "__main__":
    main()
