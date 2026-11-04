import random

from eurl import banking
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

# Bridge days moved by the annual decree of the Ministry for National Economy ("munkarend-áthelyezés"): the bridge
# day is off and a Saturday is worked instead. Known decrees only (2024-2026).
_BRIDGE_DAYS = ((2024, 8, 19), (2024, 12, 24), (2024, 12, 27),
                (2025, 5, 2), (2025, 10, 24), (2025, 12, 24),
                (2026, 1, 2), (2026, 8, 21), (2026, 12, 24))

HOLIDAYS = (
    fixed(1, 1, {"hun": "újév"}),
    fixed(3, 15, {"hun": "nemzeti ünnep (március 15.)"}),
    easter_rule(-2, {"hun": "nagypéntek"}),
    easter_rule(0, {"hun": "húsvétvasárnap"}),
    easter_rule(1, {"hun": "húsvéthétfő"}),
    fixed(5, 1, {"hun": "a munka ünnepe"}),
    easter_rule(49, {"hun": "pünkösdvasárnap"}),
    easter_rule(50, {"hun": "pünkösdhétfő"}),
    fixed(8, 20, {"hun": "az államalapítás ünnepe"}),
    fixed(10, 23, {"hun": "nemzeti ünnep (október 23.)"}),
    fixed(11, 1, {"hun": "mindenszentek"}),
    fixed(12, 25, {"hun": "karácsony"}),
    fixed(12, 26, {"hun": "karácsony másnapja"}),
) + tuple(fixed(m, d, {"hun": "áthelyezett pihenőnap"}, since=y, until=y, public=False) for y, m, d in _BRIDGE_DAYS)

_W = (9, 7, 3, 1, 9, 7, 3, 1)


def _torzsszam(rng: random.Random) -> str:
    base = str(rng.randint(1, 3)) + "".join(str(rng.randint(0, 9)) for _ in range(6))
    return base + str(-sum(w * int(d) for w, d in zip(_W, base)) % 10)


def torzsszam_valid(value: str) -> bool:
    return len(value) == 8 and value.isdigit() and sum(w * int(d) for w, d in zip(_W, value)) % 10 == 0


def adoszam(rng: random.Random) -> str:
    """Adószám of a company: törzsszám (8 digits, weights 9 7 3 1) - ÁFA code - county code."""
    return f"{_torzsszam(rng)}-2-{rng.choice(('41', '42', '43', '44', '13', '09', '02', '20'))}"


def kozossegi_adoszam_valid(value: str) -> bool:
    s = value.replace(" ", "").replace("-", "").upper()
    return s.startswith("HU") and torzsszam_valid(s[2:])


LOCALE = Locale(
    country="HU", name="Hungary", languages=("hun",),
    money=MoneyFormat("HUF", "Ft", ",", NBSP),
    timezone="Europe/Budapest",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2700, "food": 500, "accommodation": 500, "books": 500, "passenger_transport": 2700,
            "restaurant": 500},
    vat_as_of="2025",
    vat_source="2007. évi CXXVII. törvény az általános forgalmi adóról, 82. § és 3. számú melléklet; NAV; EU Taxes "
               "in Europe Database",
    company_id=adoszam,
    vat_id=lambda rng, number: "HU" + number[:8], vat_id_valid=kozossegi_adoszam_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"hun": "közlemény (RF-hivatkozás)"},
    company_suffixes=("Kft.", "Zrt.", "Bt."),
    company_stems=("Tiszavölgy", "Bakonyerdő", "Somfa", "Diófás", "Fűzliget", "Hársfa", "Kőpatak", "Napfény",
                   "Nyírfa", "Gyöngyvirág"),
    first_names=("László", "Anna", "Gábor", "Katalin", "Zoltán", "Eszter", "Péter", "Zsófia", "Balázs", "Réka",
                 "Tamás", "Judit"),
    last_names=("Nagy", "Kovács", "Tóth", "Szabó", "Horváth", "Varga", "Kiss", "Molnár", "Németh", "Farkas",
                "Balogh", "Papp"),
    cities=("Budapest", "Debrecen", "Szeged", "Miskolc", "Pécs", "Győr", "Nyíregyháza", "Kecskemét"),
    price_scale=400,
    date_style="YYYY. MM. DD.",
    office_hours=("08:00", "16:30"), lunch=("12:00", "12:30"),
    notes=["Food: 5 % for basic foods (meat, poultry, fish, eggs, fresh milk); some other foods (e.g. some bakery "
           "and dairy products) 18 %, coffee 27 %. Commercial accommodation, restaurant food and books 5 %; "
           "domestic passenger transport 27 %.",
           "Bridge days moved by the annual decree are listed per year as customary days off (public=False); only "
           "decrees up to 2026 are included.",
           "Hungarian order is family name first (Nagy László); the world writes given name first."],
)
