import datetime as dt
import string

from eurl import banking
from eurl.calendar import Rule, easter_rule, fixed
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat


class _KingsDay(Rule):
    """Koningsdag: 27 April, or 26 April when the 27th is a Sunday (since 2014)."""

    def date(self, year):
        if self.since and year < self.since:
            return None
        d = dt.date(year, 4, 27)
        return d - dt.timedelta(days=1) if d.weekday() == 6 else d


class _Lustrum(Rule):
    """A fixed date that is a day off only every fifth year (Bevrijdingsdag in 2025, 2030, ...)."""

    def date(self, year):
        return dt.date(year, self.month, self.day) if year % 5 == 0 else None


# Algemene termijnenwet art. 3: New Year, Easter and Whit Sunday and Monday, Ascension, King's Day, Christmas and
# Boxing Day, and 5 May. Whether 5 May and Good Friday are paid days off depends on the collective agreement:
# 5 May usually only in lustrum years, Good Friday in some sectors. Both are modelled as customary (public=False).
HOLIDAYS = (
    fixed(1, 1, {"nld": "Nieuwjaarsdag"}),
    easter_rule(0, {"nld": "Eerste paasdag"}),
    easter_rule(1, {"nld": "Tweede paasdag"}),
    _KingsDay("fixed", {"nld": "Koningsdag"}, month=4, day=27, since=2014),
    easter_rule(39, {"nld": "Hemelvaartsdag"}),
    easter_rule(49, {"nld": "Eerste pinksterdag"}),
    easter_rule(50, {"nld": "Tweede pinksterdag"}),
    fixed(12, 25, {"nld": "Eerste kerstdag"}),
    fixed(12, 26, {"nld": "Tweede kerstdag"}),
    # Customary / collective-agreement days off.
    easter_rule(-2, {"nld": "Goede Vrijdag"}, public=False),
    _Lustrum("fixed", {"nld": "Bevrijdingsdag"}, month=5, day=5, public=False),
)


def kvk_number(rng):
    return f"KvK {rng.randint(10000000, 99999999)}"


# --- Btw-identificatienummer: NL + RSIN (9 digits, elfproef) + B01 -----------------------------------------------
# Elfproef: 9·d1 + 8·d2 + ... + 2·d8 - d9 ≡ 0 (mod 11). Numbers issued to sole proprietors since 2020 instead
# satisfy ISO 7064 MOD 97-10 over "NL" + the full number; both are accepted.

def _elfproef(nine: str) -> bool:
    return sum((9 - i) * int(d) for i, d in enumerate(nine[:8])) % 11 == int(nine[8])


def _mod97_ok(text: str) -> bool:
    return int("".join(str(int(ch, 36)) for ch in text)) % 97 == 1


def nl_vat(rng, _kvk=None):
    while True:
        base = str(rng.randint(1, 9)) + "".join(rng.choice(string.digits) for _ in range(7))
        check = sum((9 - i) * int(d) for i, d in enumerate(base)) % 11
        if check < 10:
            return f"NL{base}{check}B01"


def nl_vat_valid(value: str) -> bool:
    s = value.replace(" ", "").replace(".", "").upper()
    if len(s) != 14 or not s.startswith("NL") or s[11] != "B":
        return False
    number, suffix = s[2:11], s[12:]
    if not number.isdigit() or not suffix.isdigit() or int(number) == 0 or int(suffix) == 0:
        return False
    return _elfproef(number) or _mod97_ok(s)


LOCALE = Locale(
    country="NL", name="Netherlands", languages=("nld",),
    money=MoneyFormat("EUR", "€" + NBSP, ",", ".", symbol_first=True),
    timezone="Europe/Amsterdam",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2100, "food": 900, "accommodation": 900, "books": 900, "passenger_transport": 900,
            "restaurant": 900},
    vat_as_of="2025",
    vat_source="Wet op de omzetbelasting 1968, tabel I (21 %; 9 % food, accommodation, books, passenger transport, "
               "restaurant meals); Belastingdienst; EU Taxes in Europe Database",
    company_id=kvk_number,
    vat_id=nl_vat,                                  # the btw-id is built on the RSIN, not on the KvK number
    vat_id_valid=nl_vat_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"nld": "betalingskenmerk (RF-referentie)"},
    company_suffixes=("B.V.", "N.V.", "V.O.F."),
    company_stems=("Polderveld", "Duinzicht", "Molenwaard", "Waterland", "Lindenhof", "Kanaalzicht", "Heideveld",
                   "Oosterweide", "Tulpendaal", "Rivierenhof"),
    first_names=("Daan", "Emma", "Sem", "Julia", "Lucas", "Sophie", "Thijs", "Anna", "Lars", "Lisa", "Bram",
                 "Fleur"),
    last_names=("de Jong", "Jansen", "de Vries", "van den Berg", "van Dijk", "Bakker", "Janssen", "Visser", "Smit",
                "Meijer", "de Boer", "Mulder"),
    cities=("Amsterdam", "Rotterdam", "Utrecht", "Eindhoven", "Groningen", "Tilburg", "Den Haag", "Zwolle"),
    office_hours=("09:00", "17:30"), lunch=("12:30", "13:00"),
    date_style="DD-MM-YYYY",
    notes=["Money is written with the symbol first: € 1.234,56.",
           "Goede Vrijdag and Bevrijdingsdag (5 May, a day off in lustrum years) are collective-agreement days off, "
           "modelled as customary.",
           "A rise of VAT on accommodation from 9 % to 21 % was planned for 2026; this pack is the 2025 snapshot.",
           "The acceptgiro betalingskenmerk was discontinued in 2019; payments use the RF reference."],
)
