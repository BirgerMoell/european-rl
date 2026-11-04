import random

from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"est": "uusaasta"}),
    fixed(2, 24, {"est": "iseseisvuspäev"}),
    easter_rule(-2, {"est": "suur reede"}),
    easter_rule(0, {"est": "ülestõusmispühade 1. püha"}),
    fixed(5, 1, {"est": "kevadpüha"}),
    easter_rule(49, {"est": "nelipühade 1. püha"}),
    fixed(6, 23, {"est": "võidupüha"}),
    fixed(6, 24, {"est": "jaanipäev"}),
    fixed(8, 20, {"est": "taasiseseisvumispäev"}),
    fixed(12, 24, {"est": "jõululaupäev"}),
    fixed(12, 25, {"est": "esimene jõulupüha"}),
    fixed(12, 26, {"est": "teine jõulupüha"}),
)


def _mod11(digits: str) -> str:
    """Estonian MOD 11 (as in isikukood): weights 1..9,1 then 3..9,1,2; 10 -> 0."""
    check = sum((i % 9 + 1) * int(d) for i, d in enumerate(digits)) % 11
    if check == 10:
        check = sum(((i + 2) % 9 + 1) * int(d) for i, d in enumerate(digits)) % 11
    return str(check % 10)


def registrikood(rng: random.Random) -> str:
    """Registrikood of a commercial company (äriregister): 8 digits starting with 1."""
    base = "1" + "".join(str(rng.randint(0, 9)) for _ in range(6))
    return base + _mod11(base)


def registrikood_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return len(s) == 8 and s.isdigit() and s[0] in "1789" and _mod11(s[:7]) == s[7]


_KMKR_W = (3, 7, 1, 3, 7, 1, 3, 7, 1)


def kmkr(rng: random.Random) -> str:
    """KMKR number: EE + 9 digits (issued from 10...), weights 3 7 1, weighted sum divisible by 10."""
    base = "10" + "".join(str(rng.randint(0, 9)) for _ in range(6))
    check = -sum(w * int(d) for w, d in zip(_KMKR_W, base)) % 10
    return "EE" + base + str(check)


def kmkr_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if not s.startswith("EE"):
        return False
    s = s[2:]
    return len(s) == 9 and s.isdigit() and sum(w * int(d) for w, d in zip(_KMKR_W, s)) % 10 == 0


def _viitenumber_check(base: str) -> str:
    weights = (7, 3, 1)
    total = sum(int(d) * weights[i % 3] for i, d in enumerate(reversed(base)))
    return str(-total % 10)


def viitenumber(rng: random.Random, base_length: int = 9) -> str:
    """Estonian bank reference number (viitenumber), 7-3-1 method (Pangaliit standard)."""
    base = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(base_length - 1))
    return base + _viitenumber_check(base)


def viitenumber_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return s.isdigit() and 2 <= len(s) <= 20 and _viitenumber_check(s[:-1]) == s[-1]


LOCALE = Locale(
    country="EE", name="Estonia", languages=("est",),
    money=MoneyFormat("EUR", "€", ",", NBSP),
    timezone="Europe/Tallinn",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2400, "food": 2400, "accommodation": 1300, "books": 900, "passenger_transport": 2400,
            "restaurant": 2400},
    vat_as_of="2025",
    vat_source="Käibemaksuseadus § 15 (standard 24 % from 2025-07-01, 22 % before; accommodation 13 % from "
               "2025-01-01; books 9 %); Maksu- ja Tolliamet (EMTA); EU Taxes in Europe Database",
    company_id=registrikood,
    vat_id=lambda rng, _code: kmkr(rng), vat_id_valid=kmkr_valid,
    payment_reference=viitenumber, payment_reference_name={"est": "viitenumber"},
    company_suffixes=("OÜ", "AS"),
    company_stems=("Kadaka", "Männisalu", "Põhjaranna", "Järveotsa", "Kuusiku", "Pihlaka", "Lepiku", "Tammeoru",
                   "Kivisilla", "Kaasiku"),
    first_names=("Mari", "Jaan", "Kadri", "Andres", "Liis", "Martin", "Kristiina", "Toomas", "Laura", "Rasmus",
                 "Kati", "Mihkel"),
    last_names=("Tamm", "Saar", "Sepp", "Mägi", "Kask", "Kukk", "Rebane", "Ilves", "Pärn", "Koppel", "Lepik",
                "Kuusk"),
    cities=("Tallinn", "Tartu", "Narva", "Pärnu", "Kohtla-Järve", "Viljandi", "Rakvere", "Kuressaare"),
    date_style="DD.MM.YYYY",
    office_hours=("09:00", "17:30"), lunch=("12:00", "12:30"),
    notes=["Standard VAT rate 24 % from 1 July 2025 (22 % from 1 January to 30 June 2025); the world uses 24 %.",
           "The working day before 24 February, 23 June, 24 December and 1 January is shortened by three hours "
           "(Töölepingu seadus § 53); not modelled.",
           "The KMKR (VAT) number is assigned separately from the registrikood."],
)
