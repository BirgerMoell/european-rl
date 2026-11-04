from eurl import banking, ids
from eurl.calendar import easter_rule, fixed, weekday_from
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"swe": "nyårsdagen"}),
    fixed(1, 6, {"swe": "trettondedag jul"}),
    easter_rule(-2, {"swe": "långfredagen"}),
    easter_rule(0, {"swe": "påskdagen"}),
    easter_rule(1, {"swe": "annandag påsk"}),
    fixed(5, 1, {"swe": "första maj"}),
    easter_rule(39, {"swe": "Kristi himmelsfärdsdag"}),
    easter_rule(49, {"swe": "pingstdagen"}),
    fixed(6, 6, {"swe": "Sveriges nationaldag"}),
    weekday_from(5, 6, 20, {"swe": "midsommardagen"}),
    weekday_from(5, 10, 31, {"swe": "alla helgons dag"}),
    fixed(12, 25, {"swe": "juldagen"}),
    fixed(12, 26, {"swe": "annandag jul"}),
    # Customary days off (not statutory): most employers close.
    weekday_from(4, 6, 19, {"swe": "midsommarafton"}, public=False),
    fixed(12, 24, {"swe": "julafton"}, public=False),
    fixed(12, 31, {"swe": "nyårsafton"}, public=False),
)

LOCALE = Locale(
    country="SE", name="Sweden", languages=("swe",),
    money=MoneyFormat("SEK", "kr", ",", NBSP),
    timezone="Europe/Stockholm",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2500, "food": 1200, "accommodation": 1200, "books": 600, "passenger_transport": 600,
            "restaurant": 1200},
    vat_as_of="2025",
    vat_source="Skatteverket; EU Taxes in Europe Database",
    company_id=ids.se_org, vat_id=lambda rng, org: ids.se_vat(org), vat_id_valid=ids.se_vat_valid,
    payment_reference=banking.ocr_se, payment_reference_name={"swe": "OCR-nummer"},
    company_suffixes=("AB",),
    company_stems=("Älvdal", "Björkhagen", "Norrsken", "Granbacken", "Sjövik", "Fjällbo", "Stenhamra",
                   "Lövnäs", "Ekbacken", "Rönnskär"),
    first_names=("Anna", "Erik", "Maria", "Karl", "Elin", "Johan", "Sara", "Lars", "Emma", "Oskar", "Ida",
                 "Fredrik"),
    last_names=("Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson",
                "Svensson", "Lindberg", "Holm", "Berg"),
    cities=("Stockholm", "Göteborg", "Malmö", "Uppsala", "Umeå", "Linköping", "Örebro", "Luleå"),
    office_hours=("08:00", "17:00"), lunch=("12:00", "13:00"),
)
