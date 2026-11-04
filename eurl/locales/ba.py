"""Bosnia and Herzegovina (non-EU). State-level holidays only; the Bajram holidays are lunar and not modelled."""
import string

from eurl.calendar import easter_rule, fixed, orthodox_rule
from eurl.locales import Locale
from eurl.money import MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"bos": "Nova godina"}),
    fixed(1, 2, {"bos": "Nova godina (drugi dan)"}),
    fixed(1, 7, {"bos": "Božić (pravoslavni)"}),
    orthodox_rule(-2, {"bos": "Veliki petak (pravoslavni)"}),
    easter_rule(1, {"bos": "Uskršnji ponedjeljak (katolički)"}),
    fixed(5, 1, {"bos": "Međunarodni praznik rada"}),
    fixed(5, 2, {"bos": "Međunarodni praznik rada (drugi dan)"}),
    fixed(12, 25, {"bos": "Božić (katolički)"}),
)

# Lunar holidays the rule engine cannot express (excluded from HOLIDAYS and from the holiday comparison).
LUNAR_HOLIDAYS = ("Ramazanski bajram", "Kurban-bajram")

_W = (7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


# --- JIB (13 digits, legal entities start with 4): mod 11 with weights 7..2 repeated; a remainder giving 10 is not
# issued. PDV broj (VAT number) = the JIB without its leading 4 (12 digits). python-stdnum has no BA module. -------

def _jib_check(body12: str):
    r = 11 - sum(w * int(d) for w, d in zip(_W, body12)) % 11
    return None if r == 10 else str(r % 11)


def jib(rng) -> str:
    while True:
        body = "42" + "".join(rng.choice(string.digits) for _ in range(10))
        check = _jib_check(body)
        if check is not None:
            return body + check


def vat_id(rng, company: str) -> str:
    return company[1:]


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return len(s) == 12 and s.isdigit() and _jib_check("4" + s[:11]) == s[11]


def invoice_reference(rng) -> str:
    """No national structured reference for commercial payments: the invoice number is quoted as 'poziv na broj'."""
    return f"{rng.randint(1, 999999):06d}/25"


LOCALE = Locale(
    country="BA", name="Bosnia and Herzegovina", languages=("bos",),
    money=MoneyFormat("BAM", "KM", ",", "."),
    timezone="Europe/Sarajevo",
    holidays=HOLIDAYS,
    vat_bp={c: 1700 for c in ("standard", "food", "accommodation", "books", "passenger_transport", "restaurant")},
    vat_as_of="2025",
    vat_source="Zakon o porezu na dodanu vrijednost BiH (single rate 17 %); Uprava za indirektno oporezivanje (UIO)",
    company_id=jib, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=invoice_reference, payment_reference_name={"bos": "poziv na broj (broj fakture)"},
    company_suffixes=("d.o.o.", "d.d."),
    company_stems=("Bistrica", "Lipa", "Zelena dolina", "Bijeli potok", "Javor", "Hrast", "Zlatno polje", "Vrelo",
                   "Brezik", "Sunčani breg"),
    first_names=("Amar", "Lejla", "Adnan", "Amra", "Emir", "Ajla", "Haris", "Selma", "Tarik", "Lana", "Dino",
                 "Sara"),
    last_names=("Hodžić", "Kovačević", "Begić", "Mehić", "Šarić", "Jusić", "Hasanović", "Mujić", "Salihović",
                "Omerović", "Zukić", "Husić"),
    cities=("Sarajevo", "Banja Luka", "Tuzla", "Zenica", "Mostar", "Bihać", "Bijeljina", "Doboj"),
    eu_member=False,
    price_scale=2,
    date_style="DD.MM.YYYY.",
    office_hours=("08:00", "16:00"), lunch=("12:00", "12:30"),
    notes=[
        "Non-EU: one VAT (PDV) rate of 17 % for all goods and services (no reduced rates); every category uses it.",
        "Currency: convertible mark (BAM, 'KM'), pegged at 1.95583 per euro.",
        "Holidays: there is no state-level holidays law; the pack lists the days observed nationwide by state "
        "institutions (as in the holidays package). Entity-level holidays (Federation of BiH, Republika Srpska, "
        "Brčko District) differ and are not modelled. NOT MODELLED: Ramazanski bajram (Eid al-Fitr) and "
        "Kurban-bajram (Eid al-Adha), which follow the Islamic lunar calendar.",
        "Company number: JIB (13 digits starting with 4, mod-11 check digit, weights 7 6 5 4 3 2). VAT number: PDV "
        "broj, the 12-digit JIB without its leading 4. python-stdnum has no Bosnian validator; the check rule is "
        "the one shared with the North Macedonian ЕДБ family and should be verified by a person.",
        "Payment reference: no national structured reference for commercial payments; the invoice number "
        "'nnnnnn/25' is quoted as poziv na broj.",
    ],
)
