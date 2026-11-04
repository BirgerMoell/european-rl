import random

from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"ces": "Den obnovy samostatného českého státu; Nový rok"}),
    easter_rule(-2, {"ces": "Velký pátek"}),
    easter_rule(1, {"ces": "Velikonoční pondělí"}),
    fixed(5, 1, {"ces": "Svátek práce"}),
    fixed(5, 8, {"ces": "Den vítězství"}),
    fixed(7, 5, {"ces": "Den slovanských věrozvěstů Cyrila a Metoděje"}),
    fixed(7, 6, {"ces": "Den upálení mistra Jana Husa"}),
    fixed(9, 28, {"ces": "Den české státnosti"}),
    fixed(10, 28, {"ces": "Den vzniku samostatného československého státu"}),
    fixed(11, 17, {"ces": "Den boje za svobodu a demokracii a Mezinárodní den studentstva"}),
    fixed(12, 24, {"ces": "Štědrý den"}),
    fixed(12, 25, {"ces": "1. svátek vánoční"}),
    fixed(12, 26, {"ces": "2. svátek vánoční"}),
)


def ico_check(base: str) -> str:
    """IČO check digit: weights 8..2, c = 11 - (sum mod 11); 10 -> 0, 11 -> 1."""
    c = (11 - sum((8 - i) * int(d) for i, d in enumerate(base)) % 11) % 11
    return str((c or 1) % 10)


def ico(rng: random.Random) -> str:
    """Identifikační číslo osoby of a legal entity (8 digits)."""
    base = str(rng.randint(0, 8)) + "".join(str(rng.randint(0, 9)) for _ in range(6))
    return base + ico_check(base)


def ico_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return len(s) == 8 and s.isdigit() and ico_check(s[:7]) == s[7]


def dic_valid(value: str) -> bool:
    """DIČ of a legal entity: CZ + IČO (the first digit is not 9)."""
    s = value.replace(" ", "").upper()
    return s.startswith("CZ") and ico_valid(s[2:]) and s[2] != "9"


def variabilni_symbol(rng: random.Random) -> str:
    """Variabilní symbol: up to 10 digits, no check digit; usually the invoice number."""
    return "2025" + "".join(str(rng.randint(0, 9)) for _ in range(6))


LOCALE = Locale(
    country="CZ", name="Czechia", languages=("ces",),
    money=MoneyFormat("CZK", "Kč", ",", NBSP),
    timezone="Europe/Prague",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2100, "food": 1200, "accommodation": 1200, "books": 0, "passenger_transport": 1200,
            "restaurant": 1200},
    vat_as_of="2025",
    vat_source="Zákon č. 235/2004 Sb., o dani z přidané hodnoty, § 47 a § 71i (books 0 % since 2024-01-01; one "
               "reduced rate of 12 % since 2024); Finanční správa; EU Taxes in Europe Database",
    company_id=ico,
    vat_id=lambda rng, number: "CZ" + number, vat_id_valid=dic_valid,
    payment_reference=variabilni_symbol, payment_reference_name={"ces": "variabilní symbol"},
    company_suffixes=("s.r.o.", "a.s.", "v.o.s."),
    company_stems=("Lipovka", "Javorník", "Bukovec", "Dubina", "Vltavín", "Skalka", "Jezerka", "Habrovka",
                   "Modřín", "Olšina"),
    first_names=("Jan", "Jana", "Petr", "Eva", "Tomáš", "Lucie", "Martin", "Kateřina", "Jakub", "Tereza", "Lukáš",
                 "Veronika"),
    last_names=("Novák", "Svoboda", "Novotný", "Dvořák", "Černý", "Procházka", "Kučera", "Veselý", "Horák",
                "Němec", "Marek", "Pokorný"),
    cities=("Praha", "Brno", "Ostrava", "Plzeň", "Liberec", "Olomouc", "České Budějovice", "Hradec Králové"),
    price_scale=25,
    date_style="D. M. YYYY",
    office_hours=("08:00", "16:30"), lunch=("12:00", "12:30"),
    notes=["Books are zero-rated (0 %) since 1 January 2024; the reduced rates 10 % and 15 % were merged into 12 %.",
           "The payment reference is the variabilní symbol (no check digit), as used for domestic CZK payments.",
           "Surnames are given in the masculine form; feminine forms differ (Novák / Nováková)."],
)
