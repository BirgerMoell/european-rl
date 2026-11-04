"""North Macedonia (non-EU). Ramazan Bajram (lunar) is not modelled."""
import string

from eurl.calendar import fixed, orthodox_rule
from eurl.locales import Locale
from eurl.money import MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"mkd": "Нова година"}),
    fixed(1, 7, {"mkd": "Божиќ (прв ден)"}),
    orthodox_rule(1, {"mkd": "Велигден (втор ден)"}),
    fixed(5, 1, {"mkd": "Ден на трудот"}),
    fixed(5, 24, {"mkd": "Светите Кирил и Методиј – Ден на сесловенските просветители"}),
    fixed(8, 2, {"mkd": "Ден на Републиката"}),
    fixed(9, 8, {"mkd": "Ден на независноста"}),
    fixed(10, 11, {"mkd": "Ден на народното востание"}),
    fixed(10, 23, {"mkd": "Ден на македонската револуционерна борба"}),
    fixed(12, 8, {"mkd": "Свети Климент Охридски"}),
    # One-off non-working days: presidential and parliamentary election days 2024.
    fixed(4, 24, {"mkd": "Ден на изборите"}, since=2024, until=2024),
    fixed(5, 8, {"mkd": "Ден на изборите"}, since=2024, until=2024),
)

# Lunar holiday the rule engine cannot express (excluded from HOLIDAYS and from the holiday comparison).
LUNAR_HOLIDAYS = ("Рамазан Бајрам",)

_W = (7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


# --- ЕДБ (13 digits, legal entities start with 4): weights 7..2 repeated, (-sum mod 11) mod 10. VAT = MK + ЕДБ --

def _edb_check(body12: str) -> str:
    return str((-sum(w * int(d) for w, d in zip(_W, body12)) % 11) % 10)


def edb(rng) -> str:
    body = "40" + "".join(rng.choice(string.digits) for _ in range(10))
    return body + _edb_check(body)


def vat_id(rng, company: str) -> str:
    return "MK" + company


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "").replace("-", "").upper()
    for prefix in ("MK", "МК"):
        if s.startswith(prefix):
            s = s[2:]
            break
    else:
        return False
    return len(s) == 13 and s.isdigit() and _edb_check(s[:12]) == s[12]


def invoice_reference(rng) -> str:
    """No national structured reference for commercial payments: the invoice number is quoted."""
    return f"{rng.randint(1, 99999):05d}/2025"


LOCALE = Locale(
    country="MK", name="North Macedonia", languages=("mkd",),
    money=MoneyFormat("MKD", "ден.", ",", "."),
    timezone="Europe/Skopje",
    holidays=HOLIDAYS,
    vat_bp={"standard": 1800, "food": 500, "accommodation": 500, "books": 500, "passenger_transport": 500,
            "restaurant": 1000},
    vat_as_of="2025",
    vat_source="Закон за данокот на додадена вредност (стапки 18 %, 10 %, 5 %); Управа за јавни приходи; PwC "
               "Worldwide Tax Summaries (North Macedonia, other taxes)",
    company_id=edb, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=invoice_reference, payment_reference_name={"mkd": "број на фактура"},
    company_suffixes=("ДООЕЛ", "ДОО", "АД"),
    company_stems=("Бела вода", "Зелен рид", "Липа", "Јасен", "Сончев брег", "Бистра река", "Даб", "Ведрина",
                   "Злато поле", "Езерски брег"),
    first_names=("Ана", "Александар", "Елена", "Марко", "Марија", "Никола", "Ивана", "Стефан", "Сара", "Филип",
                 "Мила", "Давид"),
    last_names=("Николовски", "Петровски", "Стојановски", "Јовановски", "Димитровски", "Илиевски", "Ангеловски",
                "Костовски", "Стефановски", "Митревски", "Наумовски", "Ристовски"),
    cities=("Скопје", "Битола", "Куманово", "Прилеп", "Тетово", "Охрид", "Велес", "Штип"),
    eu_member=False,
    price_scale=62,
    office_hours=("08:00", "16:00"), lunch=("12:00", "12:30"),
    notes=[
        "Non-EU: VAT (ДДВ) standard 18 %; 5 % for food, books, passenger transport and hotel accommodation; 10 % "
        "for restaurant and catering services (excluding alcohol).",
        "Languages: Macedonian is the business default; Albanian is co-official (eurl.languages maps it to AL only).",
        "Holidays: Закон за празниците на Република Северна Македонија, holidays for all citizens. NOT MODELLED: "
        "Рамазан Бајрам (Eid al-Fitr, first day), which follows the Islamic lunar calendar; the statutory move of a "
        "holiday falling on a Sunday to the next Monday (e.g. 2025-03-31); and holidays for members of particular "
        "communities or confessions only (e.g. Orthodox Christmas Eve, Good Friday, Kurban Bajram, Yom Kippur). "
        "The 2024 election days off are modelled as single-year rules.",
        "Company number: ЕДБ (13 digits, mod-11 check digit); VAT number = MK + ЕДБ. The 7-digit ЕМБС is not "
        "generated.",
        "Payment reference: no national structured reference for commercial payments; the invoice number is used.",
    ],
)
