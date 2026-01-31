import os
import importlib.util
import sys

class CartridgeLoader:
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cart_dir = os.path.join(self.root, "cartridges")

    def scan_and_load(self):
        """
        Scans 'cartridges/' for:
        1. Flat files: tool.py
        2. Managed Disks: tool_dir/main.py
        """
        if not os.path.exists(self.cart_dir): return {}
        
        carts = {}
        items = os.listdir(self.cart_dir)
        
        for item in items:
            path = os.path.join(self.cart_dir, item)
            
            # CASE A: Managed Disk (Directory)
            if os.path.isdir(path):
                entry_point = os.path.join(path, "main.py")
                if os.path.exists(entry_point):
                    name = item # The folder name is the command
                    try:
                        spec = importlib.util.spec_from_file_location(name, entry_point)
                        mod = importlib.util.module_from_spec(spec)
                        # Add cartridge dir to path so it can import its own siblings
                        sys.path.append(path) 
                        spec.loader.exec_module(mod)
                        carts[name] = mod
                    except Exception as e:
                        print(f"\033[31m[!] FAILED LOAD DIR '{name}': {e}\033[0m")

            # CASE B: Flat Cartridge (File)
            elif item.endswith(".py") and item != "__init__.py":
                name = item[:-3]
                try:
                    spec = importlib.util.spec_from_file_location(name, path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    carts[name] = mod
                except Exception as e:
                    print(f"\033[31m[!] FAILED LOAD FILE '{name}': {e}\033[0m")
                    
        return carts
