import os
def run(args):
    print(">> [ATOMIC LAB] INITIALIZING...")
    # Attempt to run the original core. Adjust filename if needed.
    if os.path.exists("pal_core.py"):
        os.system("python pal_core.py")
    else:
        print(">> [ERR] Core file 'pal_core.py' not found in cartridge.")
