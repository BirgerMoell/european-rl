"""Romania."""
import string

from eurl import banking
from eurl.calendar import fixed, orthodox_rule
from eurl.locales import Locale
from eurl.money import MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"ron": "Anul Nou"}),
    fixed(1, 2, {"ron": "Anul Nou (a doua zi)"}),
    fixed(1, 6, {"ron": "Botezul Domnului – Boboteaza"}, since=2024),
    fixed(1, 7, {"ron": "Soborul Sfântului Proroc Ioan Botezătorul"}, since=2024),
    fixed(1, 24, {"ron": "Ziua Unirii Principatelor Române"}),
    orthodox_rule(-2, {"ron": "Vinerea Mare"}),
    orthodox_rule(0, {"ron": "Paștele"}),
    orthodox_rule(1, {"ron": "A doua zi de Paște"}),
    fixed(5, 1, {"ron": "Ziua Muncii"}),
    fixed(6, 1, {"ron": "Ziua Copilului"}),
    orthodox_rule(49, {"ron": "Rusaliile"}),
    orthodox_rule(50, {"ron": "A doua zi de Rusalii"}),
    fixed(8, 15, {"ron": "Adormirea Maicii Domnului"}),
    fixed(11, 30, {"ron": "Sfântul Apostol Andrei, ocrotitorul României"}),
    fixed(12, 1, {"ron": "Ziua Națională a României"}),
    fixed(12, 25, {"ron": "Crăciunul"}),
    fixed(12, 26, {"ron": "A doua zi de Crăciun"}),
)

_W = (7, 5, 3, 2, 1, 7, 5, 3, 2)


# --- CUI/CIF: 2-10 digits, weights 7 5 3 2 1 7 5 3 2 on the zero-padded body, (10 * sum) mod 11 mod 10 ----------

def _cui_check(body: str) -> str:
    body = body.zfill(9)
    return str(10 * sum(w * int(d) for w, d in zip(_W, body)) % 11 % 10)


def cui(rng) -> str:
    body = str(rng.randint(1, 4)) + "".join(rng.choice(string.digits) for _ in range(6))
    return body + _cui_check(body)


def vat_id(rng, company: str) -> str:
    return "RO" + company


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if not s.startswith("RO"):
        return False
    n = s[2:]
    return n.isdigit() and 2 <= len(n) <= 10 and n[0] != "0" and _cui_check(n[:-1]) == n[-1]


LOCALE = Locale(
    country="RO", name="Romania", languages=("ron",),
    money=MoneyFormat("RON", "lei", ",", "."),
    timezone="Europe/Bucharest",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2100, "food": 1100, "accommodation": 1100, "books": 1100, "passenger_transport": 2100,
            "restaurant": 1100},
    vat_as_of="2025",
    vat_source="Codul fiscal art. 291 as amended by Legea 141/2025 (in force 2025-08-01); PwC Worldwide Tax "
               "Summaries (Romania, other taxes); EU Taxes in Europe Database",
    company_id=cui, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"ron": "referință RF (ISO 11649)"},
    company_suffixes=("S.R.L.", "S.A."),
    company_stems=("Stejarul", "Valea Teilor", "Izvorul Alb", "Brădet", "Lunca Verde", "Spicul de Aur",
                   "Colina Însorită", "Floare de Colț", "Mărțișor", "Pădurea Mică"),
    first_names=("Andrei", "Maria", "Alexandru", "Elena", "Mihai", "Ioana", "Ștefan", "Ana", "Gabriel", "Cristina",
                 "David", "Andreea"),
    last_names=("Popescu", "Ionescu", "Popa", "Pop", "Radu", "Dumitru", "Stan", "Stoica", "Gheorghe", "Matei",
                "Constantin", "Munteanu"),
    cities=("București", "Cluj-Napoca", "Timișoara", "Iași", "Constanța", "Brașov", "Craiova", "Oradea"),
    price_scale=5,
    office_hours=("09:00", "18:00"), lunch=("13:00", "14:00"),
    notes=[
        "VAT 2025: rates in force from 2025-08-01 (Legea 141/2025): standard 21 %, a single reduced rate of 11 % "
        "for food, hotel accommodation, books and restaurant/catering. From 2025-01-01 to 2025-07-31 the rates "
        "were 19 % standard, 9 % (food, accommodation, restaurants) and 5 % (books). Domestic passenger transport "
        "is standard-rated.",
        "Holidays: Codul muncii art. 139 (Epiphany and St John the Baptist added from 2024 by Legea 52/2023). "
        "Orthodox Easter and Pentecost dates.",
        "Company number: CUI/CIF (check digit with weights 7 5 3 2 1 7 5 3 2); VAT number = RO + CUI. The ONRC "
        "registration number (J..) is not generated.",
        "Payment reference: no national structured reference; the SEPA RF creditor reference is used.",
    ],
)
