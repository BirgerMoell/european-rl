"""Iceland. The module name is a Python keyword: load it with eurl.locales.load("IS")."""
import random

from eurl import banking
from eurl.calendar import easter_rule, fixed, weekday_from
from eurl.locales import Locale
from eurl.money import MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"isl": "nýársdagur"}),
    easter_rule(-3, {"isl": "skírdagur"}),
    easter_rule(-2, {"isl": "föstudagurinn langi"}),
    easter_rule(0, {"isl": "páskadagur"}),
    easter_rule(1, {"isl": "annar í páskum"}),
    weekday_from(3, 4, 19, {"isl": "sumardagurinn fyrsti"}),      # first Thursday after 18 April
    fixed(5, 1, {"isl": "verkalýðsdagurinn"}),
    easter_rule(39, {"isl": "uppstigningardagur"}),
    easter_rule(49, {"isl": "hvítasunnudagur"}),
    easter_rule(50, {"isl": "annar í hvítasunnu"}),
    fixed(6, 17, {"isl": "þjóðhátíðardagurinn"}),
    weekday_from(0, 8, 1, {"isl": "frídagur verslunarmanna"}),      # first Monday in August
    fixed(12, 25, {"isl": "jóladagur"}),
    fixed(12, 26, {"isl": "annar í jólum"}),
)

_KT_W = (3, 2, 7, 6, 5, 4, 3, 2)


def kennitala_valid(value: str) -> bool:
    """Kennitala: DDMMYY-RRCS; C is MOD 11 over the first 8 digits (weights 3 2 7 6 5 4 3 2), S the century."""
    s = value.replace("-", "").replace(" ", "")
    if len(s) != 10 or not s.isdigit() or s[9] not in "90":
        return False
    return -sum(w * int(d) for w, d in zip(_KT_W, s[:8])) % 11 == int(s[8])


def kennitala_company(rng: random.Random) -> str:
    """Kennitala of a legal entity: day of registration + 40."""
    while True:
        year = rng.randint(1975, 2022)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28) + 40
        base = f"{day:02d}{month:02d}{year % 100:02d}{rng.randint(20, 99):02d}"
        check = -sum(w * int(d) for w, d in zip(_KT_W, base)) % 11
        if check < 10:
            century = "9" if year < 2000 else "0"
            return f"{base[:6]}-{base[6:]}{check}{century}"


def vsk(rng: random.Random) -> str:
    """Virðisaukaskattsnúmer: an assigned 5- or 6-digit number without a check digit."""
    return str(rng.randint(100000, 999999))


def vsk_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if s.startswith("IS"):
        s = s[2:]
    return s.isdigit() and len(s) in (5, 6)


LOCALE = Locale(
    country="IS", name="Iceland", languages=("isl",),
    money=MoneyFormat("ISK", "kr.", ",", ".", minor_digits=0),
    timezone="Atlantic/Reykjavik",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2400, "food": 1100, "accommodation": 1100, "books": 1100, "passenger_transport": 0,
            "restaurant": 1100},
    vat_as_of="2025",
    vat_source="Lög um virðisaukaskatt nr. 50/1988, 2. gr. (passenger transport exempt) and 14. gr. (24 % / 11 %); "
               "Skatturinn",
    company_id=kennitala_company,
    vat_id=lambda rng, _kennitala: vsk(rng), vat_id_valid=vsk_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"isl": "tilvísun (RF)"},
    company_suffixes=("ehf.", "hf."),
    company_stems=("Fjallalind", "Sólvellir", "Jökulá", "Lækjarás", "Bergvík", "Vesturhlíð", "Hraunholt",
                   "Straumnes", "Birkihlíð", "Lyngás"),
    first_names=("Jón", "Guðrún", "Sigurður", "Anna", "Gunnar", "Kristín", "Ólafur", "Sigríður", "Einar", "Helga",
                 "Magnús", "Katrín"),
    last_names=("Jónsson", "Jónsdóttir", "Sigurðsson", "Sigurðardóttir", "Guðmundsson", "Guðmundsdóttir",
                "Gunnarsson", "Gunnarsdóttir", "Ólafsson", "Ólafsdóttir", "Magnússon", "Magnúsdóttir"),
    cities=("Reykjavík", "Kópavogur", "Hafnarfjörður", "Akureyri", "Reykjanesbær", "Garðabær", "Selfoss",
            "Ísafjörður"),
    eu_member=False,
    price_scale=150,
    date_style="D.M.YYYY",
    office_hours=("09:00", "17:00"), lunch=("12:00", "12:30"),
    notes=["Non-EU (EEA): virðisaukaskattur (VSK). Standard 24 %, reduced 11 % (food, accommodation, books, "
           "restaurant food); scheduled passenger transport is exempt (0 % in the world).",
           "The VSK number is assigned by Skatturinn and has no check digit; the company identifier is the "
           "kennitala.",
           "Christmas Eve and New Year's Eve are half days from 13:00; not modelled.",
           "Surnames are patronymics (-son / -dóttir); the synthetic world pairs given names and surnames at "
           "random, so the gender of a patronymic may not match the given name."],
)
