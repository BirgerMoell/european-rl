from eurl import banking
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import MoneyFormat

# Statutory public holidays (Code du travail art. L. 232-2; Europe Day added by the law of 2019).
HOLIDAYS = (
    fixed(1, 1, {"fra": "jour de l'An", "deu": "Neujahr"}),
    easter_rule(1, {"fra": "lundi de Pâques", "deu": "Ostermontag"}),
    fixed(5, 1, {"fra": "fête du Travail", "deu": "Tag der Arbeit"}),
    fixed(5, 9, {"fra": "journée de l'Europe", "deu": "Europatag"}, since=2019),
    easter_rule(39, {"fra": "Ascension", "deu": "Christi Himmelfahrt"}),
    easter_rule(50, {"fra": "lundi de Pentecôte", "deu": "Pfingstmontag"}),
    fixed(6, 23, {"fra": "fête nationale", "deu": "Nationalfeiertag"}),
    fixed(8, 15, {"fra": "Assomption", "deu": "Mariä Himmelfahrt"}),
    fixed(11, 1, {"fra": "Toussaint", "deu": "Allerheiligen"}),
    fixed(12, 25, {"fra": "Noël", "deu": "Erster Weihnachtstag"}),
    fixed(12, 26, {"fra": "Saint-Étienne", "deu": "Stephanstag"}),
)


def rcs_number(rng):
    return f"RCS Luxembourg B{rng.randint(100000, 299999)}"


# --- Numéro d'identification TVA: LU + 6 digits + (those six mod 89, two digits) --------------------------------

def lu_vat(rng, _rcs=None):
    six = str(rng.randint(100000, 999999))
    return f"LU{six}{int(six) % 89:02d}"


def lu_vat_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    return len(s) == 10 and s.startswith("LU") and s[2:].isdigit() and f"{int(s[2:8]) % 89:02d}" == s[8:]


LOCALE = Locale(
    country="LU", name="Luxembourg", languages=("fra", "deu"),
    money=MoneyFormat("EUR", "€", ",", "."),
    timezone="Europe/Luxembourg",
    holidays=HOLIDAYS,
    vat_bp={"standard": 1700, "food": 300, "accommodation": 300, "books": 300, "passenger_transport": 300,
            "restaurant": 300},
    vat_as_of="2025",
    vat_source="Loi modifiée du 12 février 1979 concernant la TVA, annexe A (17 %; 3 % super-reduced for food, "
               "accommodation, books, passenger transport and restaurant food; alcoholic drinks 17 %); AED; "
               "EU Taxes in Europe Database",
    company_id=rcs_number,
    vat_id=lu_vat,                                  # the TVA number is not derived from the RCS number
    vat_id_valid=lu_vat_valid,
    payment_reference=banking.rf_reference,
    payment_reference_name={"fra": "référence de paiement (RF)", "deu": "Zahlungsreferenz (RF-Referenz)"},
    company_suffixes=("S.à r.l.", "S.A.", "SCS"),
    company_stems=("Alzette", "Sûre-Vallée", "Haut-Plateau", "Mullerthal", "Moselle-Vignes", "Clairval",
                   "Rocheval", "Grünewald", "Eislek", "Petrusse"),
    first_names=("Luca", "Emma", "Gabriel", "Léa", "Noah", "Sophie", "Tom", "Mia", "Ben", "Laura", "Max",
                 "Julie"),
    last_names=("Schmit", "Muller", "Weber", "Wagner", "Hoffmann", "Thill", "Schmitz", "Kieffer", "Reuter",
                "Klein", "Majerus", "Becker"),
    cities=("Luxembourg", "Esch-sur-Alzette", "Differdange", "Dudelange", "Ettelbruck", "Diekirch", "Wiltz",
            "Echternach"),
    office_hours=("08:30", "17:30"), lunch=("12:00", "13:00"),
    date_style="DD/MM/YYYY",
    notes=["Luxembourgish is not among the 36 languages; tasks use French (default) or German.",
           "Domestic public transport is free of charge since 2020; the 3 % rate applies to paid passenger "
           "transport.",
           "A public holiday falling on a Sunday gives a compensatory day off within three months (not modelled)."],
)
