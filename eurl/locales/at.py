from eurl import banking
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

# Feiertagsruhegesetz 1957 § 7 and Staatsfeiertag 1 May: the nationwide statutory days off. Good Friday was a
# holiday for some churches until 2019 and is no longer one. Christmas Eve and New Year's Eve are ordinary working
# days by law (many collective agreements give them off, at least from noon); Länder patron days (e.g. Leopold in
# Vienna and Lower Austria, Rupert in Salzburg) are not statutory days off.
HOLIDAYS = (
    fixed(1, 1, {"deu": "Neujahr"}),
    fixed(1, 6, {"deu": "Heilige Drei Könige"}),
    easter_rule(1, {"deu": "Ostermontag"}),
    fixed(5, 1, {"deu": "Staatsfeiertag"}),
    easter_rule(39, {"deu": "Christi Himmelfahrt"}),
    easter_rule(50, {"deu": "Pfingstmontag"}),
    easter_rule(60, {"deu": "Fronleichnam"}),
    fixed(8, 15, {"deu": "Mariä Himmelfahrt"}),
    fixed(10, 26, {"deu": "Nationalfeiertag"}),
    fixed(11, 1, {"deu": "Allerheiligen"}),
    fixed(12, 8, {"deu": "Mariä Empfängnis"}),
    fixed(12, 25, {"deu": "Christtag"}),
    fixed(12, 26, {"deu": "Stephanstag"}),
)

# --- Firmenbuchnummer: up to six digits and a check letter ------------------------------------------------------
# The check letter: digits right-aligned to six places, weights 6 4 14 15 10 1, sum mod 17 indexes the alphabet
# below (e.g. FN 122119m).
_FN_WEIGHTS = (6, 4, 14, 15, 10, 1)
_FN_LETTERS = "abdfghikmpstvwxyz"


def _fn_letter(number: str) -> str:
    digits = number.zfill(6)
    return _FN_LETTERS[sum(w * int(d) for w, d in zip(_FN_WEIGHTS, digits)) % 17]


def firmenbuchnummer(rng):
    number = str(rng.randint(100000, 649999))
    return f"FN {number}{_fn_letter(number)}"


def firmenbuchnummer_valid(value: str) -> bool:
    s = value.replace(" ", "")
    if s[:2].upper() == "FN":
        s = s[2:]
    return 2 <= len(s) <= 7 and s[:-1].isdigit() and s[-1].lower() == _fn_letter(s[:-1])


# --- UID-Nummer: ATU + 7 digits + check digit ------------------------------------------------------------------
# S = c1 + q(2·c2) + c3 + q(2·c4) + c5 + q(2·c6) + c7 (q = digit sum); check = (10 - (S + 4) mod 10) mod 10.

def _uid_check(seven: str) -> str:
    total = 0
    for i, ch in enumerate(seven):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            d = d - 9 if d > 9 else d
        total += d
    return str((10 - (total + 4) % 10) % 10)


def uid(rng, _firmenbuch=None):
    seven = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(6))
    return "ATU" + seven + _uid_check(seven)


def uid_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    return len(s) == 11 and s.startswith("ATU") and s[3:].isdigit() and _uid_check(s[3:10]) == s[10]


LOCALE = Locale(
    country="AT", name="Austria", languages=("deu",),
    money=MoneyFormat("EUR", "€" + NBSP, ",", ".", symbol_first=True),
    timezone="Europe/Vienna",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2000, "food": 1000, "accommodation": 1000, "books": 1000, "passenger_transport": 1000,
            "restaurant": 1000},
    vat_as_of="2025",
    vat_source="Umsatzsteuergesetz 1994 § 10 (20 %; 10 % for food, accommodation, books, passenger transport and "
               "restaurant food; drinks in restaurants 20 %); BMF; EU Taxes in Europe Database",
    company_id=firmenbuchnummer,
    vat_id=uid,                                    # the UID is not derived from the Firmenbuch number
    vat_id_valid=uid_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"deu": "Zahlungsreferenz (RF-Referenz)"},
    company_suffixes=("GmbH", "AG", "KG", "OG"),
    company_stems=("Donaublick", "Almhof", "Lindenau", "Tauernstein", "Seewinkel", "Kalkalpen", "Murtal",
                   "Grünberg", "Wienerwald", "Mondsee"),
    first_names=("Anna", "Lukas", "Katharina", "Tobias", "Julia", "Florian", "Sophie", "Stefan", "Lena",
                 "Michael", "Elena", "Matthias"),
    last_names=("Gruber", "Huber", "Bauer", "Wagner", "Müller", "Pichler", "Steiner", "Moser", "Mayer", "Hofer",
                "Leitner", "Berger"),
    cities=("Wien", "Graz", "Linz", "Salzburg", "Innsbruck", "Klagenfurt", "Villach", "St. Pölten"),
    office_hours=("08:00", "17:00"), lunch=("12:00", "13:00"),
    date_style="DD.MM.YYYY",
    notes=["Money is written with the symbol first, € 1.234,56 (CLDR de-AT); '1.234,56 €' is also seen.",
           "Holidays are the nationwide statutory set; 24 and 31 December are working days by law (often off by "
           "collective agreement). Länder patron days are not modelled.",
           "Firmenbuchnummer check letter: weights 6 4 14 15 10 1, mod 17 (not cross-checked: stdnum only checks "
           "the format)."],
)
