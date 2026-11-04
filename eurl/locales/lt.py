import random

from eurl import banking
from eurl.calendar import easter_rule, fixed, weekday_from
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"lit": "Naujųjų metų diena"}),
    fixed(2, 16, {"lit": "Lietuvos valstybės atkūrimo diena"}),
    fixed(3, 11, {"lit": "Lietuvos nepriklausomybės atkūrimo diena"}),
    easter_rule(0, {"lit": "Velykos"}),
    easter_rule(1, {"lit": "antroji Velykų diena"}),
    fixed(5, 1, {"lit": "Tarptautinė darbo diena"}),
    weekday_from(6, 5, 1, {"lit": "Motinos diena"}),                 # first Sunday in May
    weekday_from(6, 6, 1, {"lit": "Tėvo diena"}),                    # first Sunday in June
    fixed(6, 24, {"lit": "Rasos ir Joninių diena"}),
    fixed(7, 6, {"lit": "Valstybės (Lietuvos karaliaus Mindaugo karūnavimo) diena"}),
    fixed(8, 15, {"lit": "Žolinė (Švč. Mergelės Marijos ėmimo į dangų diena)"}),
    fixed(11, 1, {"lit": "Visų šventųjų diena"}),
    fixed(11, 2, {"lit": "Mirusiųjų atminimo (Vėlinių) diena"}, since=2020),
    fixed(12, 24, {"lit": "Kūčių diena"}),
    fixed(12, 25, {"lit": "Kalėdos"}),
    fixed(12, 26, {"lit": "antroji Kalėdų diena"}),
)


def _mod11(digits: str) -> str:
    """Lithuanian MOD 11: weights 1..9,1.. then 3..9,1,2..; 10 -> 0."""
    check = sum((i % 9 + 1) * int(d) for i, d in enumerate(digits)) % 11
    if check == 10:
        check = sum(((i + 2) % 9 + 1) * int(d) for i, d in enumerate(digits)) % 11
    return str(check % 10)


def imones_kodas(rng: random.Random) -> str:
    """Juridinio asmens kodas (Registrų centras): 9 digits starting with 1 or 3, MOD 11 check digit."""
    base = str(rng.choice((1, 3))) + "".join(str(rng.randint(0, 9)) for _ in range(7))
    return base + _mod11(base)


def pvm_kodas(rng: random.Random) -> str:
    """PVM mokėtojo kodas of a legal entity: LT + 9 digits, the 8th digit is 1, MOD 11 check digit."""
    base = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(6)) + "1"
    return "LT" + base + _mod11(base)


def pvm_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if not s.startswith("LT"):
        return False
    s = s[2:]
    if not s.isdigit() or len(s) not in (9, 12) or s[-2] != "1":
        return False
    return _mod11(s[:-1]) == s[-1]


LOCALE = Locale(
    country="LT", name="Lithuania", languages=("lit",),
    money=MoneyFormat("EUR", "€", ",", NBSP),
    timezone="Europe/Vilnius",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2100, "food": 2100, "accommodation": 900, "books": 900, "passenger_transport": 900,
            "restaurant": 2100},
    vat_as_of="2025",
    vat_source="Pridėtinės vertės mokesčio įstatymas, 19 straipsnis (2025 redakcija); Valstybinė mokesčių "
               "inspekcija; EU Taxes in Europe Database",
    company_id=imones_kodas,
    vat_id=lambda rng, _code: pvm_kodas(rng), vat_id_valid=pvm_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"lit": "įmokos kodas (RF nuoroda)"},
    company_suffixes=("UAB", "AB", "MB"),
    company_stems=("Ąžuolynė", "Beržynas", "Pušynėlis", "Gintarėlis", "Šilagiris", "Upėtakis", "Liepalotas",
                   "Rasakalnis", "Vėjupis", "Ežerėlis"),
    first_names=("Lukas", "Ona", "Jonas", "Rūta", "Tomas", "Gabija", "Mantas", "Austėja", "Paulius", "Eglė",
                 "Darius", "Ieva"),
    last_names=("Kazlauskas", "Jankauskas", "Petrauskas", "Stankevičius", "Vasiliauskas", "Žukauskas", "Butkus",
                "Paulauskas", "Urbonas", "Kavaliauskas", "Navickas", "Rimkus"),
    cities=("Vilnius", "Kaunas", "Klaipėda", "Šiauliai", "Panevėžys", "Alytus", "Marijampolė", "Utena"),
    date_style="YYYY-MM-DD",
    office_hours=("08:00", "17:00"), lunch=("12:00", "12:45"),
    notes=["Rates as of 2025: standard 21 %; 9 % for accommodation, scheduled passenger transport and books. From "
           "1 January 2026 the 9 % rate is abolished (books 5 %, accommodation and passenger transport 12 %).",
           "The working day before a public holiday is one hour shorter (Darbo kodeksas, 112 str.); not modelled.",
           "The PVM code is assigned separately from the company code. Surnames are given in the masculine form; "
           "feminine forms differ (Kazlauskas / Kazlauskienė, Kazlauskaitė)."],
)
