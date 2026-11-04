"""Serbia (non-EU). Business text in Cyrillic, the official script."""
import string

from eurl.calendar import fixed, orthodox_rule
from eurl.locales import Locale
from eurl.money import MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"srp": "Нова година"}),
    fixed(1, 2, {"srp": "Нова година (други дан)"}),
    fixed(1, 7, {"srp": "Божић"}),
    fixed(2, 15, {"srp": "Сретење – Дан државности Србије"}),
    fixed(2, 16, {"srp": "Сретење – Дан државности Србије (други дан)"}),
    orthodox_rule(-2, {"srp": "Велики петак"}),
    orthodox_rule(-1, {"srp": "Велика субота"}),
    orthodox_rule(0, {"srp": "Васкрс"}),
    orthodox_rule(1, {"srp": "Други дан Васкрса"}),
    fixed(5, 1, {"srp": "Празник рада"}),
    fixed(5, 2, {"srp": "Празник рада (други дан)"}),
    fixed(11, 11, {"srp": "Дан примирја у Првом светском рату"}),
)


# --- PIB (9 digits): ISO 7064 MOD 11,10 check digit. The PIB is also the VAT number. ----------------------------

def _mod11_10(digits: str) -> str:
    product = 10
    for ch in digits:
        total = (int(ch) + product) % 10 or 10
        product = (2 * total) % 11
    return str((11 - product) % 10)


def pib(rng) -> str:
    body = "1" + "".join(rng.choice(string.digits) for _ in range(7))
    return body + _mod11_10(body)


def vat_id(rng, company: str) -> str:
    return company


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return len(s) == 9 and s.isdigit() and _mod11_10(s[:8]) == s[8]


# --- Poziv na broj, model 97: two ISO 7064 MOD 97-10 check digits before the reference body --------------------

def model97(rng) -> str:
    body = "".join(rng.choice(string.digits) for _ in range(10))
    check = 98 - int(body + "00") % 97
    return f"97 {check:02d}{body}"


def model97_valid(value: str) -> bool:
    s = value.replace(" ", "").replace("-", "")
    return len(s) >= 5 and s.isdigit() and s[:2] == "97" and int(s[4:] + s[2:4]) % 97 == 1


LOCALE = Locale(
    country="RS", name="Serbia", languages=("srp",),
    money=MoneyFormat("RSD", "дин.", ",", "."),
    timezone="Europe/Belgrade",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2000, "food": 1000, "accommodation": 1000, "books": 1000, "passenger_transport": 1000,
            "restaurant": 2000},
    vat_as_of="2025",
    vat_source="Закон о порезу на додату вредност, чл. 23 (стопе 20 % и 10 %); Пореска управа; PwC Worldwide Tax "
               "Summaries (Serbia, other taxes)",
    company_id=pib, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=model97, payment_reference_name={"srp": "позив на број (модел 97)"},
    company_suffixes=("д.о.о.", "а.д."),
    company_stems=("Морава", "Јавор", "Липа", "Бели извор", "Зелени гај", "Храст", "Сунчани брег", "Брезовица",
                   "Кладенац", "Ведро небо"),
    first_names=("Милица", "Марко", "Јована", "Никола", "Ана", "Стефан", "Тамара", "Лука", "Јелена", "Филип",
                 "Ивана", "Милош"),
    last_names=("Јовановић", "Петровић", "Марковић", "Ђорђевић", "Стојановић", "Илић", "Станковић", "Павловић",
                "Ђурић", "Костић", "Лазић", "Поповић"),
    cities=("Београд", "Нови Сад", "Ниш", "Крагујевац", "Суботица", "Чачак", "Краљево", "Зрењанин"),
    eu_member=False,
    price_scale=117,
    date_style="DD.MM.YYYY.",
    office_hours=("08:00", "16:00"), lunch=("12:00", "12:30"),
    notes=[
        "Non-EU: VAT (ПДВ) standard 20 %; 10 % for basic food, hotel accommodation, books and other monographic "
        "publications, and passenger transport. Restaurant services are standard-rated.",
        "Holidays: Закон о државним и другим празницима у Републици Србији, national (non-working) holidays with "
        "Orthodox Easter (Good Friday to Easter Monday). NOT MODELLED: when New Year, Statehood Day, Labour Day or "
        "Armistice Day falls on a Sunday, the next working day is a day off (e.g. 2025-02-17); religious holidays "
        "of other confessions (for their members only) are also not modelled.",
        "Company/VAT number: PIB (9 digits, ISO 7064 MOD 11,10 check digit). The 8-digit matični broj is not "
        "generated.",
        "Payment reference: poziv na broj with model 97 (ISO 7064 MOD 97-10 check digits), written '97 cc...'.",
    ],
)
