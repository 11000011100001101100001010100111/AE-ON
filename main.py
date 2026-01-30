import sys
import os
import importlib.util
from importlib.machinery import SourceFileLoader

# Æ-ON | D.A.T.A. Protocol
# System Bootloader [THE_SPARK]

def load_proprietary_module(path, name):
    try:
        if not os.path.exists(path):
            print(f"[!] MISSING ARTIFACT: {path}")
            sys.exit(1)
            
        loader = SourceFileLoader(name, path)
        spec = importlib.util.spec_from_loader(name, loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        loader.exec_module(module)
        return module
    except Exception as e:
        print(f"[!] BOOT FAILURE [{name}]: {e}")
        sys.exit(1)

def main():
    root = os.path.expanduser("~/AE-ON")
    
    # 1. Load Nervous System
    sys_path = os.path.join(root, "core", "system.tome")
    core_system = load_proprietary_module(sys_path, "core_system")
    
    # 2. Initialize Lattice
    lattice = core_system.AeonLattice()
    
    # 3. Load Visual Shell
    shell_path = os.path.join(root, "nexus", "shell.nxs")
    nexus_shell = load_proprietary_module(shell_path, "nexus_shell")
    
    # 4. IGNITION
    nexus_shell.ignite(lattice)

if __name__ == "__main__":
    main()
