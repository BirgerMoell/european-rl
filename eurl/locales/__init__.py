"""Locale packs: one per country. A pack is data plus small functions, tested on its own (tests/test_locales.py).

What a pack holds: languages, money format, time zone, public holidays, VAT rates by category (a dated policy
snapshot, in basis points), company and VAT identifiers, the national payment reference, names, cities and
company-name parts for the synthetic world.

VAT rates are the world's policy snapshot for the year in `vat_as_of`, taken from the European Commission's
Taxes in Europe Database and national tax authorities; `vat_verified` stays False until a person has checked them
against the source. Tasks always state the rates that apply (in the prompt or the company handbook), so the
answer is defined by the task even where real rates change.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from eurl.calendar import Rule
from eurl.money import MoneyFormat

VAT_CATEGORIES = ("standard", "food", "accommodation", "books", "passenger_transport", "restaurant")


@dataclass(frozen=True)
class Locale:
    country: str                          # ISO 3166-1 alpha-2
    name: str                             # English country name
    languages: Tuple[str, ...]            # ISO 639-3; the first is the default business language
    money: MoneyFormat
    timezone: str                         # IANA
    holidays: Tuple[Rule, ...]
    vat_bp: Dict[str, int]                # category -> rate in basis points (2550 = 25.5 %)
    vat_as_of: str
    vat_source: str
    company_id: Callable                  # rng -> national company number (display form)
    vat_id: Callable                      # (rng, company number) -> VAT identification number
    vat_id_valid: Callable                # VAT id -> bool
    payment_reference: Callable           # rng -> national structured payment reference
    payment_reference_name: Dict[str, str]
    company_suffixes: Tuple[str, ...]
    company_stems: Tuple[str, ...]
    first_names: Tuple[str, ...]
    last_names: Tuple[str, ...]
    cities: Tuple[str, ...]
    office_hours: Tuple[str, str] = ("08:00", "17:00")
    lunch: Tuple[str, str] = ("12:00", "13:00")
    weekend: Tuple[int, ...] = (5, 6)
    vat_verified: bool = False
    eu_member: bool = True
    date_style: str = "YYYY-MM-DD"        # how dates are written locally: D/DD, M/MM, YYYY with separators
    price_scale: int = 1                  # rough euro-to-local factor for synthetic prices (the world is synthetic)
    notes: List[str] = field(default_factory=list)

    @property
    def language(self) -> str:
        return self.languages[0]

    def vat_percent(self, category: str) -> str:
        bp = self.vat_bp[category]
        return f"{bp // 100}" if bp % 100 == 0 else f"{bp / 100:g}".replace(".", self.money.decimal)


# A pack is a module eurl/locales/<cc>.py defining LOCALE; adding a country is adding one file.
PACKS = tuple(sorted(p.stem for p in Path(__file__).parent.glob("[a-z][a-z].py")))


def load(country: str) -> Locale:
    code = country.lower()
    if code not in PACKS:
        raise KeyError(f"no locale pack for {country!r}; available: {', '.join(PACKS)}")
    locale = importlib.import_module(f"eurl.locales.{code}").LOCALE
    if locale.country.lower() != code:
        raise ValueError(f"pack {code} declares country {locale.country}")
    return locale


def all_packs() -> List[Locale]:
    return [load(code) for code in PACKS]


def format_date(d, style: str) -> str:
    """Render a date in a local style such as "DD.MM.YYYY", "D.M.YYYY", "DD/MM/YYYY" or "YYYY-MM-DD"."""
    import re
    out = style.replace("YYYY", f"{d.year:04d}")
    out = re.sub(r"\bDD\b", f"{d.day:02d}", out)
    out = re.sub(r"\bMM\b", f"{d.month:02d}", out)
    out = re.sub(r"\bD\b", str(d.day), out)
    return re.sub(r"\bM\b", str(d.month), out)
