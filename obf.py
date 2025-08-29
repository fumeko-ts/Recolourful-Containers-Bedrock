import os
import json
import re

HEADER_COMMENT = """/**
// © 2025 ashura_tepes – All Rights Reserved.
//
// This is a specially crafted version of Java containers by ashura_temps, also known as ashura_tepes,
// created as part of a collaborative test.
//
// This UI is custom-made. You are allowed to use it **only as-is**, inside the game.
// Do not modify, extract, reuse, or share any part of this UI — including .json, .atemp,
// layout structure, or design.
//
// Not allowed:
//   - Editing the UI (even for private/personal use)
//   - Using parts of the code or layout in your own pack
//   - Reuploading, redistributing, or hosting these files elsewhere
//   - Converting texture packs to Bedrock using this UI
//
// Deobfuscating or modifying this UI breaks the license and is forbidden.
//
// By using it, you agree to these terms.
*/
"""

def unicode_escape_string(s):
    def repl(match):
        ch = match.group(0)
        return f"\\u{ord(ch):04x}"
    return re.sub(r"(?<!\\)\\u[0-9a-fA-F]{4}|.", 
                  lambda m: m.group(0) if m.group(0).startswith("\\u") else f"\\u{ord(m.group(0)):04x}",
                  s)

def is_text_or_texture_key(key):
    key_lower = key.lower()
    return "text" in key_lower or "texture" in key_lower

def should_preserve_value(key, value):
    if isinstance(value, str) and is_text_or_texture_key(key):
        return True
    if isinstance(value, str) and (
        "textures/" in value.lower()
        or any(value.lower().endswith(ext) for ext in [".png", ".jpg", ".tga"])
    ):
        return True
    return False

def process_object(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            new_key = key if is_text_or_texture_key(key) else unicode_escape_string(key)
            new_value = value if should_preserve_value(key, value) else process_object(value)
            new_dict[new_key] = new_value
        return new_dict
    elif isinstance(obj, list):
        return [process_object(item) for item in obj]
    elif isinstance(obj, str):
        return unicode_escape_string(obj)
    else:
        return obj

def obfuscate_json_file(file_path):
    filename = os.path.basename(file_path).lower()
    if filename == "manifest.json":
        print(f"Skipping manifest file: {file_path}")
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.match(r"/\*[\s\S]*?\*/\s*", content)
        if match:
            content = content[match.end():]
        data = json.loads(content)
        processed_data = process_object(data)
        json_str = json.dumps(processed_data, separators=(",", ":"))
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(HEADER_COMMENT + "\n\n" + json_str + "\n")
        print(f"Obfuscated file: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def process_directory(root_dir):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith((".json", ".atemp")):
                obfuscate_json_file(os.path.join(root, file))

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Starting obfuscation in: {base_dir}")
    process_directory(base_dir)
    print("Obfuscation complete!")
