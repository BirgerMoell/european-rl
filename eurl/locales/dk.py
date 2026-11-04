import random

from eurl import banking
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"dan": "nytårsdag"}),
    easter_rule(-3, {"dan": "skærtorsdag"}),
    easter_rule(-2, {"dan": "langfredag"}),
    easter_rule(0, {"dan": "påskedag"}),
    easter_rule(1, {"dan": "2. påskedag"}),
    # Store bededag was abolished as a public holiday from 2024 (lov nr. 151 af 28.2.2023).
    easter_rule(26, {"dan": "store bededag"}, until=2023),
    easter_rule(39, {"dan": "Kristi himmelfartsdag"}),
    easter_rule(49, {"dan": "pinsedag"}),
    easter_rule(50, {"dan": "2. pinsedag"}),
    fixed(12, 25, {"dan": "juledag"}),
    fixed(12, 26, {"dan": "2. juledag"}),
    # Customary days off (not statutory public holidays): closed under most collective agreements and in the
    # state sector.
    fixed(12, 24, {"dan": "juleaftensdag"}, public=False),
    fixed(12, 31, {"dan": "nytårsaftensdag"}, public=False),
)

_CVR_W = (2, 7, 6, 5, 4, 3, 2, 1)


def cvr_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if s.startswith("DK"):
        s = s[2:]
    return len(s) == 8 and s.isdigit() and s[0] != "0" and sum(w * int(d) for w, d in zip(_CVR_W, s)) % 11 == 0


def cvr(rng: random.Random) -> str:
    """CVR-nummer: 8 digits, weights 2 7 6 5 4 3 2 1, weighted sum divisible by 11."""
    while True:
        base = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(6))
        check = -sum(w * int(d) for w, d in zip(_CVR_W, base)) % 11
        if check < 10:
            return base + str(check)


def vat_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    return s.startswith("DK") and cvr_valid(s)


LOCALE = Locale(
    country="DK", name="Denmark", languages=("dan",),
    money=MoneyFormat("DKK", "kr.", ",", "."),
    timezone="Europe/Copenhagen",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2500, "food": 2500, "accommodation": 2500, "books": 2500, "passenger_transport": 0,
            "restaurant": 2500},
    vat_as_of="2025",
    vat_source="Momsloven (LBK nr. 1021 af 2019 med ændringer), §§ 13 og 33; Skattestyrelsen; EU Taxes in Europe "
               "Database. One rate (25 %); passenger transport is exempt (momsloven § 13, stk. 1, nr. 15)",
    company_id=cvr,
    vat_id=lambda rng, number: "DK" + number, vat_id_valid=vat_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"dan": "betalingsreference (RF-reference)"},
    company_suffixes=("ApS", "A/S", "I/S"),
    company_stems=("Lyngbakke", "Havblik", "Søndervang", "Kildemose", "Bøgely", "Fjordlys", "Granhøj", "Strandeng",
                   "Ravnsholt", "Mosevang"),
    first_names=("Anne", "Mette", "Hanne", "Peter", "Jens", "Lars", "Mads", "Sofie", "Freja", "Mikkel", "Line",
                 "Søren"),
    last_names=("Jensen", "Nielsen", "Hansen", "Pedersen", "Andersen", "Christensen", "Larsen", "Sørensen",
                "Rasmussen", "Jørgensen", "Petersen", "Madsen"),
    cities=("København", "Aarhus", "Odense", "Aalborg", "Esbjerg", "Randers", "Kolding", "Vejle"),
    price_scale=7,
    date_style="DD.MM.YYYY",
    office_hours=("08:00", "16:00"), lunch=("12:00", "12:30"),
    notes=["Denmark has one VAT rate (25 %) for all taxable supplies; domestic passenger transport is VAT-exempt "
           "(0 % in the world).",
           "Grundlovsdag (5 June) is not a public holiday; many collective agreements give the afternoon (or the "
           "day) off. Christmas Eve and New Year's Eve are modelled as customary days off.",
           "Store bededag ceased to be a public holiday from 2024."],
)
