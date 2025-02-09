import json
import os

DEFAULT_LANG = "en"
LANG_DIR = "src/lang"

def load_messages(lang=DEFAULT_LANG):
    """Load language messages from JSON files."""
    lang_file = os.path.join(LANG_DIR, f"{lang}.json")

    if not os.path.exists(lang_file):
        lang_file = os.path.join(LANG_DIR, f"{DEFAULT_LANG}.json")  # Fallback to English

    with open(lang_file, "r", encoding="utf-8") as f:
        return json.load(f)

def translate(key, lang="en", **kwargs):
    """Translate messages based on language and replace variables if needed."""
    messages = load_messages(lang)
    message = messages.get(key, key)  # Default to key if not found
    return message.format(**kwargs)