import os
import re

C_NEW = """const C = {
    bg: "var(--bg)", surface: "var(--surface)", elevated: "var(--elevated)",
    border: "var(--border)", muted: "var(--muted)", text: "var(--text)", textSecondary: "var(--text-secondary)", avocado: "var(--avocado)", danger: "var(--danger)", warning: "var(--warning)", avocadoLight: "var(--avocado-light)"
};"""

C_REGEX = re.compile(r"const C = \{.*?\};", re.DOTALL)

for root, _, files in os.walk("/home/ofx/ProjetosWeb/GestaoFinanceira/frontend/src"):
    for file in files:
        if file.endswith(".tsx") or file.endswith(".ts"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if "const C = {" in content:
                content = C_REGEX.sub(C_NEW, content)
                content = content.replace("color: \"white\"", "color: \"var(--text)\"")
                content = content.replace("color: \"#fff\"", "color: \"var(--text)\"")
                content = content.replace("text-white", "text-[color:var(--text)]")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Updated {filepath}")
