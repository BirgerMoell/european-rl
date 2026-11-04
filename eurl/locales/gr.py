"""Greece. The VAT prefix is EL (not GR)."""
import string

from eurl import banking
from eurl.calendar import fixed, orthodox_rule
from eurl.locales import Locale
from eurl.money import MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"ell": "Πρωτοχρονιά"}),
    fixed(1, 6, {"ell": "Θεοφάνεια"}),
    orthodox_rule(-48, {"ell": "Καθαρά Δευτέρα"}),
    fixed(3, 25, {"ell": "Εικοστή Πέμπτη Μαρτίου"}),
    orthodox_rule(-2, {"ell": "Μεγάλη Παρασκευή"}),
    orthodox_rule(1, {"ell": "Δευτέρα του Πάσχα"}),
    fixed(5, 1, {"ell": "Εργατική Πρωτομαγιά"}, until=2023),
    fixed(5, 7, {"ell": "Εργατική Πρωτομαγιά"}, since=2024, until=2024),   # moved by ministerial decision (Holy Week)
    fixed(5, 1, {"ell": "Εργατική Πρωτομαγιά"}, since=2025),
    orthodox_rule(50, {"ell": "Δευτέρα του Αγίου Πνεύματος"}),
    fixed(8, 15, {"ell": "Κοίμηση της Θεοτόκου"}),
    fixed(10, 28, {"ell": "Ημέρα του Όχι"}),
    fixed(12, 25, {"ell": "Χριστούγεννα"}),
    fixed(12, 26, {"ell": "Σύναξη της Υπεραγίας Θεοτόκου"}),
)


# --- ΑΦΜ (9 digits): sum of d_i * 2^(8-i), times 2, mod 11 mod 10. VAT = EL + ΑΦΜ --------------------------------

def _afm_check(body8: str) -> str:
    total = 0
    for d in body8:
        total = total * 2 + int(d)
    return str(total * 2 % 11 % 10)


def afm(rng) -> str:
    body = "80" + "".join(rng.choice(string.digits) for _ in range(6))   # 8xxxxxxxx: legal-entity series
    return body + _afm_check(body)


def vat_id(rng, company: str) -> str:
    return "EL" + company


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    return len(s) == 11 and s.startswith("EL") and s[2:].isdigit() and _afm_check(s[2:10]) == s[10]


LOCALE = Locale(
    country="GR", name="Greece", languages=("ell",),
    money=MoneyFormat("EUR", "€", ",", "."),
    timezone="Europe/Athens",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2400, "food": 1300, "accommodation": 1300, "books": 600, "passenger_transport": 1300,
            "restaurant": 1300},
    vat_as_of="2025",
    vat_source="Κώδικας ΦΠΑ (ν. 2859/2000) Παράρτημα III; ΑΑΔΕ; PwC Worldwide Tax Summaries (Greece, other taxes); "
               "EU Taxes in Europe Database",
    company_id=afm, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"ell": "κωδικός πληρωμής RF (ISO 11649)"},
    company_suffixes=("Α.Ε.", "Ε.Π.Ε.", "Ι.Κ.Ε.", "Ο.Ε."),
    company_stems=("Ελαιώνας", "Πλάτανος", "Γαλήνη", "Κυπαρίσσι", "Αμπελώνας", "Λευκή Πέτρα", "Ακρογιαλιά",
                   "Ανατολή", "Δάφνη", "Αστέρι"),
    first_names=("Γιώργος", "Μαρία", "Δημήτρης", "Ελένη", "Νίκος", "Κατερίνα", "Γιάννης", "Σοφία", "Κώστας",
                 "Αγγελική", "Παναγιώτης", "Χριστίνα"),
    last_names=("Παπαδόπουλος", "Παπαδάκης", "Γεωργίου", "Νικολάου", "Ιωάννου", "Βασιλείου", "Αντωνίου",
                "Μαυρίδης", "Οικονόμου", "Δημητρίου", "Καραγιάννης", "Αλεξίου"),
    cities=("Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Ηράκλειο", "Λάρισα", "Βόλος", "Ιωάννινα", "Καβάλα"),
    office_hours=("09:00", "17:00"), lunch=("13:00", "13:30"),
    notes=[
        "VAT 2025: standard 24 %; 13 % for basic foodstuffs, hotel accommodation, passenger transport and restaurant "
        "food (non-alcoholic); 6 % for books. Some small Aegean islands have rates reduced by 30 % (not modelled).",
        "Holidays: statutory and customary national days off with Orthodox Easter dates. Labour Day is moved by "
        "ministerial decision when it falls in Holy Week or on Easter Monday; the 2024 move to 7 May is modelled as "
        "a single-year rule, later moves (e.g. the holidays package predicts 2027-05-04) are not.",
        "Company number: ΑΦΜ (9 digits, powers-of-two check digit); VAT number = EL + ΑΦΜ. The ΓΕΜΗ number is not "
        "generated.",
        "Payment reference: the SEPA RF creditor reference (widely used in Greece as 'κωδικός RF').",
    ],
)
