from eurl import banking, ids
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"pol": "Nowy Rok"}),
    fixed(1, 6, {"pol": "Święto Trzech Króli"}),
    easter_rule(0, {"pol": "Wielkanoc"}),
    easter_rule(1, {"pol": "Poniedziałek Wielkanocny"}),
    fixed(5, 1, {"pol": "Święto Pracy"}),
    fixed(5, 3, {"pol": "Święto Konstytucji 3 Maja"}),
    easter_rule(49, {"pol": "Zielone Świątki"}),
    easter_rule(60, {"pol": "Boże Ciało"}),
    fixed(8, 15, {"pol": "Wniebowzięcie Najświętszej Maryi Panny"}),
    fixed(11, 1, {"pol": "Wszystkich Świętych"}),
    fixed(11, 11, {"pol": "Narodowe Święto Niepodległości"}),
    fixed(12, 24, {"pol": "Wigilia Bożego Narodzenia"}, since=2025),
    fixed(12, 25, {"pol": "Boże Narodzenie (pierwszy dzień)"}),
    fixed(12, 26, {"pol": "Boże Narodzenie (drugi dzień)"}),
)

LOCALE = Locale(
    country="PL", name="Poland", languages=("pol",),
    money=MoneyFormat("PLN", "zł", ",", NBSP),
    timezone="Europe/Warsaw",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2300, "food": 500, "accommodation": 800, "books": 500, "passenger_transport": 800,
            "restaurant": 800},
    vat_as_of="2025",
    vat_source="Ustawa o podatku od towarów i usług; EU Taxes in Europe Database",
    company_id=ids.pl_nip, vat_id=lambda rng, nip: ids.pl_vat(nip), vat_id_valid=ids.pl_nip_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"pol": "tytuł przelewu (referencja RF)"},
    company_suffixes=("sp. z o.o.", "S.A.", "sp.k."),
    company_stems=("Wiślany", "Bursztyn", "Zielony Gaj", "Mazowsze", "Tatry", "Odra", "Kresowa", "Sosnowa",
                   "Złoty Kłos", "Bałtyk"),
    first_names=("Anna", "Jakub", "Zofia", "Jan", "Maja", "Antoni", "Julia", "Szymon", "Natalia", "Piotr",
                 "Katarzyna", "Tomasz"),
    last_names=("Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski",
                "Zieliński", "Szymański", "Woźniak", "Dąbrowski", "Kozłowski"),
    cities=("Kraków", "Gdańsk", "Poznań", "Wrocław", "Łódź", "Lublin", "Katowice", "Warszawa"),
    price_scale=4,
    date_style="DD.MM.YYYY",
    office_hours=("08:00", "16:00"), lunch=("12:00", "12:30"),
)
