"""
Run this after makemore training is done to collect 200+ novel names.
Usage: python3 sample_makemore.py
"""
import subprocess
import re

NAMES_FILE = "makemore/names.txt"
OUT_FILE = "makemore_names.txt"
WORK_DIR = "makemore/names"
TARGET = 200

def load_set(path):
    with open(path) as f:
        return {line.strip().lower() for line in f if line.strip()}

def extract_new_names(stdout):
    """Parse makemore stdout and return only the 'new' (novel) names."""
    names = []
    in_new_section = False
    for line in stdout.splitlines():
        line = line.strip()
        if re.match(r'\d+ samples that are new:', line):
            in_new_section = True
            continue
        if re.match(r'\d+ samples that are in', line) or line.startswith('---') or line.startswith('{'):
            in_new_section = False
            continue
        if in_new_section and line and line.isalpha():
            names.append(line.lower())
    return names

existing = load_set(NAMES_FILE)
novel = []
seen = set()

for seed in range(1, 20):
    result = subprocess.run(
        ["python3", "makemore/makemore.py", "-i", NAMES_FILE, "-o", WORK_DIR,
         "--sample-only", f"--seed={seed}"],
        capture_output=True, text=True, cwd="/workspaces/AI/name_Generation"
    )
    for name in extract_new_names(result.stdout):
        if name not in existing and name not in seen and len(name) >= 3:
            novel.append(name)
            seen.add(name)
    print(f"seed {seed}: total novel so far = {len(novel)}")
    if len(novel) >= TARGET:
        break

with open(OUT_FILE, "w") as f:
    for name in novel[:TARGET]:
        f.write(name + "\n")

print(f"\nWrote {min(len(novel), TARGET)} novel names to {OUT_FILE}")
