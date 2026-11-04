import string

from eurl import banking
from eurl.calendar import Rule, easter_rule
from eurl.locales import Locale
from eurl.money import MoneyFormat


class _NationalDay(Rule):
    """A fixed national holiday that only counts as such when it does not fall on a Sunday: the yearly BOE list
    then leaves the replacement Monday to the autonomous communities (Estatuto de los Trabajadores art. 37.2)."""

    def date(self, year):
        d = super().date(year)
        return None if d is not None and d.weekday() == 6 else d


def _fixed(month, day, names, **kw):
    return _NationalDay("fixed", names, month=month, day=day, **kw)


# National holidays common to all of Spain (Real Decreto 2001/1983 art. 45 and the yearly BOE resolution). Jueves
# Santo, 19 March, 25 July, Easter Monday and the autonomous communities' own days are regional and not modelled;
# the communities may also move a national holiday that falls on a Sunday to the Monday.
HOLIDAYS = (
    _fixed(1, 1, {"spa": "Año Nuevo", "cat": "Cap d'Any", "eus": "Urteberri eguna", "glg": "Aninovo"}),
    _fixed(1, 6, {"spa": "Epifanía del Señor", "cat": "Reis", "eus": "Errege eguna", "glg": "Día de Reis"}),
    easter_rule(-2, {"spa": "Viernes Santo", "cat": "Divendres Sant", "eus": "Ostiral Santua",
                     "glg": "Venres Santo"}),
    _fixed(5, 1, {"spa": "Fiesta del Trabajo", "cat": "Festa del Treball", "eus": "Langileen eguna",
                  "glg": "Día do Traballo"}),
    _fixed(8, 15, {"spa": "Asunción de la Virgen", "cat": "L'Assumpció", "eus": "Andre Mariaren Jasokundea",
                   "glg": "Asunción da Virxe"}),
    _fixed(10, 12, {"spa": "Fiesta Nacional de España", "cat": "Festa Nacional d'Espanya",
                    "eus": "Espainiako Jai Nazionala", "glg": "Festa Nacional de España"}),
    _fixed(11, 1, {"spa": "Todos los Santos", "cat": "Tots Sants", "eus": "Santu Guztien eguna",
                   "glg": "Día de Todos os Santos"}),
    _fixed(12, 6, {"spa": "Día de la Constitución", "cat": "Dia de la Constitució", "eus": "Konstituzio eguna",
                   "glg": "Día da Constitución"}),
    _fixed(12, 8, {"spa": "Inmaculada Concepción", "cat": "La Immaculada", "eus": "Sortzez Garbiaren eguna",
                   "glg": "Inmaculada Concepción"}),
    _fixed(12, 25, {"spa": "Navidad", "cat": "Nadal", "eus": "Eguberri eguna", "glg": "Nadal"}),
)

# --- CIF / NIF of a company: organisation letter, 2-digit province, 5 digits, control character ----------------
# Control: Luhn check digit c over the 7 digits; A, B, E, H use the digit, N, P, Q, R, S, W the letter
# "JABCDEFGHI"[c]; other letters may use either.
_LETTERS = "JABCDEFGHI"
_PROVINCES = ("08", "28", "46", "41", "50", "48", "29", "36", "15", "33")


def cif(rng):
    letter = rng.choice("BBBA")                     # B = sociedad limitada, A = sociedad anónima
    digits = rng.choice(_PROVINCES) + "".join(rng.choice(string.digits) for _ in range(5))
    return letter + digits + banking.luhn_digit(digits)


def cif_valid(value: str) -> bool:
    s = value.replace(" ", "").replace("-", "").upper()
    if len(s) != 9 or s[0] not in "ABCDEFGHJNPQRSUVW" or not s[1:8].isdigit():
        return False
    digit = banking.luhn_digit(s[1:8])
    letter = _LETTERS[int(digit)]
    if s[0] in "ABEH":
        return s[8] == digit
    if s[0] in "NPQRSW":
        return s[8] == letter
    return s[8] in (digit, letter)


def es_vat(_rng, nif: str) -> str:
    return "ES" + nif


def es_vat_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    return s.startswith("ES") and cif_valid(s[2:])


LOCALE = Locale(
    country="ES", name="Spain", languages=("spa", "cat", "eus", "glg"),
    money=MoneyFormat("EUR", "€", ",", "."),
    timezone="Europe/Madrid",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2100, "food": 400, "accommodation": 1000, "books": 400, "passenger_transport": 1000,
            "restaurant": 1000},
    vat_as_of="2025",
    vat_source="Ley 37/1992 del IVA art. 90–91 (21 %; 4 % basic food such as bread, milk, eggs, fruit and "
               "vegetables, and books, back to 4 % from 1 January 2025 after the temporary 0 %/2 %; 10 % "
               "accommodation, passenger transport and restaurants); AEAT; EU Taxes in Europe Database",
    company_id=cif,
    vat_id=es_vat,                                  # ES + the company NIF
    vat_id_valid=es_vat_valid,
    payment_reference=banking.rf_reference,
    payment_reference_name={"spa": "referencia de pago (RF)", "cat": "referència de pagament (RF)",
                            "eus": "ordainketa-erreferentzia (RF)", "glg": "referencia de pagamento (RF)"},
    company_suffixes=("S.L.", "S.A.", "S.L.U."),
    company_stems=("Sierra Clara", "Monteclaro", "Río Claro", "Los Olivos", "Alameda", "Vega Alta", "Peñaverde",
                   "Mirasol", "Fuentesol", "Robledal"),
    first_names=("Lucía", "Hugo", "María", "Martín", "Paula", "Daniel", "Carmen", "Pablo", "Laura", "Javier",
                 "Sofía", "Alejandro"),
    last_names=("García", "Rodríguez", "González", "Fernández", "López", "Martínez", "Sánchez", "Pérez", "Gómez",
                "Martín", "Jiménez", "Ruiz"),
    cities=("Madrid", "Barcelona", "Valencia", "Sevilla", "Zaragoza", "Bilbao", "Málaga", "Vigo"),
    office_hours=("09:00", "18:00"), lunch=("14:00", "15:00"),
    date_style="DD/MM/YYYY",
    notes=["Holidays are the national set common to all of Spain; Jueves Santo, Easter Monday and the autonomous "
           "communities' days (e.g. 11 September in Catalonia, 25 July in Galicia) are regional.",
           "VAT is the peninsular and Balearic rate; the Canary Islands (IGIC), Ceuta and Melilla (IPSI) have their "
           "own taxes.",
           "The Canary Islands use Atlantic/Canary time.",
           "Spanish style does not group four-digit numbers (1234,56 €); amounts here are always grouped."],
)
