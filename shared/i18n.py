"""Internationalization (i18n) infrastructure for Lumina."""

import json
from pathlib import Path
from typing import Any, Dict

LOCALES_DIR = Path(__file__).parent.parent / "locales"

_translations_cache: Dict[str, Dict[str, Any]] = {}


def load_locales() -> Dict[str, Dict[str, Any]]:
    """Loads all JSON translation files from locales/ directory."""
    global _translations_cache
    if _translations_cache:
        return _translations_cache

    for lang_file in LOCALES_DIR.glob("*.json"):
        lang_code = lang_file.stem
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                _translations_cache[lang_code] = json.load(f)
        except Exception:
            _translations_cache[lang_code] = {}

    return _translations_cache


def get_locale_dict(lang: str = "ru") -> Dict[str, Any]:
    """Retrieves full locale dictionary for requested language."""
    locales = load_locales()
    return locales.get(lang, locales.get("ru", {}))


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """
    Translates a dot-separated translation key (e.g. 'common.save' or 'errors.forbidden').
    Falls back to 'ru', then returns the key itself if not found.
    Interpolates {placeholder} with kwargs.
    """
    locales = load_locales()
    dict_for_lang = locales.get(lang, locales.get("ru", {}))

    keys = key.split(".")
    val: Any = dict_for_lang
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            val = None
            break

    # Fallback to ru if primary lookup failed and lang wasn't ru
    if val is None and lang != "ru":
        val = locales.get("ru", {})
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                val = None
                break

    if val is None or not isinstance(val, str):
        return key

    if kwargs:
        try:
            return val.format(**kwargs)
        except Exception:
            return val

    return val
