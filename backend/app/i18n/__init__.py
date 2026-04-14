import json
from functools import lru_cache
from pathlib import Path

SUPPORTED_LOCALES = [
    "en",
    "es",
    "fr",
    "de",
    "pt",
    "zh-CN",
    "zh-TW",
    "ja",
    "ko",
    "ar",
    "hi",
    "ru",
    "it",
    "nl",
    "tr",
]

DEFAULT_LOCALE = "en"

MESSAGES_DIR = Path(__file__).parent / "messages"


@lru_cache(maxsize=len(SUPPORTED_LOCALES))
def load_messages(locale: str) -> dict:
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE
    path = MESSAGES_DIR / f"{locale}.json"
    if not path.exists():
        path = MESSAGES_DIR / f"{DEFAULT_LOCALE}.json"
    with open(path) as f:
        return json.load(f)


def t(key: str, locale: str = DEFAULT_LOCALE) -> str:
    messages = load_messages(locale)
    parts = key.split(".")
    value = messages
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, key)
        else:
            return key
    return str(value)
