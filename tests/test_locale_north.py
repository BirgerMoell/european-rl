"""North, Central and Baltic locale packs (DK NO IS EE LV LT CZ SK HU SI HR): identifiers cross-checked with
python-stdnum, known real-world examples, known invalid examples, national payment references."""
import importlib
import random

import pytest
from stdnum import iso11649, luhn
from stdnum.cz import dic as cz_dic
from stdnum.dk import cvr as dk_cvr
from stdnum.ee import kmkr as ee_kmkr
from stdnum.ee import registrikood as ee_registrikood
from stdnum.hr import oib as hr_oib
from stdnum.hu import anum as hu_anum
from stdnum.is_ import kennitala as is_kennitala
from stdnum.is_ import vsk as is_vsk
from stdnum.lt import pvm as lt_pvm
from stdnum.lv import pvn as lv_pvn
from stdnum.no import mva as no_mva
from stdnum.no import orgnr as no_orgnr
from stdnum.si import ddv as si_ddv
from stdnum.si import maticna as si_maticna
from stdnum.sk import dph as sk_dph

from eurl.locales import load
from eurl.money import format_money, parse_money

PACKS = ("DK", "NO", "IS", "EE", "LV", "LT", "CZ", "SK", "HU", "SI", "HR")

# country -> (company-id validator, VAT-id validator), both from python-stdnum
STDNUM = {
    "DK": (dk_cvr.is_valid, dk_cvr.is_valid),
    "NO": (no_orgnr.is_valid, no_mva.is_valid),
    "IS": (is_kennitala.is_valid, is_vsk.is_valid),
    "EE": (ee_registrikood.is_valid, ee_kmkr.is_valid),
    "LV": (lv_pvn.is_valid, lv_pvn.is_valid),
    "LT": (None, lt_pvm.is_valid),          # stdnum has no validator for the company code
    "CZ": (cz_dic.is_valid, cz_dic.is_valid),
    "SK": (None, sk_dph.is_valid),          # nor for the Slovak IČO
    "HU": (lambda v: hu_anum.is_valid(v[:8]), hu_anum.is_valid),
    "SI": (si_maticna.is_valid, si_ddv.is_valid),
    "HR": (hr_oib.is_valid, hr_oib.is_valid),
}


@pytest.mark.parametrize("country", PACKS)
def test_generated_identifiers_pass_stdnum(country):
    locale = load(country)
    company_ok, vat_ok = STDNUM[country]
    rng = random.Random(11)
    for _ in range(500):
        company = locale.company_id(rng)
        vat = locale.vat_id(rng, company)
        if company_ok:
            assert company_ok(company), (country, company)
        assert vat_ok(vat), (country, vat)
        assert locale.vat_id_valid(vat), (country, vat)
        if locale.eu_member:
            assert vat.startswith(country), vat


# Public examples from the python-stdnum documentation (numbers of real registered entities), and one invalid each.
VALID_VAT = {
    "DK": "DK13585628", "NO": "NO995525828MVA", "IS": "00621", "EE": "EE100594102", "LV": "LV40003521600",
    "LT": "LT119511515", "CZ": "CZ25123891", "SK": "SK2022749619", "HU": "HU12892312", "SI": "SI50223054",
    "HR": "HR33392005961",
}
INVALID_VAT = {
    "DK": "DK13585627", "NO": "NO995525829MVA", "IS": "0062199", "EE": "EE100594103", "LV": "LV40003521601",
    "LT": "LT100001919018", "CZ": "CZ25123890", "SK": "SK2022749618", "HU": "HU12892313", "SI": "SI50223055",
    "HR": "HR33392005962",
}


@pytest.mark.parametrize("country", PACKS)
def test_known_vat_examples(country):
    locale = load(country)
    assert locale.vat_id_valid(VALID_VAT[country])
    assert not locale.vat_id_valid(INVALID_VAT[country])


def test_known_company_examples():
    no, is_, ee, lv, cz, hr = (importlib.import_module(f"eurl.locales.{c}") for c in ("no", "is", "ee", "lv", "cz", "hr"))
    assert no.orgnr_valid("988 077 917") and not no.orgnr_valid("988 077 918")
    assert is_.kennitala_valid("450401-3150") and not is_.kennitala_valid("450401-3160")
    assert ee.registrikood_valid("12345678") and not ee.registrikood_valid("12345679")
    assert lv.registracijas_numurs_valid("40003521600") and not lv.registracijas_numurs_valid("40003521601")
    assert cz.ico_valid("25123891") and not cz.ico_valid("25123890")
    assert hr.oib_valid("33392005961") and not hr.oib_valid("33392005962")


def test_payment_references():
    rng = random.Random(4)
    ee = importlib.import_module("eurl.locales.ee")
    for _ in range(300):
        assert luhn.is_valid(load("NO").payment_reference(rng))
        ref = load("EE").payment_reference(rng)
        assert ee.viitenumber_valid(ref)
        for country in ("DK", "IS", "LV", "LT", "HU", "SI", "HR"):
            assert iso11649.is_valid(load(country).payment_reference(rng))
        for country in ("CZ", "SK"):
            vs = load(country).payment_reference(rng)
            assert vs.isdigit() and len(vs) <= 10
    # Estonian reference numbers from the Pangaliit 7-3-1 description
    assert ee.viitenumber_valid("1232") and not ee.viitenumber_valid("1233")


def test_money_formats():
    assert format_money(123450, load("DK").money) == "1.234,50 kr."
    assert format_money(123450, load("NO").money) == "1 234,50 kr"
    assert format_money(123450, load("CZ").money) == "1 234,50 Kč"
    assert format_money(123450, load("HU").money) == "1 234,50 Ft"
    assert format_money(123450, load("SI").money) == "1.234,50 €"
    assert format_money(123450, load("HR").money) == "1.234,50 €"
    isk = load("IS").money
    assert format_money(1234567, isk) == "1.234.567 kr."
    rng = random.Random(9)
    for _ in range(300):
        minor = rng.randint(-10 ** 9, 10 ** 9)
        assert parse_money(format_money(minor, isk), isk.minor_digits) == minor


def test_non_eu_and_currencies():
    for country, currency, scale in (("NO", "NOK", 11), ("IS", "ISK", 150)):
        locale = load(country)
        assert not locale.eu_member and locale.money.currency == currency and locale.price_scale == scale
    assert load("IS").money.minor_digits == 0
    for country, currency, scale in (("DK", "DKK", 7), ("CZ", "CZK", 25), ("HU", "HUF", 400)):
        locale = load(country)
        assert locale.eu_member and locale.money.currency == currency and locale.price_scale == scale
    for country in ("EE", "LV", "LT", "SK", "SI", "HR"):
        assert load(country).money.currency == "EUR" and load(country).price_scale == 1


def test_recent_holiday_changes():
    import datetime as dt
    from eurl.calendar import days_off
    sk = load("SK").holidays
    assert dt.date(2025, 5, 8) in days_off(sk, 2025) and dt.date(2026, 5, 8) not in days_off(sk, 2026)
    assert dt.date(2027, 9, 15) in days_off(sk, 2027) and dt.date(2025, 11, 17) not in days_off(sk, 2025)
    hr = load("HR").holidays
    assert dt.date(2025, 5, 30) in days_off(hr, 2025) and dt.date(2025, 6, 25) not in days_off(hr, 2025)
    assert dt.date(2025, 4, 18) in days_off(load("HU").holidays, 2025)            # Good Friday since 2017
    assert dt.date(2025, 5, 16) not in days_off(load("DK").holidays, 2025)        # Store bededag abolished
    lv = load("LV").holidays
    assert dt.date(2025, 5, 5) in days_off(lv, 2025, public_only=True)            # 4 May on a Sunday
