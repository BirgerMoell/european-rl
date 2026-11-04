import string

from eurl import banking
from eurl.calendar import easter_rule, fixed, weekday_from
from eurl.locales import Locale
from eurl.money import MoneyFormat

# Legge 260/1949 as amended (1977, 1985, 2000), plus San Francesco d'Assisi (4 October) restored as a national
# holiday from 2026. The Giorno dell'Unità Nazionale e delle Forze Armate is celebrated on the first Sunday of
# November (legge 54/1977). City patron days (e.g. Sant'Ambrogio in Milan, San Giovanni in Florence and Turin, Santi
# Pietro e Paolo in Rome) and Whit Monday in South Tyrol are local and not modelled.
HOLIDAYS = (
    fixed(1, 1, {"ita": "Capodanno"}),
    fixed(1, 6, {"ita": "Epifania"}),
    easter_rule(0, {"ita": "Pasqua"}),
    easter_rule(1, {"ita": "Lunedì dell'Angelo"}),
    fixed(4, 25, {"ita": "Festa della Liberazione"}),
    fixed(5, 1, {"ita": "Festa del Lavoro"}),
    fixed(6, 2, {"ita": "Festa della Repubblica"}),
    fixed(8, 15, {"ita": "Assunzione (Ferragosto)"}),
    fixed(10, 4, {"ita": "San Francesco d'Assisi, patrono d'Italia"}, since=2026),
    weekday_from(6, 11, 1, {"ita": "Giorno dell'Unità Nazionale e delle Forze Armate"}),
    fixed(11, 1, {"ita": "Ognissanti"}),
    fixed(12, 8, {"ita": "Immacolata Concezione"}),
    fixed(12, 25, {"ita": "Natale"}),
    fixed(12, 26, {"ita": "Santo Stefano"}),
)


# --- Partita IVA: 7-digit serial, 3-digit office code, Luhn check digit ------------------------------------------
# A company's codice fiscale is the same 11 digits, so the company number and the VAT number coincide.

def partita_iva(rng):
    serial = "".join(rng.choice(string.digits) for _ in range(6)) + str(rng.randint(1, 9))
    office = f"{rng.randint(1, 100):03d}"
    base = serial + office
    return base + banking.luhn_digit(base)


def it_vat(_rng, piva: str) -> str:
    return "IT" + piva


def it_vat_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if s.startswith("IT"):
        s = s[2:]
    else:
        return False
    if len(s) != 11 or not s.isdigit() or int(s[:7]) == 0:
        return False
    office = s[7:10]
    if not ("001" <= office <= "100" or office in ("120", "121", "888", "999")):
        return False
    return banking.luhn_valid(s)


LOCALE = Locale(
    country="IT", name="Italy", languages=("ita",),
    money=MoneyFormat("EUR", "€", ",", "."),
    timezone="Europe/Rome",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2200, "food": 400, "accommodation": 1000, "books": 400, "passenger_transport": 1000,
            "restaurant": 1000},
    vat_as_of="2025",
    vat_source="DPR 633/1972, Tabella A (22 %; 4 % basic food such as bread, pasta, milk, fruit and vegetables, and "
               "books; 10 % accommodation, passenger transport and restaurant services); Agenzia delle Entrate; EU "
               "Taxes in Europe Database",
    company_id=partita_iva,
    vat_id=it_vat,                                  # IT + the partita IVA
    vat_id_valid=it_vat_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"ita": "riferimento di pagamento (RF)"},
    company_suffixes=("S.r.l.", "S.p.A.", "S.a.s."),
    company_stems=("Valverde", "Monteverde", "Colle Alto", "Fontebella", "Riva Chiara", "Poggio Sereno",
                   "Campo Fiorito", "Torre Bianca", "Lago Azzurro", "Valle Serena"),
    first_names=("Giulia", "Marco", "Francesca", "Luca", "Chiara", "Alessandro", "Sara", "Matteo", "Martina",
                 "Andrea", "Elena", "Davide"),
    last_names=("Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci", "Marino",
                "Greco", "Bruno", "Gallo"),
    cities=("Milano", "Torino", "Bologna", "Firenze", "Roma", "Napoli", "Verona", "Genova"),
    office_hours=("09:00", "18:00"), lunch=("13:00", "14:00"),
    date_style="DD/MM/YYYY",
    notes=["Food uses the 4 % rate for basic staples; many other foods are 10 % and coffee is 22 %.",
           "Holidays are the national set; city patron days are not modelled.",
           "The payment reference is RF; pagoPA notice codes exist for payments to public bodies only."],
)
