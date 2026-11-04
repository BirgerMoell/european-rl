"""Cyprus (areas under the effective control of the Republic). Greek is the business language; Turkish is the
second official language."""
import string

from eurl import banking
from eurl.calendar import fixed, orthodox_rule
from eurl.locales import Locale
from eurl.money import MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"ell": "Πρωτοχρονιά", "tur": "Yılbaşı"}),
    fixed(1, 6, {"ell": "Θεοφάνεια", "tur": "Epifani Yortusu"}),
    orthodox_rule(-48, {"ell": "Καθαρά Δευτέρα", "tur": "Temiz Pazartesi"}),
    fixed(3, 25, {"ell": "Ημέρα της Ελληνικής Ανεξαρτησίας", "tur": "Yunanistan Bağımsızlık Günü"}),
    fixed(4, 1, {"ell": "Εθνική Ημέρα Κύπρου", "tur": "Kıbrıs Ulusal Günü"}),
    orthodox_rule(-2, {"ell": "Μεγάλη Παρασκευή", "tur": "Kutsal Cuma"}),
    orthodox_rule(0, {"ell": "Κυριακή του Πάσχα", "tur": "Paskalya Pazarı"}),
    orthodox_rule(1, {"ell": "Δευτέρα του Πάσχα", "tur": "Paskalya Pazartesi"}),
    fixed(5, 1, {"ell": "Πρωτομαγιά", "tur": "Emek ve Dayanışma Günü"}),
    orthodox_rule(50, {"ell": "Κατακλυσμός (Δευτέρα του Αγίου Πνεύματος)", "tur": "Kataklismos (Pentekost Pazartesi)"}),
    fixed(8, 15, {"ell": "Κοίμηση της Θεοτόκου", "tur": "Meryem Ana'nın Göğe Alınışı"}),
    fixed(10, 1, {"ell": "Ημέρα της Κυπριακής Ανεξαρτησίας", "tur": "Kıbrıs Bağımsızlık Günü"}),
    fixed(10, 28, {"ell": "Ημέρα του Όχι", "tur": "Ohi Günü"}),
    fixed(12, 25, {"ell": "Χριστούγεννα", "tur": "Noel"}),
    fixed(12, 26, {"ell": "Δεύτερη μέρα των Χριστουγέννων", "tur": "Noel'in ikinci günü"}),
    # Customary: banks and the public service close; many private employers follow.
    orthodox_rule(2, {"ell": "Τρίτη της Διακαινησίμου", "tur": "Paskalya Salısı"}, public=False),
)

_LETTER = {"0": 1, "1": 0, "2": 5, "3": 7, "4": 9, "5": 13, "6": 15, "7": 17, "8": 19, "9": 21}


# --- VAT/TIC: 8 digits + check letter (odd positions mapped, even positions summed, mod 26). ---------------------

def _check_letter(body8: str) -> str:
    total = sum(_LETTER[d] for d in body8[::2]) + sum(int(d) for d in body8[1::2])
    return string.ascii_uppercase[total % 26]


def company_number(rng) -> str:
    """Registrar of Companies number for a private limited company: ΗΕ + 6 digits (shown in Latin, HE)."""
    return "HE " + str(rng.randint(300000, 459999))


def vat_id(rng, company: str) -> str:
    body = "10" + "".join(rng.choice(string.digits) for _ in range(6))   # 10xxxxxx: legal-entity TIC series
    return "CY" + body + _check_letter(body)


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "").replace("-", "").upper()
    if len(s) != 11 or not s.startswith("CY"):
        return False
    body, letter = s[2:10], s[10]
    return body.isdigit() and not body.startswith("12") and _check_letter(body) == letter


LOCALE = Locale(
    country="CY", name="Cyprus", languages=("ell", "tur"),
    money=MoneyFormat("EUR", "€", ",", "."),
    timezone="Asia/Nicosia",
    holidays=HOLIDAYS,
    vat_bp={"standard": 1900, "food": 500, "accommodation": 900, "books": 300, "passenger_transport": 900,
            "restaurant": 900},
    vat_as_of="2025",
    vat_source="Ο περί Φόρου Προστιθέμενης Αξίας Νόμος 95(I)/2000, Παραρτήματα V, XIV; Tax Department of Cyprus; "
               "PwC Worldwide Tax Summaries (Cyprus, other taxes); EU Taxes in Europe Database",
    company_id=company_number, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=banking.rf_reference,
    payment_reference_name={"ell": "κωδικός πληρωμής RF (ISO 11649)", "tur": "RF ödeme referansı (ISO 11649)"},
    company_suffixes=("Λτδ", "Ltd"),
    company_stems=("Λεμονιά", "Κυπαρισσιά", "Γαλάζια Ακτή", "Χαρουπιά", "Αμπέλι", "Ελιά", "Πεύκος", "Αμμουδιά",
                   "Θαλασσινό Αεράκι", "Κίτρινη Πέτρα"),
    first_names=("Ανδρέας", "Μαρία", "Χρίστος", "Ελένη", "Γιώργος", "Άννα", "Κυριάκος", "Σοφία", "Μιχάλης",
                 "Παναγιώτα", "Νίκος", "Χριστίνα"),
    last_names=("Γεωργίου", "Χαραλάμπους", "Κωνσταντίνου", "Ιωάννου", "Νικολάου", "Αντωνίου", "Χριστοδούλου",
                "Παναγιώτου", "Δημητρίου", "Μιχαήλ", "Ευαγγέλου", "Λοΐζου"),
    cities=("Λευκωσία", "Λεμεσός", "Λάρνακα", "Πάφος", "Παραλίμνι", "Αγία Νάπα", "Στρόβολος", "Λακατάμια"),
    office_hours=("08:00", "17:00"), lunch=("13:00", "14:00"),
    notes=[
        "Languages: Greek (business default) and Turkish are both official; eurl.languages maps Turkish text to "
        "TR only, so Turkish appears here in holiday and reference names only.",
        "VAT 2025: standard 19 %; 9 % hotel accommodation, restaurant/catering and local bus passenger transport; "
        "5 % foodstuffs; 3 % books, newspapers and periodicals (from 2023-07-21). Certain basic goods (bread, milk, "
        "eggs, baby food) are temporarily zero-rated; the food category uses the general 5 % foodstuffs rate.",
        "Holidays: national public holidays with Orthodox Easter dates. Easter Tuesday is a bank and public-service "
        "holiday, modelled as a customary day off (public=False). Christmas Eve and Holy Saturday are optional.",
        "Company number: Registrar of Companies number HE + digits (no check digit). VAT number: CY + 8 digits + "
        "check letter (the TIC series for companies starts with 10 or 30; 12 is not allowed).",
        "Payment reference: the SEPA RF creditor reference.",
    ],
)
