"""Locale packs against independent oracles: the `holidays` package for public holidays and python-stdnum for
identifiers and payment references (both dev-only dependencies)."""
import random

import holidays
import pytest
from stdnum import iban as std_iban
from stdnum import iso11649, luhn
from stdnum.be import ogm_vcs
from stdnum.de import vat as de_vat
from stdnum.fi import ytunnus
from stdnum.fr import tva
from stdnum.pl import nip
from stdnum.se import vat as se_vat

from eurl import banking, ids
from eurl.calendar import days_off, easter, orthodox_easter
from eurl.languages import LANGUAGES
from eurl.locales import VAT_CATEGORIES, all_packs, load
from eurl.money import format_money, parse_money

YEARS = range(2024, 2031)


def test_36_languages_match_europa():
    assert len(LANGUAGES) == 36
    assert sum(lang.eu_official for lang in LANGUAGES.values()) == 24


@pytest.mark.parametrize("year", range(1990, 2040))
def test_easter_algorithms(year):
    from dateutil.easter import EASTER_ORTHODOX, easter as du_easter
    assert easter(year) == du_easter(year)
    assert orthodox_easter(year) == du_easter(year, EASTER_ORTHODOX)


# Packs whose official calendars include days the rule engine cannot express (Islamic lunar holidays; statutory
# weekend-substitute days) are compared in tests/test_locale_southeast.py instead: observed=False, the declared
# lunar holidays (LUNAR_HOLIDAYS in the pack) removed, everything else exact for 2024-2030.
RELAXED_ORACLE = {"AL", "BA", "BG", "GR", "MK", "RS", "TR"}


@pytest.mark.parametrize("pack", [p.country for p in all_packs()])
def test_public_holidays_match_the_holidays_package(pack):
    if pack in RELAXED_ORACLE:
        pytest.skip("lunar or substitute holidays: checked in test_locale_southeast.py")
    locale = load(pack)
    for year in YEARS:
        public = set(days_off(locale.holidays, year, public_only=True))
        every = set(days_off(locale.holidays, year))
        theirs = set(holidays.SE(years=year, include_sundays=False) if pack == "SE"
                     else holidays.country_holidays(pack, years=year))
        # the package lists some customary days off (e.g. Finnish Midsummer Eve) as holidays; our public set or our
        # full days-off set must match it exactly
        assert theirs in (public, every), (pack, year, sorted(public ^ theirs), sorted(every ^ theirs))


@pytest.mark.parametrize("pack", [p.country for p in all_packs()])
def test_pack_fields(pack):
    locale = load(pack)
    assert set(locale.vat_bp) == set(VAT_CATEGORIES)
    assert all(0 <= bp < 3000 for bp in locale.vat_bp.values())  # 0 % is real (IE, MT zero-rating)
    assert all(lang in LANGUAGES for lang in locale.languages)
    for rule in locale.holidays:
        assert set(rule.names) <= set(locale.languages) and locale.language in rule.names
    rng = random.Random(1)
    for _ in range(200):
        company = locale.company_id(rng)
        vat = locale.vat_id(rng, company)
        assert locale.vat_id_valid(vat), (pack, vat)
        assert banking.iban_valid(banking.iban(rng, pack))


def test_identifiers_against_stdnum():
    rng = random.Random(7)
    for _ in range(500):
        org = ids.se_org(rng)
        assert se_vat.is_valid(ids.se_vat(org)) and ids.se_vat_valid(ids.se_vat(org))
        assert de_vat.is_valid(ids.de_vat(rng))
        siren = ids.fr_siren(rng)
        assert tva.is_valid(ids.fr_vat(siren)) and ids.fr_vat_valid(ids.fr_vat(siren))
        n = ids.pl_nip(rng)
        assert nip.is_valid(n) and ids.pl_nip_valid(n)
        y = ids.fi_ytunnus(rng)
        assert ytunnus.is_valid(y) and ids.fi_ytunnus_valid(y)
    assert not ids.de_vat_valid("DE123456789") or de_vat.is_valid("DE123456789")
    assert not ids.pl_nip_valid("1234567890") or nip.is_valid("1234567890")


def test_banking_against_stdnum():
    rng = random.Random(3)
    for country in banking.IBAN_LENGTH:
        assert 4 + sum(int(n) for n in __import__("re").findall(r"\d+", banking.BBAN[country])) == \
            banking.IBAN_LENGTH[country], country
        for _ in range(50):
            value = banking.iban(rng, country)
            assert len(value) == banking.IBAN_LENGTH[country]
            assert banking.iban_valid(value)
            assert std_iban.is_valid(value, check_country=False), value
    for example in ("DE89370400440532013000", "FR1420041010050500013M02606", "NL91ABNA0417164300",
                    "BE68539007547034", "PL61109010140000071219812874", "FI2112345600000785", "NO9386011117947"):
        assert banking.iban_valid(example)
    assert not banking.iban_valid("DE89370400440532013001")
    for _ in range(200):
        rf = banking.rf_reference(rng)
        assert iso11649.is_valid(rf) and banking.rf_valid(rf)
        ogm = banking.ogm_be(rng)
        assert ogm_vcs.is_valid(ogm) and banking.ogm_valid(ogm)
        assert luhn.is_valid(banking.ocr_se(rng)) and luhn.is_valid(banking.kid_no(rng))
        assert banking.viitenumero_valid(banking.viitenumero_fi(rng))
    assert banking.rf_valid("RF18539007547034")
    assert banking.viitenumero_valid("1232")


@pytest.mark.parametrize("pack", [p.country for p in all_packs()])
def test_money_round_trip(pack):
    f = load(pack).money
    rng = random.Random(5)
    for _ in range(300):
        minor = rng.randint(-10 ** 9, 10 ** 9)
        assert parse_money(format_money(minor, f), f.minor_digits) == minor
    assert format_money(123450, load("SE").money) == "1 234,50 kr"
    assert format_money(123450, load("DE").money) == "1.234,50 €"


def test_money_parsing_variants():
    for text in ("1 234,50 €", "1.234,50 EUR", "1234.50", "€1,234.50", "1 234,50 zł", "1 234:50 kr"):
        assert parse_money(text) in (123450, None)
    assert parse_money("1 234,50 €") == 123450 and parse_money("1234.50") == 123450
    assert parse_money("12,00 € oder 13,00 €") is None
