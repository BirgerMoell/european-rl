import datetime as dt
import string

from eurl import banking
from eurl.calendar import Rule, easter_rule, fixed, weekday_from
from eurl.locales import Locale
from eurl.money import MoneyFormat


class _BrigidsDay(Rule):
    """Saint Brigid's Day (since 2023): the first Monday in February, or 1 February when that is a Friday."""

    def date(self, year):
        if self.since and year < self.since:
            return None
        first = dt.date(year, 2, 1)
        if first.weekday() == 4:
            return first
        return first + dt.timedelta(days=(0 - first.weekday()) % 7)


# Organisation of Working Time Act 1997, Schedule 2, as amended (Saint Brigid's Day from 2023). Good Friday is not
# a public holiday. When a holiday falls on a weekend the employee is owed a day in lieu (often the next working
# day) — an entitlement, not a public holiday, so it is not modelled.
HOLIDAYS = (
    fixed(1, 1, {"eng": "New Year's Day", "gle": "Lá Caille"}),
    _BrigidsDay("fixed", {"eng": "Saint Brigid's Day", "gle": "Lá Fhéile Bríde"}, month=2, day=1, since=2023),
    fixed(3, 17, {"eng": "Saint Patrick's Day", "gle": "Lá Fhéile Pádraig"}),
    easter_rule(1, {"eng": "Easter Monday", "gle": "Luan Cásca"}),
    weekday_from(0, 5, 1, {"eng": "May Bank Holiday", "gle": "Lá Saoire i mí na Bealtaine"}),
    weekday_from(0, 6, 1, {"eng": "June Bank Holiday", "gle": "Lá Saoire i mí an Mheithimh"}),
    weekday_from(0, 8, 1, {"eng": "August Bank Holiday", "gle": "Lá Saoire i mí Lúnasa"}),
    weekday_from(0, 10, 25, {"eng": "October Bank Holiday", "gle": "Lá Saoire i mí Dheireadh Fómhair"}),
    fixed(12, 25, {"eng": "Christmas Day", "gle": "Lá Nollag"}),
    fixed(12, 26, {"eng": "Saint Stephen's Day", "gle": "Lá Fhéile Stiofáin"}),
)


def cro_number(rng):
    return f"CRO {rng.randint(500000, 799999)}"


# --- VAT number: IE + 7 digits + check letter (+ "A" or "H" in the 2013 format) ----------------------------------
# check = ALPHABET[(8·d1 + 7·d2 + ... + 2·d7 + 9·index(second letter)) mod 23], ALPHABET = "WABC...V".
_ALPHABET = "WABCDEFGHIJKLMNOPQRSTUV"


def _ie_check(seven: str, second: str = "") -> str:
    total = sum((8 - i) * int(d) for i, d in enumerate(seven)) + (9 * _ALPHABET.index(second) if second else 0)
    return _ALPHABET[total % 23]


def ie_vat(rng, _cro=None):
    seven = str(rng.randint(1, 9)) + "".join(rng.choice(string.digits) for _ in range(6))
    second = rng.choice(("", "A", "H"))
    return "IE" + seven + _ie_check(seven, second) + second


def ie_vat_valid(value: str) -> bool:
    s = value.replace(" ", "").replace("-", "").upper()
    if not s.startswith("IE"):
        return False
    s = s[2:]
    if len(s) not in (8, 9) or not all(ch in _ALPHABET for ch in s[7:]):
        return False
    if s[:7].isdigit():                                   # current formats: 1234567X, 1234567XA
        return s[7] == _ie_check(s[:7], s[8:])
    if s[0].isdigit() and s[1] in string.ascii_uppercase + "+*" and s[2:7].isdigit() and len(s) == 8:
        return s[7] == _ie_check(("0" + s[2:7] + s[0]))   # pre-2013 format, e.g. 8D79739I
    return False


LOCALE = Locale(
    country="IE", name="Ireland", languages=("eng", "gle"),
    money=MoneyFormat("EUR", "€", ".", ",", symbol_first=True),
    timezone="Europe/Dublin",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2300, "food": 0, "accommodation": 1350, "books": 0, "passenger_transport": 0,
            "restaurant": 1350},
    vat_as_of="2025",
    vat_source="Value-Added Tax Consolidation Act 2010, Schedules 2–3 (23 %; basic food and printed books 0 %; "
               "accommodation and restaurant/catering 13.5 %; domestic passenger transport exempt); Revenue VAT "
               "rates database; EU Taxes in Europe Database",
    company_id=cro_number,
    vat_id=ie_vat,                                  # the VAT number is not derived from the CRO number
    vat_id_valid=ie_vat_valid,
    payment_reference=banking.rf_reference,
    payment_reference_name={"eng": "payment reference (RF)", "gle": "tagairt íocaíochta (RF)"},
    company_suffixes=("Ltd", "DAC", "PLC"),
    company_stems=("Glenmore", "Ardmore", "Corrib Bay", "Rathmore", "Kilbride", "Ballyvale", "Shannonside",
                   "Slievemore", "Bramblewood", "Inchmore"),
    first_names=("Seán", "Aoife", "Conor", "Siobhán", "Niamh", "Patrick", "Ciara", "Darragh", "Emma", "Liam",
                 "Orla", "Cian"),
    last_names=("Murphy", "Kelly", "O'Sullivan", "Walsh", "Smith", "O'Brien", "Byrne", "Ryan", "O'Connor",
                "O'Neill", "Doyle", "McCarthy"),
    cities=("Dublin", "Cork", "Galway", "Limerick", "Waterford", "Kilkenny", "Sligo", "Athlone"),
    office_hours=("09:00", "17:30"), lunch=("13:00", "14:00"),
    date_style="DD/MM/YYYY",
    notes=["Basic food and printed books are zero-rated and domestic passenger transport is exempt: these "
           "categories carry 0 % VAT.",
           "The hospitality rate (13.5 %) is scheduled to fall to 9 % for restaurant food from July 2026 (not in "
           "this 2025 snapshot).",
           "Money is written €1,234.56 (symbol first, comma grouping, decimal point)."],
)
