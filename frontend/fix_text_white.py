import os
import re

d = "/home/ofx/ProjetosWeb/GestaoFinanceira/frontend/src/app"
d2 = "/home/ofx/ProjetosWeb/GestaoFinanceira/frontend/src/components"

def fix_file(p):
    with open(p, "r") as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if "text-white" in line:
            if "<button" in line or "🥑" in line or "Avocado AI" in line:
                new_lines.append(line)
                continue
            if "transition-opacity" in line or "hover:" in line:
                 new_lines.append(line)
                 continue
            if "GlobalLoader" in line:
                 new_lines.append(line)
                 continue
            # Replace safely
            line = re.sub(r' +text-white +', ' ', line)
            line = re.sub(r' +text-white"', '"', line)
            line = re.sub(r'"text-white +', '"', line)
            line = re.sub(r'"text-white"', '""', line)
        new_lines.append(line)
    
    with open(p, "w") as f:
        f.write('\n'.join(new_lines))


for r, _, fs in os.walk(d):
    for f in fs:
        if f.endswith(".tsx"):
            fix_file(os.path.join(r, f))

for r, _, fs in os.walk(d2):
    for f in fs:
        if f.endswith(".tsx"):
            fix_file(os.path.join(r, f))

print("Fixed text-white")
