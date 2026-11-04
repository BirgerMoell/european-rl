import string

from eurl import banking
from eurl.calendar import easter_rule, fixed
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

# Código do Trabalho art. 234 (the four days suspended in 2013–2015 were restored in 2016). Carnaval is an optional
# holiday (art. 235) that most employers grant: modelled as customary. Municipal holidays (e.g. Santo António in
# Lisbon on 13 June, São João in Porto on 24 June) are local and not modelled.
HOLIDAYS = (
    fixed(1, 1, {"por": "Ano Novo"}),
    easter_rule(-2, {"por": "Sexta-feira Santa"}),
    easter_rule(0, {"por": "Páscoa"}),
    fixed(4, 25, {"por": "Dia da Liberdade"}),
    fixed(5, 1, {"por": "Dia do Trabalhador"}),
    fixed(6, 10, {"por": "Dia de Portugal, de Camões e das Comunidades Portuguesas"}),
    easter_rule(60, {"por": "Corpo de Deus"}),
    fixed(8, 15, {"por": "Assunção de Nossa Senhora"}),
    fixed(10, 5, {"por": "Implantação da República"}),
    fixed(11, 1, {"por": "Dia de Todos os Santos"}),
    fixed(12, 1, {"por": "Restauração da Independência"}),
    fixed(12, 8, {"por": "Imaculada Conceição"}),
    fixed(12, 25, {"por": "Dia de Natal"}),
    # Optional holiday, customary day off.
    easter_rule(-47, {"por": "Carnaval"}, public=False),
)


# --- NIPC (número de identificação de pessoa coletiva): 9 digits, weights 9..2, mod 11 ---------------------------

def _check(eight: str) -> str:
    total = sum((9 - i) * int(d) for i, d in enumerate(eight))
    return str((11 - total % 11) % 11 % 10)


def nipc(rng):
    eight = "5" + "".join(rng.choice(string.digits) for _ in range(7))   # 5 = pessoa coletiva
    return eight + _check(eight)


def pt_vat(_rng, number: str) -> str:
    return "PT" + number


def pt_vat_valid(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if not s.startswith("PT"):
        return False
    s = s[2:]
    return len(s) == 9 and s.isdigit() and s[0] != "0" and _check(s[:8]) == s[8]


LOCALE = Locale(
    country="PT", name="Portugal", languages=("por",),
    money=MoneyFormat("EUR", "€", ",", NBSP),
    timezone="Europe/Lisbon",
    holidays=HOLIDAYS,
    vat_bp={"standard": 2300, "food": 600, "accommodation": 600, "books": 600, "passenger_transport": 600,
            "restaurant": 1300},
    vat_as_of="2025",
    vat_source="Código do IVA art. 18 and Listas I–II (mainland: 23 %; 6 % basic food, accommodation, books, "
               "passenger transport; 13 % restaurant meals, most drinks 23 %); Autoridade Tributária; EU Taxes in "
               "Europe Database",
    company_id=nipc,
    vat_id=pt_vat,                                  # PT + the NIPC
    vat_id_valid=pt_vat_valid,
    payment_reference=banking.rf_reference, payment_reference_name={"por": "referência de pagamento (RF)"},
    company_suffixes=("Lda.", "S.A.", "Unipessoal Lda."),
    company_stems=("Vale Verde", "Monte Claro", "Ribeira Alta", "Quinta do Sol", "Serra Azul", "Alto Mira",
                   "Fonte Clara", "Lagoa Mansa", "Casal Novo", "Pinhal Alto"),
    first_names=("Maria", "João", "Ana", "Francisco", "Beatriz", "Tiago", "Inês", "Rodrigo", "Carolina", "Miguel",
                 "Leonor", "Duarte"),
    last_names=("Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Costa", "Rodrigues", "Martins", "Sousa",
                "Fernandes", "Gonçalves", "Gomes"),
    cities=("Lisboa", "Porto", "Braga", "Coimbra", "Aveiro", "Faro", "Évora", "Setúbal"),
    office_hours=("09:00", "18:00"), lunch=("13:00", "14:00"),
    date_style="DD/MM/YYYY",
    notes=["VAT rates are mainland Portugal; the Azores and Madeira apply lower regional rates.",
           "The Azores use Atlantic/Azores time.",
           "Carnaval (Shrove Tuesday) is an optional holiday, modelled as a customary day off.",
           "Multibanco payment references (entity + reference) exist but depend on the payee's entity; payments "
           "use the RF reference."],
)
