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

def is_text_or_texture_key(key):
    key_lower = key.lower()
    return "text" in key_lower or "texture" in key_lower

def is_binding_key(key):
    key_lower = key.lower()
    return key_lower == "bindings"

def is_binding_property(key):
    binding_properties = [
        "binding_name",
        "binding_collection_name",
        "binding_type",
        "binding_condition",
        "source_property_name",
        "target_property_name"
    ]
    return key.lower() in [prop.lower() for prop in binding_properties]

def should_preserve_value(key, value):
    if isinstance(value, str) and (is_text_or_texture_key(key) or is_binding_property(key)):
        return True
    if isinstance(value, str) and (
        "textures/" in value.lower()
        or any(value.lower().endswith(ext) for ext in [".png", ".jpg", ".tga"])
    ):
        return True
    return False

def unicode_escape_key(key):
    # Escape each character as \uXXXX, but leave existing \uXXXX sequences intact
    result = []
    i = 0
    while i < len(key):
        if key[i] == "\\" and i + 5 < len(key) and key[i+1] == "u" and all(c in "0123456789abcdefABCDEF" for c in key[i+2:i+6]):
            result.append(key[i:i+6])
            i += 6
        else:
            result.append(f"\\u{ord(key[i]):04x}")
            i += 1
    return "".join(result)

def process_object(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            if is_binding_key(key):
                # Preserve the entire bindings structure
                new_dict[key] = value
            else:
                new_key = key if (is_text_or_texture_key(key) or is_binding_property(key)) else unicode_escape_key(key)
                if should_preserve_value(key, value):
                    new_value = value
                else:
                    new_value = process_object(value)
                new_dict[new_key] = new_value
        return new_dict
    elif isinstance(obj, list):
        return [process_object(item) for item in obj]
    elif isinstance(obj, str):
        # Only escape strings that are not text/texture values
        return unicode_escape_key(obj)
    else:
        return obj

class SingleBackslashEncoder(json.JSONEncoder):
    def encode(self, obj):
        # Use the default encoder then replace double backslashes with single
        result = super().encode(obj)
        return result.replace('\\\\u', '\\u')

def obfuscate_json_file(file_path):
    filename = os.path.basename(file_path).lower()
    if filename == "manifest.json":
        print(f"Skipping manifest file: {file_path}")
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        content_no_header = content
        match = re.match(r"/\*[\s\S]*?\*/\s*", content)
        if match:
            content_no_header = content[match.end():]
        data = json.loads(content_no_header)
        processed_data = process_object(data)
        json_str = json.dumps(processed_data, separators=(",", ":"), cls=SingleBackslashEncoder)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(HEADER_COMMENT)
            f.write("\n\n")
            f.write(json_str)
            f.write("\n")
        print(f"Obfuscated file: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def process_directory(root_dir):
    ui_dir = os.path.join(root_dir, "ui")
    if not os.path.exists(ui_dir):
        print(f"No /ui directory found in {root_dir}")
        return
    for root, _, files in os.walk(ui_dir):
        for file in files:
            if file.lower().endswith((".json", ".atemp")):
                obfuscate_json_file(os.path.join(root, file))

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Starting obfuscation in: {base_dir}")
    process_directory(base_dir)
    print("Obfuscation complete!")