from eurl import banking, ids
from eurl.calendar import easter_rule, fixed, weekday_from
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"fin": "uudenvuodenpäivä", "swe": "nyårsdagen"}),
    fixed(1, 6, {"fin": "loppiainen", "swe": "trettondagen"}),
    easter_rule(-2, {"fin": "pitkäperjantai", "swe": "långfredagen"}),
    easter_rule(0, {"fin": "pääsiäispäivä", "swe": "påskdagen"}),
    easter_rule(1, {"fin": "2. pääsiäispäivä", "swe": "annandag påsk"}),
    fixed(5, 1, {"fin": "vappu", "swe": "första maj"}),
    easter_rule(39, {"fin": "helatorstai", "swe": "Kristi himmelfärdsdag"}),
    easter_rule(49, {"fin": "helluntaipäivä", "swe": "pingstdagen"}),
    weekday_from(5, 6, 20, {"fin": "juhannuspäivä", "swe": "midsommardagen"}),
    weekday_from(5, 10, 31, {"fin": "pyhäinpäivä", "swe": "alla helgons dag"}),
    fixed(12, 6, {"fin": "itsenäisyyspäivä", "swe": "självständighetsdagen"}),
    fixed(12, 25, {"fin": "joulupäivä", "swe": "juldagen"}),
    fixed(12, 26, {"fin": "tapaninpäivä", "swe": "annandag jul"}),
    # Customary days off, not statutory.
    weekday_from(4, 6, 19, {"fin": "juhannusaatto", "swe": "midsommarafton"}, public=False),
    fixed(12, 24, {"fin": "jouluaatto", "swe": "julafton"}, public=False),
)

LOCALE = Locale(
    country="FI", name="Finland", languages=("fin", "swe"),
    money=MoneyFormat("EUR", "€", ",", NBSP),
    timezone="Europe/Helsinki",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2550, "food": 1400, "accommodation": 1400, "books": 1400, "passenger_transport": 1400,
            "restaurant": 1400},
    vat_as_of="2025",
    vat_source="Arvonlisäverolaki; Vero.fi (standard rate 25.5 % from 2024-09-01; several 10 % items moved to "
               "14 % on 2025-01-01); EU Taxes in Europe Database",
    company_id=ids.fi_ytunnus,
    vat_id=lambda rng, ytunnus: ids.fi_vat(ytunnus), vat_id_valid=ids.fi_ytunnus_valid,
    payment_reference=banking.viitenumero_fi, payment_reference_name={"fin": "viitenumero", "swe": "referensnummer"},
    company_suffixes=("Oy", "Oyj", "Ky"),
    company_stems=("Järvenpää", "Koivula", "Revontuli", "Saimaa", "Kallio", "Metsälä", "Pohjola", "Rantala",
                   "Kuusikko", "Aalto"),
    first_names=("Aino", "Eetu", "Helmi", "Onni", "Sofia", "Leo", "Emilia", "Väinö", "Ella", "Juho", "Venla",
                 "Mikko"),
    last_names=("Korhonen", "Virtanen", "Mäkinen", "Nieminen", "Mäkelä", "Hämäläinen", "Laine", "Heikkinen",
                "Koskinen", "Järvinen", "Lehtonen", "Saarinen"),
    cities=("Tampere", "Turku", "Oulu", "Jyväskylä", "Kuopio", "Lahti", "Vaasa", "Helsinki"),
    date_style="D.M.YYYY",
    office_hours=("08:00", "16:00"), lunch=("11:00", "12:00"),
)
