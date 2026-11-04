import random

from eurl import banking
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import MoneyFormat

# Zakon o blagdanima, spomendanima i neradnim danima (NN 110/19), in force from 2020: Statehood Day moved from
# 25 June to 30 May, Independence Day (8 October) is no longer a holiday, Remembrance Day (18 November) added.
HOLIDAYS = (
    fixed(1, 1, {"hrv": "Nova godina"}),
    fixed(1, 6, {"hrv": "Bogojavljenje ili Sveta tri kralja"}),
    easter_rule(0, {"hrv": "Uskrs"}),
    easter_rule(1, {"hrv": "Uskrsni ponedjeljak"}),
    fixed(5, 1, {"hrv": "Praznik rada"}),
    fixed(5, 30, {"hrv": "Dan državnosti"}, since=2020),
    fixed(6, 25, {"hrv": "Dan državnosti"}, until=2019),
    easter_rule(60, {"hrv": "Tijelovo"}),
    fixed(6, 22, {"hrv": "Dan antifašističke borbe"}),
    fixed(8, 5, {"hrv": "Dan pobjede i domovinske zahvalnosti i Dan hrvatskih branitelja"}),
    fixed(8, 15, {"hrv": "Velika Gospa"}),
    fixed(10, 8, {"hrv": "Dan neovisnosti"}, until=2019),
    fixed(11, 1, {"hrv": "Svi sveti"}),
    fixed(11, 18, {"hrv": "Dan sjećanja na žrtve Domovinskog rata"}, since=2020),
    fixed(12, 25, {"hrv": "Božić"}),
    fixed(12, 26, {"hrv": "Sveti Stjepan"}),
)


def _oib_check(base: str) -> str:
    """ISO 7064 MOD 11,10 over the first 10 digits."""
    t = 10
    for d in base:
        t = (t + int(d)) % 10 or 10
        t = t * 2 % 11
    return str((11 - t) % 10)


def oib(rng: random.Random) -> str:
    """Osobni identifikacijski broj of a company (11 digits)."""
    base = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(9))
    return base + _oib_check(base)


def oib_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if s.startswith("HR"):
        s = s[2:]
    return len(s) == 11 and s.isdigit() and _oib_check(s[:10]) == s[10]


def pdv_id_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    return s.startswith("HR") and oib_valid(s)


LOCALE = Locale(
    country="HR", name="Croatia", languages=("hrv",),
    money=MoneyFormat("EUR", "€", ",", "."),
    timezone="Europe/Zagreb",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2500, "food": 500, "accommodation": 1300, "books": 500, "passenger_transport": 2500,
            "restaurant": 1300},
    vat_as_of="2025",
    vat_source="Zakon o porezu na dodanu vrijednost (NN 73/13 s izmjenama), čl. 38; Porezna uprava; EU Taxes in "
               "Europe Database",
    company_id=oib,
    vat_id=lambda rng, number: "HR" + number, vat_id_valid=pdv_id_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"hrv": "poziv na broj (RF)"},
    company_suffixes=("d.o.o.", "d.d.", "j.d.o.o."),
    company_stems=("Maslinik", "Borovina", "Lavanda", "Galebica", "Kamenjar", "Smokvica", "Lučica", "Vinogradina",
                   "Hrastovac", "Bijelka"),
    first_names=("Ivan", "Ana", "Marko", "Maja", "Luka", "Petra", "Josip", "Ivana", "Matej", "Lucija", "Tomislav",
                 "Marija"),
    last_names=("Horvat", "Kovačević", "Babić", "Marić", "Jurić", "Novak", "Knežević", "Vuković", "Marković",
                "Petrović", "Matić", "Tomić"),
    cities=("Zagreb", "Split", "Rijeka", "Osijek", "Zadar", "Pula", "Slavonski Brod", "Varaždin"),
    date_style="D. M. YYYY.",
    office_hours=("08:00", "16:00"), lunch=("12:00", "12:30"),
    notes=["Reduced rates: 5 % (basic foods such as bread, milk, eggs, fresh meat, fruit and vegetables; books), "
           "13 % (accommodation, restaurant food). Domestic passenger transport is taxed at 25 %.",
           "The VAT number is HR + OIB; the company OIB is the company identifier."],
)
