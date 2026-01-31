import os
import subprocess
import datetime

class GemRefract:
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.link_path = os.path.join(self.root, "NEURAL_LINK.md")
        self.manifest_path = os.path.join(self.root, "PROJECT_MANIFEST.md")

    def get_git_log(self):
        try:
            cmd = ["git", "log", "-n", "3", "--pretty=format:%h|%s", "--date=short"]
            return subprocess.check_output(cmd, text=True, cwd=self.root).strip().split('\n')
        except: return ["(No Git Repo)"]

    def read_link_tail(self, lines=5):
        try:
            with open(self.link_path, "r") as f:
                content = f.readlines()
            return [x.strip() for x in content[-lines:]]
        except: return ["(Link Empty)"]

    def scan_cartridges(self):
        cart_dir = os.path.join(self.root, "cartridges")
        if not os.path.exists(cart_dir): return []
        return [f for f in os.listdir(cart_dir) if f.endswith(".py")]

    def generate_seed(self):
        print("\n=== [GEM REFRACT :: COGNITIVE SEED] ===")
        print(f"TS: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        print("\n[REALITY :: GIT]")
        for l in self.get_git_log(): print(f"  {l}")

        print("\n[REALITY :: CARTRIDGES]")
        for c in self.scan_cartridges(): print(f"  [+] {c}")

        print("\n[COMMS :: NEURAL LINK (LAST 5)]")
        for m in self.read_link_tail(): print(f"  {m}")
        
        print("\n========================================")

    def write_signal(self, user, msg):
        ts = datetime.datetime.now().strftime('%H:%M')
        with open(self.link_path, "a") as f:
            f.write(f"\n{ts} | {user} | {msg}")

if __name__ == "__main__":
    GemRefract().generate_seed()
