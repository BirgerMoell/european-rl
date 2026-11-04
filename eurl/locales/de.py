from eurl import banking, ids
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import MoneyFormat

# Nationwide public holidays only. Several Länder add more (e.g. Fronleichnam, Allerheiligen, Reformationstag);
# the world places German subsidiaries in Hamburg-like settings with nationwide holidays only, and tasks that
# depend on a regional holiday name the Land and its extra days explicitly.
HOLIDAYS = (
    fixed(1, 1, {"deu": "Neujahr"}),
    easter_rule(-2, {"deu": "Karfreitag"}),
    easter_rule(1, {"deu": "Ostermontag"}),
    fixed(5, 1, {"deu": "Tag der Arbeit"}),
    easter_rule(39, {"deu": "Christi Himmelfahrt"}),
    easter_rule(50, {"deu": "Pfingstmontag"}),
    fixed(10, 3, {"deu": "Tag der Deutschen Einheit"}),
    fixed(12, 25, {"deu": "Erster Weihnachtstag"}),
    fixed(12, 26, {"deu": "Zweiter Weihnachtstag"}),
)


def handelsregister(rng):
    return "HRB " + str(rng.randint(10000, 199999))


LOCALE = Locale(
    country="DE", name="Germany", languages=("deu",),
    money=MoneyFormat("EUR", "€", ",", "."),
    timezone="Europe/Berlin",
    holidays=HOLIDAYS,
    vat_bp={"standard": 1900, "food": 700, "accommodation": 700, "books": 700, "passenger_transport": 700,
            "restaurant": 1900},
    vat_as_of="2025",
    vat_source="Umsatzsteuergesetz §12; EU Taxes in Europe Database",
    company_id=handelsregister,
    vat_id=lambda rng, _register: ids.de_vat(rng),   # not derived from the register number
    vat_id_valid=ids.de_vat_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"deu": "Verwendungszweck (RF-Referenz)"},
    company_suffixes=("GmbH", "AG", "KG", "GmbH & Co. KG"),
    company_stems=("Rheinblick", "Lindenhof", "Nordwerk", "Alpenstein", "Elbwerft", "Tannenberg", "Weserland",
                   "Buchenhain", "Sonnenfeld", "Brückmann"),
    first_names=("Anna", "Lukas", "Sophie", "Jonas", "Lea", "Felix", "Marie", "Paul", "Hannah", "Maximilian",
                 "Laura", "Tobias"),
    last_names=("Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Hoffmann",
                "Schäfer", "Koch", "Richter"),
    cities=("Hamburg", "Bremen", "Hannover", "Kiel", "Berlin", "Leipzig", "Dortmund", "Essen"),
    date_style="DD.MM.YYYY",
    office_hours=("09:00", "17:00"), lunch=("12:30", "13:30"),
    notes=["Holidays are the nationwide set; regional holidays are named explicitly in tasks that need them."],
)
