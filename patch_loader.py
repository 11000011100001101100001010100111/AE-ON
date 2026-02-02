import os

# 1. DEFINE TARGET PATH (Relative to ~/AE-ON)
target_path = os.path.join("nexus", "cart_loader.py")

# 2. DEFINE CONTENT (CLIP 050)
code = r'''import os
import importlib.util
import sys

class CartridgeLoader:
    def __init__(self):
        # Resolve root relative to this file (nexus/cart_loader.py -> ../ -> root)
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cart_dir = os.path.join(self.root, "cartridges")

    def scan_and_load(self):
        """
        Scans 'cartridges/' for:
        1. Packages: tool_dir/__init__.py (Standard)
        2. Managed:  tool_dir/main.py (Legacy)
        3. Flat:     tool.py
        """
        if not os.path.exists(self.cart_dir): return {}

        carts = {}
        try:
            items = sorted(os.listdir(self.cart_dir))
        except OSError:
            return {}

        for item in items:
            path = os.path.join(self.cart_dir, item)
            name = item

            # CASE A: Directory (Package or Managed)
            if os.path.isdir(path):
                # Priority 1: Standard Python Package (__init__.py)
                init_path = os.path.join(path, "__init__.py")
                main_path = os.path.join(path, "main.py")
                
                entry_point = None
                
                if os.path.exists(init_path):
                    entry_point = init_path
                elif os.path.exists(main_path):
                    entry_point = main_path
                
                if entry_point:
                    try:
                        # Ensure the cartridge folder is in sys.path for internal imports
                        if path not in sys.path:
                            sys.path.append(path)
                            
                        spec = importlib.util.spec_from_file_location(name, entry_point)
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        
                        if hasattr(mod, 'run'):
                            carts[name] = mod
                    except Exception as e:
                        # Print error cleanly to avoid breaking TUI if possible
                        print(f"ERR LOADING {name}: {e}")

            # CASE B: Flat Cartridge (File)
            elif item.endswith(".py") and item != "__init__.py":
                name = item[:-3]
                try:
                    spec = importlib.util.spec_from_file_location(name, path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, 'run'):
                        carts[name] = mod
                except Exception as e:
                    print(f"ERR LOADING {name}: {e}")

        return carts
'''

# 3. WRITE FILE
print(f"[+] TARGET: {target_path}")
try:
    with open(target_path, "w") as f:
        f.write(code)
    print("    -> SUCCESS: Loader Updated.")
except Exception as e:
    print(f"    -> ERROR: {e}")
    # Fallback to absolute path check
    print("    -> RETRYING with absolute path...")
    abs_path = os.path.abspath(target_path)
    try:
        with open(abs_path, "w") as f:
            f.write(code)
        print("    -> SUCCESS.")
    except Exception as e2:
        print(f"    -> CRITICAL FAIL: {e2}")

