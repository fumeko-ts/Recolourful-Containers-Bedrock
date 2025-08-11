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
    return ''.join(f'\\u{ord(c):04x}' for c in s)

def is_text_or_texture_key(key):
    key_lower = key.lower()
    return 'text' in key_lower or 'texture' in key_lower

def should_preserve_value(key, value):
    # Preserve text or texture keys/values:
    if isinstance(value, str) and is_text_or_texture_key(key):
        return True
    # Also preserve if the value contains texture path patterns
    if isinstance(value, str) and ('textures/' in value.lower() or
                                   any(value.lower().endswith(ext) for ext in ['.png', '.jpg', '.tga'])):
        return True
    return False

def process_object(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            # Obfuscate key unless it matches text or texture
            if is_text_or_texture_key(key):
                new_key = key
            else:
                new_key = unicode_escape_string(key)
            # Preserve value if text or texture key, else process recursively
            if should_preserve_value(key, value):
                new_value = value
            else:
                new_value = process_object(value)
            new_dict[new_key] = new_value
        return new_dict
    elif isinstance(obj, list):
        return [process_object(item) for item in obj]
    elif isinstance(obj, str):
        # Obfuscate string value
        return unicode_escape_string(obj)
    else:
        return obj

def obfuscate_json_file(file_path):
    filename = os.path.basename(file_path).lower()
    if filename == "manifest.json":
        print(f"Skipping manifest file: {file_path}")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove existing comment header if any
        content_no_header = content
        match = re.match(r'/\*[\s\S]*?\*/\s*', content)
        if match:
            content_no_header = content[match.end():]

        data = json.loads(content_no_header)
        processed_data = process_object(data)

        # Dump JSON without extra whitespace
        json_str = json.dumps(processed_data, separators=(',', ':'))

        # Fix double-escaped unicode sequences (from python json.dumps escaping)
        json_str = re.sub(r'\\\\u([0-9a-fA-F]{4})', r'\\u\1', json_str)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(HEADER_COMMENT)
            f.write('\n')  # two blank lines after header
            f.write('\n')
            f.write(json_str)
            f.write('\n')

        print(f"Obfuscated file: {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def process_directory(root_dir):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(('.json', '.atemp')):
                obfuscate_json_file(os.path.join(root, file))

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Starting obfuscation in: {base_dir}")
    process_directory(base_dir)
    print("Obfuscation complete!")
