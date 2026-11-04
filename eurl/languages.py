"""The 36 languages OpenEuroLLM prioritises (the EUROPA Eval set): the 24 EU official languages plus 12 more.

Codes are ISO 639-3 as in EUROPA (`nor` is Norwegian; Bokmål is the written standard used). Each language names the
countries whose locale packs render it, so every language has at least one world to live in.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Language:
    code: str                    # ISO 639-3 (EUROPA key)
    iso1: str                    # ISO 639-1
    name: str                    # English name
    native: str                  # endonym
    script: str                  # ISO 15924
    countries: Tuple[str, ...]   # ISO 3166-1 alpha-2 of the locale packs that use it
    eu_official: bool = True


_ROWS = [
    Language("bul", "bg", "Bulgarian", "български", "Cyrl", ("BG",)),
    Language("ces", "cs", "Czech", "čeština", "Latn", ("CZ",)),
    Language("dan", "da", "Danish", "dansk", "Latn", ("DK",)),
    Language("deu", "de", "German", "Deutsch", "Latn", ("DE", "AT", "LU", "BE")),
    Language("ell", "el", "Greek", "Ελληνικά", "Grek", ("GR", "CY")),
    Language("eng", "en", "English", "English", "Latn", ("IE", "MT")),
    Language("est", "et", "Estonian", "eesti", "Latn", ("EE",)),
    Language("fin", "fi", "Finnish", "suomi", "Latn", ("FI",)),
    Language("fra", "fr", "French", "français", "Latn", ("FR", "BE", "LU")),
    Language("gle", "ga", "Irish", "Gaeilge", "Latn", ("IE",)),
    Language("hrv", "hr", "Croatian", "hrvatski", "Latn", ("HR",)),
    Language("hun", "hu", "Hungarian", "magyar", "Latn", ("HU",)),
    Language("ita", "it", "Italian", "italiano", "Latn", ("IT",)),
    Language("lav", "lv", "Latvian", "latviešu", "Latn", ("LV",)),
    Language("lit", "lt", "Lithuanian", "lietuvių", "Latn", ("LT",)),
    Language("mlt", "mt", "Maltese", "Malti", "Latn", ("MT",)),
    Language("nld", "nl", "Dutch", "Nederlands", "Latn", ("NL", "BE")),
    Language("pol", "pl", "Polish", "polski", "Latn", ("PL",)),
    Language("por", "pt", "Portuguese", "português", "Latn", ("PT",)),
    Language("ron", "ro", "Romanian", "română", "Latn", ("RO",)),
    Language("slk", "sk", "Slovak", "slovenčina", "Latn", ("SK",)),
    Language("slv", "sl", "Slovenian", "slovenščina", "Latn", ("SI",)),
    Language("spa", "es", "Spanish", "español", "Latn", ("ES",)),
    Language("swe", "sv", "Swedish", "svenska", "Latn", ("SE", "FI")),
    Language("cat", "ca", "Catalan", "català", "Latn", ("ES",), eu_official=False),
    Language("eus", "eu", "Basque", "euskara", "Latn", ("ES",), eu_official=False),
    Language("glg", "gl", "Galician", "galego", "Latn", ("ES",), eu_official=False),
    Language("isl", "is", "Icelandic", "íslenska", "Latn", ("IS",), eu_official=False),
    Language("nor", "no", "Norwegian", "norsk", "Latn", ("NO",), eu_official=False),
    Language("sqi", "sq", "Albanian", "shqip", "Latn", ("AL",), eu_official=False),
    Language("bos", "bs", "Bosnian", "bosanski", "Latn", ("BA",), eu_official=False),
    Language("srp", "sr", "Serbian", "српски", "Cyrl", ("RS",), eu_official=False),
    Language("mkd", "mk", "Macedonian", "македонски", "Cyrl", ("MK",), eu_official=False),
    Language("tur", "tr", "Turkish", "Türkçe", "Latn", ("TR",), eu_official=False),
    Language("ukr", "uk", "Ukrainian", "українська", "Cyrl", ("UA",), eu_official=False),
    Language("kat", "ka", "Georgian", "ქართული", "Geor", ("GE",), eu_official=False),
]

LANGUAGES: Dict[str, Language] = {row.code: row for row in _ROWS}
BY_ISO1: Dict[str, Language] = {row.iso1: row for row in _ROWS}


def get(code: str) -> Language:
    """Look up by ISO 639-3 or ISO 639-1 code."""
    if code in LANGUAGES:
        return LANGUAGES[code]
    if code in BY_ISO1:
        return BY_ISO1[code]
    raise KeyError(f"unknown language {code!r}; known: {', '.join(sorted(LANGUAGES))}")
