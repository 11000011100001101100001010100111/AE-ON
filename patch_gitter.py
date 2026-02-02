import os

# 1. DEFINE PATH
# Target: ~/AE-ON/core/gitter.py
target_path = os.path.expanduser("~/AE-ON/core/gitter.py")

# 2. DEFINE CONTENT
code = r'''import subprocess

class Diplomat:
    def get_status(self):
        """Returns a list of changed files."""
        try:
            # Check for changes
            res = subprocess.check_output(["git", "status", "--porcelain"], text=True)
            if not res: return []
            return [line.strip() for line in res.split('\n') if line.strip()]
        except:
            return []

    def execute_save(self, message):
        """Stages, Commits, AND PUSHES changes."""
        try:
            # 1. Stage All
            subprocess.check_call(["git", "add", "."])
            
            # 2. Commit
            commit_res = subprocess.run(
                ["git", "commit", "-m", message], 
                capture_output=True, text=True
            )
            
            # Handle "Nothing to commit" vs Actual Errors
            if commit_res.returncode != 0:
                if "nothing to commit" in commit_res.stdout:
                    return "NO LOCAL CHANGES."
                return f"COMMIT ERR: {commit_res.stderr.strip()}"

            # 3. AUTO-PUSH (The Missing Link)
            push_res = subprocess.run(
                ["git", "push"], 
                capture_output=True, text=True
            )
            
            if push_res.returncode == 0:
                # Get short hash for log
                try:
                    short_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
                except:
                    short_hash = "SYNCED"
                return f"[{short_hash}] COMMITTED & PUSHED."
            else:
                return f"COMMIT OK, PUSH FAILED: {push_res.stderr.strip()}"

        except Exception as e:
            return f"CRITICAL FAULT: {str(e)}"
'''

# 3. WRITE FILE
print(f"[+] WRITING: {target_path}")
try:
    with open(target_path, "w") as f:
        f.write(code)
    print("    -> SUCCESS: Diplomat Updated.")
except Exception as e:
    print(f"    -> ERROR: {e}")

