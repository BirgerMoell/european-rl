import datetime as dt
import random

from eurl import banking
from eurl.calendar import easter_rule, fixed, weekday_from
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat


def _moved_to_monday(month: int, day: int, name: str, years=range(2007, 2041)):
    """Law 'Par svētku, atceres un atzīmējamām dienām' (since 2007): when 4 May or 18 November falls on a Saturday
    or Sunday, the next Monday is a day off. Expanded into one dated rule per year."""
    rules = []
    for year in years:
        d = dt.date(year, month, day)
        if d.weekday() >= 5:
            monday = d + dt.timedelta(days=7 - d.weekday())
            rules.append(fixed(monday.month, monday.day, {"lav": name}, since=year, until=year))
    return tuple(rules)


# Working days moved by Cabinet orders ("Par darba dienu pārcelšanu <gads>. gadā"): the bridge day is off, a Saturday
# is worked instead. Known orders only (2024-2026); later years are added when the orders are published.
_TRANSFERRED = ((2024, 12, 23), (2024, 12, 30), (2025, 5, 2), (2025, 11, 17), (2026, 1, 2), (2026, 6, 22))

HOLIDAYS = (
    fixed(1, 1, {"lav": "Jaungada diena"}),
    easter_rule(-2, {"lav": "Lielā piektdiena"}),
    easter_rule(0, {"lav": "Pirmās Lieldienas"}),
    easter_rule(1, {"lav": "Otrās Lieldienas"}),
    fixed(5, 1, {"lav": "Darba svētki; Latvijas Republikas Satversmes sapulces sasaukšanas diena"}),
    fixed(5, 4, {"lav": "Latvijas Republikas Neatkarības atjaunošanas diena"}),
    weekday_from(6, 5, 8, {"lav": "Mātes diena"}),                   # second Sunday in May
    easter_rule(49, {"lav": "Vasarsvētki"}),
    fixed(6, 23, {"lav": "Līgo diena"}),
    fixed(6, 24, {"lav": "Jāņu diena"}),
    fixed(11, 18, {"lav": "Latvijas Republikas Proklamēšanas diena"}),
    fixed(12, 24, {"lav": "Ziemassvētku vakars"}),
    fixed(12, 25, {"lav": "Pirmie Ziemassvētki"}),
    fixed(12, 26, {"lav": "Otrie Ziemassvētki"}),
    fixed(12, 31, {"lav": "Vecgada diena"}),
) + _moved_to_monday(5, 4, "brīvdiena (Neatkarības atjaunošanas diena)") \
  + _moved_to_monday(11, 18, "brīvdiena (Proklamēšanas diena)") \
  + tuple(fixed(m, d, {"lav": "pārcelta darba diena (brīvdiena)"}, since=y, until=y, public=False)
          for y, m, d in _TRANSFERRED)

_PVN_W = (9, 1, 4, 8, 3, 10, 2, 5, 7, 6)


def registracijas_numurs(rng: random.Random) -> str:
    """Uzņēmumu reģistra numurs of a company: 11 digits, 4000xxxxxxx; weights 9 1 4 8 3 10 2 5 7 6 1 give 3 mod 11."""
    while True:
        base = "4000" + "".join(str(rng.randint(0, 9)) for _ in range(6))
        check = (3 - sum(w * int(d) for w, d in zip(_PVN_W, base))) % 11
        if check < 10:
            return base + str(check)


def registracijas_numurs_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return len(s) == 11 and s.isdigit() and s[0] > "3" and \
        (sum(w * int(d) for w, d in zip(_PVN_W, s[:10])) + int(s[10])) % 11 == 3


def pvn_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    return s.startswith("LV") and registracijas_numurs_valid(s[2:])


LOCALE = Locale(
    country="LV", name="Latvia", languages=("lav",),
    money=MoneyFormat("EUR", "€", ",", NBSP),
    timezone="Europe/Riga",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2100, "food": 2100, "accommodation": 1200, "books": 500, "passenger_transport": 1200,
            "restaurant": 2100},
    vat_as_of="2025",
    vat_source="Pievienotās vērtības nodokļa likums, 41. and 42. pants; Valsts ieņēmumu dienests; EU Taxes in "
               "Europe Database",
    company_id=registracijas_numurs,
    vat_id=lambda rng, number: "LV" + number, vat_id_valid=pvn_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"lav": "maksājuma mērķis (RF atsauce)"},
    company_suffixes=("SIA", "AS"),
    company_stems=("Ozolkalns", "Bērzaine", "Liepkalni", "Dzintarlejas", "Mežvidi", "Upmalas", "Vējmala",
                   "Rudzlauki", "Akmeņdārzs", "Priedkalni"),
    first_names=("Anna", "Jānis", "Līga", "Andris", "Ilze", "Mārtiņš", "Kristīne", "Edgars", "Laura", "Artūrs",
                 "Inese", "Roberts"),
    last_names=("Bērziņš", "Kalniņš", "Ozoliņš", "Jansons", "Liepiņš", "Krūmiņš", "Balodis", "Zariņš", "Pētersons",
                "Vītols", "Kļaviņš", "Eglītis"),
    cities=("Rīga", "Daugavpils", "Liepāja", "Jelgava", "Jūrmala", "Ventspils", "Rēzekne", "Valmiera"),
    date_style="DD.MM.YYYY.",
    office_hours=("08:30", "17:00"), lunch=("12:00", "12:30"),
    notes=["Food: 21 %, except Latvian-type fresh fruit, berries and vegetables (12 %); a 12 % pilot for bread, "
           "milk, poultry and eggs runs from 1 July 2026.",
           "Day off on the Monday after 4 May or 18 November when that date falls on a weekend (statutory, "
           "expanded per year 2007-2040). Bridge days moved by Cabinet orders are listed per year as customary "
           "days off (public=False); only orders up to 2026 are included.",
           "Surnames are given in the masculine form; feminine forms differ (Bērziņš / Bērziņa)."],
)
