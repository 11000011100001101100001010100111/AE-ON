import os
def run(args):
    print(">> [RADAR] SPINNING UP...")
    # Attempt to run the radar script
    if os.path.exists("wx-radar.py"):
        os.system("python wx-radar.py")
    else:
        print(">> [ERR] 'wx-radar.py' not found.")
