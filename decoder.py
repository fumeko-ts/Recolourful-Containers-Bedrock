import os
import json
import re

UI_PATH = "./ui"

def format_json(data, indent=0):
    sp = "  " * indent

    if isinstance(data, dict):
        # Simple dict with single key and primitive/array -> inline with spaces
        if len(data) == 1:
            k, v = next(iter(data.items()))
            if not isinstance(v, (dict, list)):
                return "{ " + json.dumps(k, ensure_ascii=False) + ": " + json.dumps(v, ensure_ascii=False) + " }"
            if isinstance(v, list) and all(not isinstance(i, (dict, list)) for i in v):
                return "{ " + json.dumps(k, ensure_ascii=False) + ": " + json.dumps(v, ensure_ascii=False) + " }"
        
        # Otherwise expand normally
        lines = []
        for k, v in data.items():
            lines.append(sp + json.dumps(k, ensure_ascii=False) + ": " + format_json(v, indent + 1))
        return "{\n" + ",\n".join(lines) + "\n" + sp + "}"

    elif isinstance(data, list):
        if all(not isinstance(i, (dict, list)) for i in data):
            return json.dumps(data, ensure_ascii=False)
        lines = []
        for item in data:
            lines.append("  " * (indent + 1) + format_json(item, indent + 1))
        return "[\n" + ",\n".join(lines) + "\n" + sp + "]"

    else:
        return json.dumps(data, ensure_ascii=False)


def deobfuscate_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove top comment blocks
    content = re.sub(r"^/\*\*.*?\*/\s*", "", content, flags=re.DOTALL)

    try:
        decoded_content = content.encode("utf-8").decode("unicode_escape")
    except UnicodeDecodeError:
        decoded_content = content

    try:
        data = json.loads(decoded_content)
    except json.JSONDecodeError as e:
        print(f"[ERROR] {filepath}: {e}")
        return

    formatted = format_json(data, indent=1)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(formatted)
    print(f"[OK] {filepath}")


def process_ui_folder():
    for root, _, files in os.walk(UI_PATH):
        for file in files:
            if file.endswith(".json") or file.endswith(".atemp"):
                deobfuscate_file(os.path.join(root, file))


if __name__ == "__main__":
    process_ui_folder()
