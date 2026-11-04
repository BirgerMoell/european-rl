from eurl import banking
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import MoneyFormat

# The ten statutory public holidays (Royal Decree of 18 April 1974) plus Easter Sunday and Whit Sunday, which the
# law also names (they fall on Sundays). Community holidays (11 July Flemish, 27 September French, 15 November
# German-speaking Community) are not national days off.
HOLIDAYS = (
    fixed(1, 1, {"nld": "Nieuwjaar", "fra": "jour de l'An", "deu": "Neujahr"}),
    easter_rule(0, {"nld": "Pasen", "fra": "Pâques", "deu": "Ostern"}),
    easter_rule(1, {"nld": "Paasmaandag", "fra": "lundi de Pâques", "deu": "Ostermontag"}),
    fixed(5, 1, {"nld": "Dag van de Arbeid", "fra": "fête du Travail", "deu": "Tag der Arbeit"}),
    easter_rule(39, {"nld": "Onze-Lieve-Heer-Hemelvaart", "fra": "Ascension", "deu": "Christi Himmelfahrt"}),
    easter_rule(49, {"nld": "Pinksteren", "fra": "Pentecôte", "deu": "Pfingsten"}),
    easter_rule(50, {"nld": "Pinkstermaandag", "fra": "lundi de Pentecôte", "deu": "Pfingstmontag"}),
    fixed(7, 21, {"nld": "Nationale feestdag", "fra": "fête nationale", "deu": "Nationalfeiertag"}),
    fixed(8, 15, {"nld": "Onze-Lieve-Vrouw-Hemelvaart", "fra": "Assomption", "deu": "Mariä Himmelfahrt"}),
    fixed(11, 1, {"nld": "Allerheiligen", "fra": "Toussaint", "deu": "Allerheiligen"}),
    fixed(11, 11, {"nld": "Wapenstilstand", "fra": "Armistice", "deu": "Waffenstillstand"}),
    fixed(12, 25, {"nld": "Kerstmis", "fra": "Noël", "deu": "Weihnachten"}),
)


# --- Ondernemingsnummer / numéro d'entreprise: 10 digits, the last two = 97 - (first eight mod 97) ---------------

def _check(base8: str) -> str:
    return f"{97 - int(base8) % 97:02d}"


def ondernemingsnummer(rng):
    base = "0" + str(rng.randint(4, 8)) + "".join(str(rng.randint(0, 9)) for _ in range(6))
    s = base + _check(base)
    return f"{s[:4]}.{s[4:7]}.{s[7:]}"


def be_vat(_rng, company: str) -> str:
    return "BE" + company.replace(".", "")


def be_vat_valid(value: str) -> bool:
    s = value.replace(" ", "").replace(".", "").upper()
    if not s.startswith("BE"):
        return False
    s = s[2:]
    return len(s) == 10 and s.isdigit() and s[0] in "01" and int(s) > 0 and _check(s[:8]) == s[8:]


LOCALE = Locale(
    country="BE", name="Belgium", languages=("nld", "fra", "deu"),
    money=MoneyFormat("EUR", "€", ",", "."),
    timezone="Europe/Brussels",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2100, "food": 600, "accommodation": 600, "books": 600, "passenger_transport": 600,
            "restaurant": 1200},
    vat_as_of="2025",
    vat_source="Wetboek van de belasting over de toegevoegde waarde / Code de la TVA, KB nr. 20 (21 %; 6 % food, "
               "accommodation, books, passenger transport; 12 % restaurant food, drinks 21 %); FOD Financiën; "
               "EU Taxes in Europe Database",
    company_id=ondernemingsnummer,
    vat_id=be_vat,                                  # BE + the enterprise number
    vat_id_valid=be_vat_valid,
    payment_reference=banking.ogm_be,
    payment_reference_name={"nld": "gestructureerde mededeling", "fra": "communication structurée",
                            "deu": "strukturierte Mitteilung"},
    company_suffixes=("BV", "NV", "SRL", "SA"),
    company_stems=("Scheldeland", "Kempenhof", "Leiedal", "Zonnebloem", "Heidebos", "Meersbeek", "Lindehof",
                   "Polderzicht", "Maasvallei", "Duinhoek"),
    first_names=("Lucas", "Emma", "Louis", "Olivia", "Arthur", "Marie", "Noah", "Louise", "Thomas", "Sarah",
                 "Jules", "Elise"),
    last_names=("Peeters", "Janssens", "Maes", "Jacobs", "Mertens", "Willems", "Claes", "Goossens", "Dubois",
                "Lambert", "Dupont", "Wouters"),
    cities=("Antwerpen", "Gent", "Brussel", "Leuven", "Brugge", "Hasselt", "Mechelen", "Kortrijk"),
    office_hours=("08:30", "17:00"), lunch=("12:00", "13:00"),
    date_style="DD/MM/YYYY",
    notes=["Money: '1.234,56 €' (common across the language communities; CLDR nl-BE writes '€ 1.234,56', "
           "fr-BE '1 234,56 €').",
           "Holidays are the national set; community holidays (11 July, 27 September, 15 November) are not modelled. "
           "A holiday on a Sunday gives a replacement day chosen per employer (not modelled).",
           "A rise of VAT on accommodation from 6 % to 12 % was planned for 2026; this pack is the 2025 snapshot."],
)
