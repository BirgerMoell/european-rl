"""Türkiye (non-EU). Ramazan Bayramı and Kurban Bayramı are lunar and not modelled (see notes)."""
import string

from eurl.calendar import fixed
from eurl.locales import Locale
from eurl.money import MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"tur": "Yılbaşı"}),
    fixed(4, 23, {"tur": "Ulusal Egemenlik ve Çocuk Bayramı"}),
    fixed(5, 1, {"tur": "Emek ve Dayanışma Günü"}),
    fixed(5, 19, {"tur": "Atatürk'ü Anma, Gençlik ve Spor Bayramı"}),
    fixed(7, 15, {"tur": "Demokrasi ve Millî Birlik Günü"}),
    fixed(8, 30, {"tur": "Zafer Bayramı"}),
    fixed(10, 29, {"tur": "Cumhuriyet Bayramı"}),
)

# Lunar holidays the rule engine cannot express (excluded from HOLIDAYS and from the holiday comparison).
LUNAR_HOLIDAYS = ("Ramazan Bayramı", "Kurban Bayramı")


# --- VKN (10 digits): the check digit of the Gelir İdaresi algorithm (as in python-stdnum tr.vkn) -------------

def _vkn_check(body9: str) -> str:
    s = 0
    for i, n in enumerate(reversed(body9), 1):
        c1 = (int(n) + i) % 10
        if c1:
            s += (c1 * 2 ** i) % 9 or 9
    return str((10 - s % 10) % 10)


def vkn(rng) -> str:
    body = str(rng.randint(1, 9)) + "".join(rng.choice(string.digits) for _ in range(8))
    return body + _vkn_check(body)


def vat_id(rng, company: str) -> str:
    return company                                             # VAT is declared under the VKN


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return len(s) == 10 and s.isdigit() and _vkn_check(s[:9]) == s[9]


def invoice_reference(rng) -> str:
    """No national structured reference: the e-Fatura invoice number (3-letter series, year, 9-digit serial)."""
    return "EFA2025" + f"{rng.randint(1, 999999999):09d}"


LOCALE = Locale(
    country="TR", name="Türkiye", languages=("tur",),
    money=MoneyFormat("TRY", "TL", ",", "."),
    timezone="Europe/Istanbul",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2000, "food": 100, "accommodation": 1000, "books": 1000, "passenger_transport": 2000,
            "restaurant": 1000},
    vat_as_of="2025",
    vat_source="3065 sayılı Katma Değer Vergisi Kanunu, (I) ve (II) sayılı listeler; Cumhurbaşkanı Kararları 5189 "
               "(2022) ve 7346 (2023); Gelir İdaresi Başkanlığı; PwC Worldwide Tax Summaries (Turkey, other taxes)",
    company_id=vkn, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=invoice_reference, payment_reference_name={"tur": "fatura numarası"},
    company_suffixes=("A.Ş.", "Ltd. Şti."),
    company_stems=("Çınar", "Defne", "Mavi Koy", "Yeşil Vadi", "Altın Başak", "Lale", "Göl Kıyısı", "Zeytin Dalı",
                   "Kardelen", "Meltem"),
    first_names=("Ayşe", "Mehmet", "Fatma", "Mustafa", "Zeynep", "Ahmet", "Elif", "Emre", "Merve", "Burak", "Selin",
                 "Can"),
    last_names=("Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım", "Öztürk", "Aydın", "Özdemir",
                "Arslan", "Doğan"),
    cities=("İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Konya", "Gaziantep", "Eskişehir"),
    eu_member=False,
    price_scale=40,
    date_style="DD.MM.YYYY",
    office_hours=("09:00", "18:00"), lunch=("12:30", "13:30"),
    notes=[
        "Non-EU: KDV standard 20 % (since 2023-07-10); 10 % (list II) for hotel accommodation, restaurant services "
        "and books; 1 % (list I) for basic foodstuffs such as bread, flour, milk and fresh produce (since 2022). "
        "Domestic passenger transport is taken as standard-rated (20 %); this and books should be checked.",
        "Holidays: 2429 sayılı Ulusal Bayram ve Genel Tatiller Hakkında Kanun, fixed-date holidays. NOT MODELLED: "
        "Ramazan Bayramı (3 days) and Kurban Bayramı (4 days), which follow the Islamic lunar calendar, and the "
        "half days off on 28 October and on each bayram eve (arife) from 13:00.",
        "Company/VAT number: VKN (10 digits with the Gelir İdaresi check digit). The 16-digit MERSİS number is not "
        "generated.",
        "Payment reference: no national structured reference; the e-Fatura invoice number is quoted.",
        "Money: written '1.234,50 TL' (the ₺ sign before the amount is also common).",
    ],
)
