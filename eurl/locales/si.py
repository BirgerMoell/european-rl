import random

from eurl import banking
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"slv": "novo leto"}),
    fixed(1, 2, {"slv": "novo leto"}),
    fixed(2, 8, {"slv": "Prešernov dan, slovenski kulturni praznik"}),
    easter_rule(0, {"slv": "velikonočna nedelja"}),
    easter_rule(1, {"slv": "velikonočni ponedeljek"}),
    fixed(4, 27, {"slv": "dan upora proti okupatorju"}),
    fixed(5, 1, {"slv": "praznik dela"}),
    fixed(5, 2, {"slv": "praznik dela"}),
    easter_rule(49, {"slv": "binkoštna nedelja"}),
    fixed(6, 25, {"slv": "dan državnosti"}),
    fixed(8, 15, {"slv": "Marijino vnebovzetje"}),
    fixed(10, 31, {"slv": "dan reformacije"}),
    fixed(11, 1, {"slv": "dan spomina na mrtve"}),
    fixed(12, 25, {"slv": "božič"}),
    fixed(12, 26, {"slv": "dan samostojnosti in enotnosti"}),
)


def _ddv_check(base: str) -> int:
    """Davčna številka: weights 8..2, 11 - (sum mod 11); 10 -> 0, 11 -> no valid number."""
    c = 11 - sum((8 - i) * int(d) for i, d in enumerate(base)) % 11
    return 0 if c == 10 else c


def ddv(rng: random.Random) -> str:
    while True:
        base = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(6))
        c = _ddv_check(base)
        if c < 10:
            return "SI" + base + str(c)


def ddv_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if not s.startswith("SI"):
        return False
    s = s[2:]
    return len(s) == 8 and s.isdigit() and s[0] != "0" and _ddv_check(s[:7]) == int(s[7])


def maticna(rng: random.Random) -> str:
    """Matična številka (AJPES): 7 digits with a MOD 11 check digit (weights 7..2), plus the unit code 000."""
    while True:
        base = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(5))
        r = -sum(w * int(d) for w, d in zip((7, 6, 5, 4, 3, 2), base)) % 11
        if r:
            return base + str(r % 10) + "000"


LOCALE = Locale(
    country="SI", name="Slovenia", languages=("slv",),
    money=MoneyFormat("EUR", "€", ",", "."),
    timezone="Europe/Ljubljana",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2200, "food": 950, "accommodation": 950, "books": 500, "passenger_transport": 950,
            "restaurant": 950},
    vat_as_of="2025",
    vat_source="Zakon o davku na dodano vrednost (ZDDV-1), 41. člen, prilogi I in IV; FURS; EU Taxes in Europe "
               "Database",
    company_id=maticna,
    vat_id=lambda rng, _maticna: ddv(rng), vat_id_valid=ddv_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"slv": "referenca (RF)"},
    company_suffixes=("d.o.o.", "d.d."),
    company_stems=("Lipnica", "Brezovec", "Javornik", "Smrekovec", "Bukovje", "Savinja", "Kamnik", "Gorjanec",
                   "Hrastje", "Vrbica"),
    first_names=("Luka", "Maja", "Marko", "Nina", "Jan", "Eva", "Matej", "Ana", "Žiga", "Sara", "Andrej", "Katja"),
    last_names=("Novak", "Horvat", "Kovačič", "Krajnc", "Zupančič", "Potočnik", "Kovač", "Mlakar", "Kos", "Vidmar",
                "Golob", "Turk"),
    cities=("Ljubljana", "Maribor", "Celje", "Kranj", "Koper", "Velenje", "Novo mesto", "Ptuj"),
    date_style="D. M. YYYY",
    office_hours=("08:00", "16:00"), lunch=("12:00", "12:30"),
    notes=["Reduced rate 9.5 % (food, accommodation, passenger transport, restaurant food), 5 % (books).",
           "The davčna številka (VAT number) is assigned separately from the matična številka."],
)
