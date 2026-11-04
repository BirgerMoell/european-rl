from eurl import banking, ids
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import NNBSP, MoneyFormat

# Metropolitan France. Alsace-Moselle adds Good Friday and 26 December; overseas departments add their own days.
HOLIDAYS = (
    fixed(1, 1, {"fra": "jour de l'An"}),
    easter_rule(1, {"fra": "lundi de Pâques"}),
    fixed(5, 1, {"fra": "fête du Travail"}),
    fixed(5, 8, {"fra": "Victoire 1945"}),
    easter_rule(39, {"fra": "Ascension"}),
    easter_rule(50, {"fra": "lundi de Pentecôte"}),
    fixed(7, 14, {"fra": "fête nationale"}),
    fixed(8, 15, {"fra": "Assomption"}),
    fixed(11, 1, {"fra": "Toussaint"}),
    fixed(11, 11, {"fra": "Armistice 1918"}),
    fixed(12, 25, {"fra": "Noël"}),
)

LOCALE = Locale(
    country="FR", name="France", languages=("fra",),
    money=MoneyFormat("EUR", "€", ",", NNBSP),
    timezone="Europe/Paris",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2000, "food": 550, "accommodation": 1000, "books": 550, "passenger_transport": 1000,
            "restaurant": 1000},
    vat_as_of="2025",
    vat_source="Code général des impôts art. 278 ff.; EU Taxes in Europe Database",
    company_id=ids.fr_siren, vat_id=lambda rng, siren: ids.fr_vat(siren), vat_id_valid=ids.fr_vat_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"fra": "référence de paiement (RF)"},
    company_suffixes=("SARL", "SAS", "SA"),
    company_stems=("Belle-Rive", "Clairefontaine", "Montvert", "Les Tilleuls", "Bastide", "Roche-Blanche",
                   "Val de Loire", "Pierrefeu", "Marais", "Hautecour"),
    first_names=("Camille", "Louis", "Chloé", "Hugo", "Manon", "Lucas", "Léa", "Jules", "Inès", "Gabriel",
                 "Sarah", "Arthur"),
    last_names=("Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy",
                "Moreau", "Simon", "Laurent"),
    cities=("Lyon", "Nantes", "Lille", "Bordeaux", "Toulouse", "Rennes", "Strasbourg", "Paris"),
    office_hours=("09:00", "18:00"), lunch=("12:00", "14:00"),
    notes=["Holidays are the metropolitan set (without Alsace-Moselle's extra days)."],
)
