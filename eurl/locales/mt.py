from eurl import banking
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import MoneyFormat

# National Holidays and Other Public Holidays Act (Cap. 252): five national and nine public holidays. Since 2021 a
# holiday on a weekend gives an extra day of leave, not a public holiday (not modelled).
HOLIDAYS = (
    fixed(1, 1, {"mlt": "L-Ewwel tas-Sena", "eng": "New Year's Day"}),
    fixed(2, 10, {"mlt": "Il-Festa tan-Nawfraġju ta' San Pawl", "eng": "Feast of St Paul's Shipwreck"}),
    fixed(3, 19, {"mlt": "Il-Festa ta' San Ġużepp", "eng": "Feast of St Joseph"}),
    fixed(3, 31, {"mlt": "Jum il-Ħelsien", "eng": "Freedom Day"}),
    easter_rule(-2, {"mlt": "Il-Ġimgħa l-Kbira", "eng": "Good Friday"}),
    fixed(5, 1, {"mlt": "Jum il-Ħaddiem", "eng": "Worker's Day"}),
    fixed(6, 7, {"mlt": "Sette Giugno", "eng": "Sette Giugno"}),
    fixed(6, 29, {"mlt": "L-Imnarja (Il-Festa ta' San Pietru u San Pawl)", "eng": "Feast of St Peter and St Paul"}),
    fixed(8, 15, {"mlt": "Santa Marija", "eng": "Feast of the Assumption"}),
    fixed(9, 8, {"mlt": "Jum il-Vitorja", "eng": "Victory Day"}),
    fixed(9, 21, {"mlt": "Jum l-Indipendenza", "eng": "Independence Day"}),
    fixed(12, 8, {"mlt": "Il-Festa tal-Immakulata Kunċizzjoni", "eng": "Feast of the Immaculate Conception"}),
    fixed(12, 13, {"mlt": "Jum ir-Repubblika", "eng": "Republic Day"}),
    fixed(12, 25, {"mlt": "Il-Milied", "eng": "Christmas Day"}),
)


def mbr_number(rng):
    return f"C {rng.randint(10000, 109999)}"


# --- VAT number: MT + 8 digits; weights 3 4 6 7 8 9 10 1, sum ≡ 0 (mod 37) ---------------------------------------
_W = (3, 4, 6, 7, 8, 9)


def mt_vat(rng, _mbr=None):
    six = str(rng.randint(100000, 999999))
    check = (37 - sum(w * int(d) for w, d in zip(_W, six)) % 37) % 37
    return f"MT{six}{check:02d}"


def mt_vat_valid(value: str) -> bool:
    s = value.replace(" ", "").replace("-", "").upper()
    if len(s) != 10 or not s.startswith("MT") or not s[2:].isdigit() or s[2] == "0":
        return False
    return sum(w * int(d) for w, d in zip(_W + (10, 1), s[2:])) % 37 == 0


LOCALE = Locale(
    country="MT", name="Malta", languages=("mlt", "eng"),
    money=MoneyFormat("EUR", "€", ".", ",", symbol_first=True),
    timezone="Europe/Malta",
    holidays=HOLIDAYS,
    vat_bp={"standard": 1800, "food": 0, "accommodation": 700, "books": 500, "passenger_transport": 0,
            "restaurant": 1800},
    vat_as_of="2025",
    vat_source="VAT Act (Cap. 406), Fifth and Eighth Schedules (18 %; 7 % accommodation; 5 % printed books; "
               "food for human consumption and scheduled passenger transport exempt with credit, i.e. 0 %; "
               "restaurant meals 18 %); Commissioner for Revenue; EU Taxes in Europe Database",
    company_id=mbr_number,
    vat_id=mt_vat,                                  # the VAT number is not derived from the MBR registration
    vat_id_valid=mt_vat_valid,
    payment_reference=banking.rf_reference,
    payment_reference_name={"mlt": "referenza tal-ħlas (RF)", "eng": "payment reference (RF)"},
    company_suffixes=("Ltd", "Limited", "p.l.c."),
    company_stems=("Dwejra", "Xlendi", "Buskett", "Fawwara", "Kemmuna", "Ramla", "Marsalforn", "Qbajjar",
                   "Sannat", "Wied Babu"),
    first_names=("Maria", "Luke", "Martina", "Matthew", "Julia", "Jake", "Elena", "Daniel", "Nicole", "Kurt",
                 "Sarah", "Andrea"),
    last_names=("Borg", "Camilleri", "Vella", "Farrugia", "Zammit", "Galea", "Micallef", "Grech", "Attard",
                "Spiteri", "Azzopardi", "Cassar"),
    cities=("Valletta", "Birkirkara", "Mosta", "Qormi", "Sliema", "Żabbar", "San Ġwann", "Victoria"),
    office_hours=("08:00", "17:00"), lunch=("12:30", "13:30"),
    date_style="DD/MM/YYYY",
    notes=["Food and scheduled passenger transport are exempt with credit (0 %).",
           "Money is written €1,234.56 (symbol first, comma grouping, decimal point).",
           "Victoria (Ir-Rabat) is the main town of Gozo."],
)
