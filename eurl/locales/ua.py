"""Ukraine (non-EU). Under martial law (since 2022) the holidays of Labour Code art. 73 are not days off, so the
2025 snapshot has no public holidays; the statutory list is kept in STATUTORY_SUSPENDED."""
import string

from eurl.calendar import fixed, orthodox_rule
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

# Labour Code art. 73 as amended in 2023 (Christmas on 25 December only, Statehood Day 15 July, Defenders' Day
# 1 October, Remembrance and Victory Day 8 May). Suspended as days off by Law 2136-IX on martial law; NOT part of the
# pack's holidays while martial law lasts.
STATUTORY_SUSPENDED = (
    fixed(1, 1, {"ukr": "Новий рік"}),
    fixed(3, 8, {"ukr": "Міжнародний жіночий день"}),
    orthodox_rule(0, {"ukr": "Великдень (Пасха)"}),
    fixed(5, 1, {"ukr": "День праці"}),
    fixed(5, 8, {"ukr": "День пам'яті та перемоги над нацизмом у Другій світовій війні 1939–1945 років"}),
    orthodox_rule(49, {"ukr": "Трійця"}),
    fixed(6, 28, {"ukr": "День Конституції України"}),
    fixed(7, 15, {"ukr": "День Української Державності"}),
    fixed(8, 24, {"ukr": "День Незалежності України"}),
    fixed(10, 1, {"ukr": "День захисників і захисниць України"}),
    fixed(12, 25, {"ukr": "Різдво Христове"}),
)
HOLIDAYS = ()

_REGIONS = range(1, 27)


# --- ЄДРПОУ (8 digits): weights 1..7 (7,1..6 when the code starts with 3, 4 or 5) mod 11; if 10, weights + 2 ----

def _edrpou_check(body7: str) -> str:
    weights = [7, 1, 2, 3, 4, 5, 6] if body7[0] in "345" else [1, 2, 3, 4, 5, 6, 7]
    total = sum(w * int(d) for w, d in zip(weights, body7))
    if total % 11 < 10:
        return str(total % 11)
    total = sum((w + 2) * int(d) for w, d in zip(weights, body7))
    return str(total % 11 % 10)


def edrpou(rng) -> str:
    body = str(rng.choice((3, 4))) + "".join(rng.choice(string.digits) for _ in range(6))
    return body + _edrpou_check(body)


# --- ІПН of a VAT payer (12 digits): first 7 digits of the ЄДРПОУ, 2-digit region code (01–26), 2-digit sequence,
# 1 final digit. The final digit's algorithm is not published, so the generator draws it and the validator checks
# the format. python-stdnum has no validator for it. ---------------------------------------------------------------

def vat_id(rng, company: str) -> str:
    return company[:7] + f"{rng.choice(_REGIONS):02d}" + f"{rng.randint(1, 99):02d}" + rng.choice(string.digits)


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return len(s) == 12 and s.isdigit() and int(s[7:9]) in _REGIONS


def invoice_reference(rng) -> str:
    """No national structured reference: the invoice number is quoted in the payment purpose."""
    return f"СФ-{rng.randint(1, 999999):06d}"


LOCALE = Locale(
    country="UA", name="Ukraine", languages=("ukr",),
    money=MoneyFormat("UAH", "грн", ",", NBSP),
    timezone="Europe/Kyiv",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2000, "food": 2000, "accommodation": 700, "books": 2000, "passenger_transport": 2000,
            "restaurant": 2000},
    vat_as_of="2025",
    vat_source="Податковий кодекс України, ст. 193 (20 %, 14 %, 7 %); ДПС України; PwC Worldwide Tax Summaries "
               "(Ukraine, other taxes)",
    company_id=edrpou, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=invoice_reference, payment_reference_name={"ukr": "номер рахунку-фактури"},
    company_suffixes=("ТОВ", "ПрАТ"),
    company_stems=("Калина", "Соняшник", "Зелений гай", "Барвінок", "Лелека", "Світанок", "Ясен", "Золотий колос",
                   "Верба", "Джерело"),
    first_names=("Олена", "Андрій", "Оксана", "Дмитро", "Наталія", "Олександр", "Ірина", "Максим", "Тетяна",
                 "Сергій", "Юлія", "Іван"),
    last_names=("Шевченко", "Бондаренко", "Коваленко", "Ткаченко", "Кравченко", "Олійник", "Шевчук", "Поліщук",
                "Бойко", "Мельник", "Лисенко", "Савченко"),
    cities=("Київ", "Львів", "Одеса", "Харків", "Дніпро", "Вінниця", "Полтава", "Ужгород"),
    eu_member=False,
    price_scale=45,
    office_hours=("09:00", "18:00"), lunch=("13:00", "14:00"),
    notes=[
        "Non-EU: ПДВ standard 20 %; 7 % for hotel (temporary) accommodation, medicines and some cultural events; "
        "14 % for certain agricultural products (not retail groceries). Food, books (outside the temporary "
        "exemption for domestically produced books), restaurants and domestic passenger transport are standard-"
        "rated.",
        "Holidays: under martial law (Law 2136-IX, in force since 2022) the holidays and non-working days of Labour "
        "Code art. 73 are not days off, so HOLIDAYS is empty for the 2025 snapshot (the holidays package agrees: no "
        "public holidays 2023 onward). The statutory list is kept in STATUTORY_SUSPENDED (2023 calendar reform: "
        "Christmas on 25 December only; Statehood Day 15 July; Defenders' Day 1 October; Remembrance and Victory "
        "Day 8 May). Restore it as HOLIDAYS when martial law ends.",
        "Company number: ЄДРПОУ (8 digits with check digit). VAT number: the 12-digit ІПН of a VAT payer; its last "
        "digit's algorithm is not published, so only the format is generated and validated.",
        "Payment reference: no national structured reference; the invoice number is quoted in the payment purpose "
        "(призначення платежу).",
        "Legal form: Ukrainian usage puts the form first (ТОВ «Калина»); the generator appends it.",
    ],
)
