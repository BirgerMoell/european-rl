import random

from eurl import banking
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"nor": "første nyttårsdag"}),
    easter_rule(-3, {"nor": "skjærtorsdag"}),
    easter_rule(-2, {"nor": "langfredag"}),
    easter_rule(0, {"nor": "første påskedag"}),
    easter_rule(1, {"nor": "andre påskedag"}),
    fixed(5, 1, {"nor": "arbeidernes dag"}),
    fixed(5, 17, {"nor": "grunnlovsdag"}),
    easter_rule(39, {"nor": "Kristi himmelfartsdag"}),
    easter_rule(49, {"nor": "første pinsedag"}),
    easter_rule(50, {"nor": "andre pinsedag"}),
    fixed(12, 25, {"nor": "første juledag"}),
    fixed(12, 26, {"nor": "andre juledag"}),
)

_ORGNR_W = (3, 2, 7, 6, 5, 4, 3, 2)


def _orgnr_check(base: str) -> int:
    """MOD 11 with weights 3 2 7 6 5 4 3 2; 11 -> 0, 10 -> no valid number."""
    return -sum(w * int(d) for w, d in zip(_ORGNR_W, base)) % 11


def orgnr_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return len(s) == 9 and s.isdigit() and _orgnr_check(s[:8]) == int(s[8])


def orgnr(rng: random.Random) -> str:
    """Organisasjonsnummer (Brønnøysundregistrene), 9 digits starting with 8 or 9, shown as 'ddd ddd ddd'."""
    while True:
        base = str(rng.choice((8, 9))) + "".join(str(rng.randint(0, 9)) for _ in range(7))
        check = _orgnr_check(base)
        if check < 10:
            s = base + str(check)
            return f"{s[:3]} {s[3:6]} {s[6:]}"


def mva(number: str) -> str:
    """MVA-registered businesses: 'NO' + organisasjonsnummer + 'MVA'."""
    return "NO" + number.replace(" ", "") + "MVA"


def mva_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    return s.startswith("NO") and s.endswith("MVA") and orgnr_valid(s[2:-3])


LOCALE = Locale(
    country="NO", name="Norway", languages=("nor",),
    money=MoneyFormat("NOK", "kr", ",", NBSP),
    timezone="Europe/Oslo",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2500, "food": 1500, "accommodation": 1200, "books": 0, "passenger_transport": 1200,
            "restaurant": 2500},
    vat_as_of="2025",
    vat_source="Merverdiavgiftsloven §§ 5-1, 5-2, 6-4 (books zero-rated); Stortingets avgiftsvedtak 2025; "
               "Skatteetaten",
    company_id=orgnr,
    vat_id=lambda rng, number: mva(number), vat_id_valid=mva_valid,
    payment_reference=banking.kid_no, payment_reference_name={"nor": "KID-nummer"},
    company_suffixes=("AS", "ASA", "DA"),
    company_stems=("Fjellheim", "Bjørkely", "Granli", "Solvang", "Havbris", "Lyngmo", "Elvetun", "Sjøgløtt",
                   "Fossheim", "Furuli"),
    first_names=("Ingrid", "Ole", "Kari", "Lars", "Nora", "Henrik", "Emma", "Sindre", "Ida", "Magnus", "Silje",
                 "Erlend"),
    last_names=("Hansen", "Johansen", "Olsen", "Larsen", "Andersen", "Pedersen", "Nilsen", "Kristiansen", "Jensen",
                "Karlsen", "Berg", "Haugen"),
    cities=("Oslo", "Bergen", "Trondheim", "Stavanger", "Tromsø", "Kristiansand", "Drammen", "Bodø"),
    eu_member=False,
    price_scale=11,
    date_style="DD.MM.YYYY",
    office_hours=("08:00", "16:00"), lunch=("11:30", "12:00"),
    notes=["Non-EU (EEA): merverdiavgift (MVA). Standard 25 %, food 15 %, accommodation and passenger transport "
           "12 %, printed books 0 % (zero-rated); food served in restaurants 25 % (take-away 15 %).",
           "Christmas Eve and New Year's Eve are customary half days (offices close around 12:00); not modelled."],
)
