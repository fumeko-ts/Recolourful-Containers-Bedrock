import os

# Set the root directory where your .lang files are
root_dir = "texts"

# Translations dictionary
translations = {
    "bg_BG": "Светъл режим",
    "cs_CZ": "Světlý režim",
    "da_DK": "Lys tilstand",
    "de_DE": "Hellmodus",
    "el_GR": "Φωτεινή λειτουργία",
    "en_GB": "Light Mode",
    "en_US": "Light Mode",
    "es_ES": "Modo Claro",
    "es_MX": "Modo Claro",
    "fi_FI": "Vaalea tila",
    "fr_CA": "Mode Clair",
    "fr_FR": "Mode Clair",
    "hu_HU": "Világos mód",
    "id_ID": "Mode Terang",
    "it_IT": "Modalità Chiara",
    "ja_JP": "ライトモード",
    "ko_KR": "라이트 모드",
    "nb_NO": "Lysmodus",
    "nl_NL": "Lichtmodus",
    "pl_PL": "Jasny tryb",
    "pt_BR": "Modo Claro",
    "pt_PT": "Modo Claro",
    "ru_RU": "Светлый режим",
    "sk_SK": "Svetlý režim",
    "sv_SE": "Ljust läge",
    "tr_TR": "Açık Mod",
    "uk_UA": "Світлий режим",
    "zh_CN": "浅色模式",
    "zh_TW": "淺色模式"
}

# Loop through all files in the root directory
for filename in os.listdir(root_dir):
    file_path = os.path.join(root_dir, filename)
    if os.path.isfile(file_path):
        # Get the language code from filename (assumes format xx_XX.lang)
        lang_code = filename.split(".")[0]
        if lang_code in translations:
            translation = translations[lang_code]
            # Open the file in append mode and add the new line
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"\nashur.mode.manifest={translation}")
            print(f"Added translation to {filename}")
