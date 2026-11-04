import random

from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

# Zákon č. 241/1993 Z. z. as amended: 1 September is a state holiday but a working day since 2024 (530/2023);
# 17 November a working day since 2025; 8 May and 15 September are working days in 2026 only (261/2025).
HOLIDAYS = (
    fixed(1, 1, {"slk": "Deň vzniku Slovenskej republiky"}),
    fixed(1, 6, {"slk": "Zjavenie Pána (Traja králi)"}),
    easter_rule(-2, {"slk": "Veľký piatok"}),
    easter_rule(1, {"slk": "Veľkonočný pondelok"}),
    fixed(5, 1, {"slk": "Sviatok práce"}),
    fixed(5, 8, {"slk": "Deň víťazstva nad fašizmom"}, until=2025),
    fixed(5, 8, {"slk": "Deň víťazstva nad fašizmom"}, since=2027),
    fixed(7, 5, {"slk": "Sviatok svätého Cyrila a svätého Metoda"}),
    fixed(8, 29, {"slk": "Výročie Slovenského národného povstania"}),
    fixed(9, 1, {"slk": "Deň Ústavy Slovenskej republiky"}, until=2023),
    fixed(9, 15, {"slk": "Sedembolestná Panna Mária"}, until=2025),
    fixed(9, 15, {"slk": "Sedembolestná Panna Mária"}, since=2027),
    fixed(11, 1, {"slk": "Sviatok Všetkých svätých"}),
    fixed(11, 17, {"slk": "Deň boja za slobodu a demokraciu"}, until=2024),
    fixed(12, 24, {"slk": "Štedrý deň"}),
    fixed(12, 25, {"slk": "Prvý sviatok vianočný"}),
    fixed(12, 26, {"slk": "Druhý sviatok vianočný"}),
)


def ico_check(base: str) -> str:
    """IČO check digit (shared with the Czech scheme): weights 8..2, 11 - (sum mod 11); 10 -> 0, 11 -> 1."""
    c = (11 - sum((8 - i) * int(d) for i, d in enumerate(base)) % 11) % 11
    return str((c or 1) % 10)


def ico(rng: random.Random) -> str:
    """Identifikačné číslo organizácie (8 digits)."""
    base = str(rng.randint(3, 5)) + "".join(str(rng.randint(0, 9)) for _ in range(6))
    return base + ico_check(base)


def ic_dph(rng: random.Random) -> str:
    """IČ DPH: SK + DIČ (10 digits, first not 0, third in 2 3 4 7 8 9, the number divisible by 11)."""
    while True:
        base = "20" + str(rng.choice((2, 3, 4, 7, 8, 9))) + "".join(str(rng.randint(0, 9)) for _ in range(6))
        check = -int(base) * 10 % 11
        if check < 10:
            return "SK" + base + str(check)


def ic_dph_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if not s.startswith("SK"):
        return False
    s = s[2:]
    return len(s) == 10 and s.isdigit() and s[0] != "0" and s[2] in "234789" and int(s) % 11 == 0


def variabilny_symbol(rng: random.Random) -> str:
    """Variabilný symbol: up to 10 digits, no check digit; usually the invoice number."""
    return "2025" + "".join(str(rng.randint(0, 9)) for _ in range(6))


LOCALE = Locale(
    country="SK", name="Slovakia", languages=("slk",),
    money=MoneyFormat("EUR", "€", ",", NBSP),
    timezone="Europe/Bratislava",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2300, "food": 500, "accommodation": 500, "books": 500, "passenger_transport": 2300,
            "restaurant": 500},
    vat_as_of="2025",
    vat_source="Zákon č. 222/2004 Z. z. o DPH, § 27 a prílohy 7 a 7a (zákon 278/2024: 23 % / 19 % / 5 % od "
               "2025-01-01); Finančná správa SR",
    company_id=ico,
    vat_id=lambda rng, _ico: ic_dph(rng), vat_id_valid=ic_dph_valid,
    payment_reference=variabilny_symbol, payment_reference_name={"slk": "variabilný symbol"},
    company_suffixes=("s.r.o.", "a.s."),
    company_stems=("Javorina", "Lipovec", "Brezina", "Hronka", "Tatranec", "Dubovec", "Jedlina", "Smrekovec",
                   "Kamenec", "Vršky"),
    first_names=("Peter", "Jana", "Martin", "Mária", "Tomáš", "Zuzana", "Michal", "Katarína", "Lukáš", "Lucia",
                 "Juraj", "Monika"),
    last_names=("Horváth", "Kováč", "Varga", "Tóth", "Nagy", "Baláž", "Szabó", "Molnár", "Lukáč", "Kollár",
                "Novák", "Oravec"),
    cities=("Bratislava", "Košice", "Prešov", "Žilina", "Nitra", "Banská Bystrica", "Trnava", "Trenčín"),
    date_style="D. M. YYYY",
    office_hours=("08:00", "16:30"), lunch=("12:00", "12:30"),
    notes=["From 2025: 23 % standard, 19 % (other foods, non-alcoholic drinks served in restaurants), 5 % (basic "
           "foods, books, accommodation, food served in restaurants). Domestic passenger transport is taxed at "
           "the standard rate.",
           "8 May and 15 September are working days in 2026 only (zákon 261/2025); 17 November is a working day "
           "from 2025; 1 September from 2024.",
           "The IČ DPH is assigned by the tax office and is not derived from the IČO. Surnames are given in the "
           "masculine form; feminine forms differ (Kováč / Kováčová)."],
)
