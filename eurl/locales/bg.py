"""Bulgaria. The 2025 snapshot uses the lev (BGN); Bulgaria adopts the euro on 2026-01-01."""
import string

from eurl import banking
from eurl.calendar import fixed, orthodox_rule
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"bul": "Нова година"}),
    fixed(3, 3, {"bul": "Ден на Освобождението на България от османско иго"}),
    orthodox_rule(-2, {"bul": "Велики петък"}),
    orthodox_rule(-1, {"bul": "Велика събота"}),
    orthodox_rule(0, {"bul": "Великден"}),
    orthodox_rule(1, {"bul": "Великден (втори ден)"}),
    fixed(5, 1, {"bul": "Ден на труда и на международната работническа солидарност"}),
    fixed(5, 6, {"bul": "Гергьовден, Ден на храбростта и Българската армия"}),
    fixed(5, 24, {"bul": "Ден на светите братя Кирил и Методий, на българската азбука, просвета и култура и на "
                         "славянската книжовност"}),
    fixed(9, 6, {"bul": "Ден на Съединението"}),
    fixed(9, 22, {"bul": "Ден на Независимостта на България"}),
    fixed(12, 24, {"bul": "Бъдни вечер"}),
    fixed(12, 25, {"bul": "Рождество Христово"}),
    fixed(12, 26, {"bul": "Рождество Христово (втори ден)"}),
    # One-off days off by decision of the Council of Ministers (euro changeover).
    fixed(12, 31, {"bul": "Неприсъствен ден"}, since=2025, until=2025),
    fixed(1, 2, {"bul": "Неприсъствен ден"}, since=2026, until=2026),
)


# --- ЕИК (UIC, 9 digits): weights 1..8 mod 11; if 10, weights 3..10 mod 11; 10 -> 0. VAT = BG + ЕИК -----------

def _eik_check(base8: str) -> str:
    check = sum((i + 1) * int(d) for i, d in enumerate(base8)) % 11
    if check == 10:
        check = sum((i + 3) * int(d) for i, d in enumerate(base8)) % 11
    return str(check % 10)


def eik(rng) -> str:
    base = "20" + "".join(rng.choice(string.digits) for _ in range(6))   # 20xxxxxxx: Commercial Register series
    return base + _eik_check(base)


def vat_id(rng, company: str) -> str:
    return "BG" + company


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    return len(s) == 11 and s.startswith("BG") and s[2:].isdigit() and _eik_check(s[2:10]) == s[10]


LOCALE = Locale(
    country="BG", name="Bulgaria", languages=("bul",),
    money=MoneyFormat("BGN", "лв.", ",", NBSP),
    timezone="Europe/Sofia",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2000, "food": 2000, "accommodation": 900, "books": 900, "passenger_transport": 2000,
            "restaurant": 2000},
    vat_as_of="2025",
    vat_source="Закон за данък върху добавената стойност (ЗДДС) чл. 66; PwC Worldwide Tax Summaries (Bulgaria, "
               "other taxes); EU Taxes in Europe Database",
    company_id=eik, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"bul": "RF референция (ISO 11649)"},
    company_suffixes=("ЕООД", "ООД", "АД"),
    company_stems=("Бели брег", "Златна нива", "Синя река", "Дъбрава", "Елов дол", "Росица", "Яворов лес",
                   "Камчия", "Зелен хълм", "Слънчев извор"),
    first_names=("Иван", "Мария", "Георги", "Елена", "Николай", "Виктория", "Петър", "Десислава", "Александър",
                 "Цветелина", "Йордан", "Анна"),
    last_names=("Иванов", "Георгиев", "Петров", "Николов", "Христов", "Стоянов", "Тодоров", "Илиев", "Атанасов",
                "Петков", "Ангелов", "Колев"),
    cities=("София", "Пловдив", "Варна", "Бургас", "Русе", "Стара Загора", "Плевен", "Велико Търново"),
    price_scale=2,
    office_hours=("09:00", "18:00"), lunch=("12:00", "13:00"),
    notes=[
        "Currency: the 2025 snapshot uses the lev (BGN, fixed at 1.95583 per euro). Bulgaria adopts the euro on "
        "2026-01-01; update money and price_scale for a 2026 snapshot.",
        "VAT 2025: standard 20 %; 9 % for hotel accommodation, books and periodicals (permanent). The temporary 9 % "
        "for restaurant and catering and 0 % for bread and flour ended on 2024-12-31, so both are 20 % in 2025. "
        "Domestic passenger transport is standard-rated.",
        "Holidays: Labour Code art. 154. When a holiday other than Easter falls on a Saturday or Sunday, the next "
        "working day is a day off (art. 154(2)); the rule engine cannot express this, so these substitute days "
        "are not modelled. The one-off government days off 2025-12-31 and 2026-01-02 (euro changeover) are "
        "modelled as single-year rules.",
        "Company number: ЕИК/UIC (9 digits, BULSTAT check digit); VAT number = BG + ЕИК.",
        "Payment reference: no national structured reference; the SEPA RF creditor reference is used.",
    ],
)
