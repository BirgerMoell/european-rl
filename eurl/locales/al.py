"""Albania (non-EU). The two Bajram holidays follow the Islamic lunar calendar and are not modelled (see notes)."""
import re
import string

from eurl.calendar import easter_rule, fixed, orthodox_rule
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"sqi": "Festat e Vitit të Ri"}),
    fixed(1, 2, {"sqi": "Festat e Vitit të Ri (dita e dytë)"}),
    fixed(3, 14, {"sqi": "Dita e Verës"}),
    fixed(3, 22, {"sqi": "Dita e Nevruzit"}),
    easter_rule(0, {"sqi": "E diela e Pashkëve Katolike"}),
    # Easter Sunday always falls on a Sunday, so the day off moves to Monday by law.
    easter_rule(1, {"sqi": "E hëna pas Pashkëve Katolike (ditë pushimi)"}),
    orthodox_rule(0, {"sqi": "E diela e Pashkëve Ortodokse"}),
    orthodox_rule(1, {"sqi": "E hëna pas Pashkëve Ortodokse (ditë pushimi)"}),
    fixed(5, 1, {"sqi": "Dita Ndërkombëtare e Punëtorëve"}),
    fixed(9, 5, {"sqi": "Dita e Shenjtërimit të Shenjt Terezës"}),
    fixed(11, 22, {"sqi": "Dita e Alfabetit"}, since=2024),
    fixed(11, 28, {"sqi": "Dita e Flamurit dhe e Pavarësisë"}),
    fixed(11, 29, {"sqi": "Dita e Çlirimit"}),
    fixed(12, 8, {"sqi": "Dita Kombëtare e Rinisë"}),
    fixed(12, 25, {"sqi": "Krishtlindjet"}),
    # One-off day off declared by the Council of Ministers.
    fixed(3, 15, {"sqi": "Ditë pushimi"}, since=2024, until=2024),
)

# Lunar holidays the rule engine cannot express (excluded from HOLIDAYS and from the holiday comparison).
LUNAR_HOLIDAYS = ("Dita e Bajramit të Madh", "Dita e Kurban Bajramit")

_NIPT = re.compile(r"^[A-M][0-9]{8}[A-Z]$")


# --- NIPT/NUIS: letter (decade) + 8 digits (year, month/region, day, serial) + check letter ----------------------
# The check-letter algorithm is not published (python-stdnum validates the format only), so the generator draws the
# final letter at random and the validator checks the format.

def nipt(rng) -> str:
    decade = rng.choice("LM")                                  # L = 2010s, M = 2020s registrations
    digits = (str(rng.randint(0, 9)) + f"{rng.randint(10, 49):02d}" + f"{rng.randint(1, 28):02d}"
              + "".join(rng.choice(string.digits) for _ in range(3)))
    return decade + digits + rng.choice(string.ascii_uppercase)


def vat_id(rng, company: str) -> str:
    return company                                             # the NIPT is also the VAT number


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if s.startswith("AL"):
        s = s[2:]
    return bool(_NIPT.match(s))


def invoice_reference(rng) -> str:
    """No national structured reference: the invoice number (year/serial) is quoted as the payment purpose."""
    return f"FT-2025-{rng.randint(1, 999999):06d}"


LOCALE = Locale(
    country="AL", name="Albania", languages=("sqi",),
    money=MoneyFormat("ALL", "Lekë", ",", NBSP),
    timezone="Europe/Tirane",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2000, "food": 2000, "accommodation": 600, "books": 600, "passenger_transport": 2000,
            "restaurant": 2000},
    vat_as_of="2025",
    vat_source="Ligji nr. 92/2014 për TVSH-në (as amended); Drejtoria e Përgjithshme e Tatimeve; PwC Worldwide Tax "
               "Summaries (Albania, other taxes)",
    company_id=nipt, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=invoice_reference, payment_reference_name={"sqi": "numri i faturës"},
    company_suffixes=("sh.p.k.", "sh.a."),
    company_stems=("Ulliri", "Bregu i Detit", "Liqeni", "Kodra e Gjelbër", "Pylli", "Agimi", "Guri i Bardhë",
                   "Lumi i Kaltër", "Fusha e Artë", "Burimi"),
    first_names=("Arben", "Elira", "Besnik", "Ermira", "Dritan", "Anisa", "Gentian", "Blerta", "Erion", "Jonida",
                 "Ilir", "Klea"),
    last_names=("Gjoka", "Dervishi", "Krasniqi", "Kola", "Prifti", "Mema", "Hysa", "Marku", "Çela", "Lika", "Tafa",
                "Bregu"),
    cities=("Tiranë", "Durrës", "Vlorë", "Shkodër", "Elbasan", "Korçë", "Fier", "Berat"),
    eu_member=False,
    price_scale=100,
    office_hours=("08:00", "16:30"), lunch=("12:00", "12:30"),
    notes=[
        "Non-EU: VAT (TVSH) standard 20 %; 6 % for hotel accommodation (and certified agritourism) and books; 10 % "
        "for agricultural inputs. Food, restaurants and domestic passenger transport are standard-rated.",
        "Holidays: Ligji nr. 132/2015 për festat zyrtare (Alphabet Day 22 November added from 2024). NOT MODELLED: "
        "the lunar Islamic holidays Dita e Bajramit të Madh (Eid al-Fitr) and Dita e Kurban Bajramit (Eid al-Adha), "
        "whose dates are set yearly; and the statutory move of a holiday falling on a weekend to the next working "
        "day, except for the two Easter Sundays, whose Monday day off is modelled explicitly (when that Monday is already a "
        "substitute day, e.g. 2027-05-03 for 1 May, the Easter day off moves to Tuesday; not modelled). The one-off "
        "day off 2024-03-15 is a single-year rule.",
        "Company/VAT number: NIPT (letter + 8 digits + letter); the check letter algorithm is not public, so only "
        "the format is generated and validated.",
        "Payment reference: no national structured reference; a plain invoice number 'FT-2025-nnnnnn' is used.",
        "Currency: the lek's minor unit (qindarka) is not used in cash; invoices show two decimals.",
    ],
)
