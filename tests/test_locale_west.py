"""West/South locale packs (AT, BE, LU, NL, IE, MT, IT, ES, PT): identifiers against python-stdnum, known real-world
examples, known invalid examples, and the custom holiday rules."""
import datetime as dt
import random

import pytest
from stdnum import iso11649
from stdnum.at import businessid as at_businessid
from stdnum.at import uid as at_uid
from stdnum.be import ogm_vcs
from stdnum.be import vat as be_vat
from stdnum.es import cif as es_cif
from stdnum.es import nif as es_nif
from stdnum.ie import vat as ie_vat
from stdnum.it import iva as it_iva
from stdnum.lu import tva as lu_tva
from stdnum.mt import vat as mt_vat
from stdnum.nl import btw as nl_btw
from stdnum.pt import nif as pt_nif

from eurl.calendar import days_off
from eurl.locales import load

WEST = ("AT", "BE", "LU", "NL", "IE", "MT", "IT", "ES", "PT")
STDNUM_VAT = {"AT": at_uid, "BE": be_vat, "LU": lu_tva, "NL": nl_btw, "IE": ie_vat, "MT": mt_vat, "IT": it_iva,
              "ES": es_nif, "PT": pt_nif}


@pytest.mark.parametrize("cc", WEST)
def test_generated_vat_ids_pass_stdnum(cc):
    locale = load(cc)
    rng = random.Random(11)
    for _ in range(1000):
        company = locale.company_id(rng)
        vat = locale.vat_id(rng, company)
        assert vat.startswith(cc) and " " not in vat, vat
        assert locale.vat_id_valid(vat), vat
        assert STDNUM_VAT[cc].is_valid(vat), vat


@pytest.mark.parametrize("cc", WEST)
def test_validators_agree_with_stdnum_on_random_strings(cc):
    """Mutating one digit of a valid number: our verdict equals stdnum's."""
    locale = load(cc)
    rng = random.Random(23)
    for _ in range(1000):
        vat = locale.vat_id(rng, locale.company_id(rng))
        positions = [i for i, ch in enumerate(vat) if ch.isdigit()]
        i = rng.choice(positions)
        mutated = vat[:i] + str((int(vat[i]) + rng.randint(1, 9)) % 10) + vat[i + 1:]
        assert locale.vat_id_valid(mutated) == STDNUM_VAT[cc].is_valid(mutated), mutated


def test_company_ids_against_stdnum():
    rng = random.Random(5)
    for _ in range(500):
        assert at_businessid.is_valid(load("AT").company_id(rng))
        be = load("BE").company_id(rng)
        assert be_vat.is_valid(be) and len(be) == 12 and be[4] == "."
        assert es_cif.is_valid(load("ES").company_id(rng))
        assert pt_nif.is_valid(load("PT").company_id(rng))
        assert it_iva.is_valid(load("IT").company_id(rng))


# Known-valid published numbers (stdnum documentation examples and long-standing public registrations).
KNOWN_VALID = {
    "AT": ["ATU13585627"],
    "BE": ["BE0428759497", "BE 0403.019.261"],
    "LU": ["LU15027442", "LU 150 274 42"],
    "NL": ["NL004495445B01", "NL002455799B11"],
    "IE": ["IE6433435F", "IE6433435OA", "IE8D79739I"],
    "MT": ["MT11679112"],
    "IT": ["IT00743110157"],
    "ES": ["ESJ99216582", "ESA13585625"],
    "PT": ["PT501964843"],
}
KNOWN_INVALID = {
    "AT": ["ATU13585626", "AT13585627"],
    "BE": ["BE0431150351", "BE2428759497"],
    "LU": ["LU15027443", "15027442"],
    "NL": ["NL123456789B90", "NL004495445C01"],
    "IE": ["IE6433435E", "IE6433435OB"],
    "MT": ["MT11679113", "MT01679112"],
    "IT": ["IT00743110158", "IT00743112007"],
    "ES": ["ESJ99216583", "ESB1358562A"],
    "PT": ["PT501964842", "PT001964843"],
}


@pytest.mark.parametrize("cc", WEST)
def test_known_examples(cc):
    locale = load(cc)
    for value in KNOWN_VALID[cc]:
        assert locale.vat_id_valid(value), value
        assert STDNUM_VAT[cc].is_valid(value), value
    for value in KNOWN_INVALID[cc]:
        assert not locale.vat_id_valid(value), value


def test_austrian_firmenbuch_check_letter():
    from eurl.locales.at import firmenbuchnummer_valid
    assert firmenbuchnummer_valid("FN 122119m")
    assert not firmenbuchnummer_valid("FN 122119a")


def test_payment_references():
    rng = random.Random(9)
    for _ in range(300):
        assert ogm_vcs.is_valid(load("BE").payment_reference(rng))
        for cc in ("AT", "LU", "NL", "IE", "MT", "IT", "ES", "PT"):
            assert iso11649.is_valid(load(cc).payment_reference(rng)), cc
    for cc in WEST:
        locale = load(cc)
        assert set(locale.payment_reference_name) == set(locale.languages), cc


def _dates(cc, year, public_only=False):
    return sorted(days_off(load(cc).holidays, year, public_only))


def test_custom_holiday_rules():
    # Koningsdag moves to the 26th when the 27th is a Sunday (2025); Bevrijdingsdag off in lustrum years
    assert dt.date(2025, 4, 26) in _dates("NL", 2025) and dt.date(2025, 4, 27) not in _dates("NL", 2025)
    assert dt.date(2026, 4, 27) in _dates("NL", 2026)
    assert dt.date(2025, 5, 5) in _dates("NL", 2025) and dt.date(2025, 5, 5) not in _dates("NL", 2025, True)
    assert dt.date(2026, 5, 5) not in _dates("NL", 2026)
    # Saint Brigid's Day: first Monday of February, or 1 February when that is a Friday
    assert dt.date(2025, 2, 3) in _dates("IE", 2025)
    assert dt.date(2030, 2, 1) in _dates("IE", 2030) and dt.date(2030, 2, 4) not in _dates("IE", 2030)
    assert not any(d.month == 2 for d in _dates("IE", 2022))
    # Spain: a national holiday on a Sunday is not in the national list
    assert dt.date(2025, 10, 12) not in _dates("ES", 2025) and dt.date(2026, 10, 12) in _dates("ES", 2026)
    # Italy: San Francesco from 2026
    assert dt.date(2025, 10, 4) not in _dates("IT", 2025) and dt.date(2026, 10, 4) in _dates("IT", 2026)


@pytest.mark.parametrize("cc", WEST)
def test_holiday_names_cover_every_language(cc):
    locale = load(cc)
    for rule in locale.holidays:
        assert set(rule.names) == set(locale.languages), (cc, rule.names)


def test_prices_are_in_euro():
    for cc in WEST:
        locale = load(cc)
        assert locale.money.currency == "EUR" and locale.price_scale == 1 and locale.eu_member
