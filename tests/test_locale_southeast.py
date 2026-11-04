"""Southeast and East Europe packs (BG RO GR CY AL BA RS MK TR UA GE) against independent oracles.

Holidays: the shared test in test_locales.py requires an exact match with the `holidays` package. That cannot hold
where the package lists days the rule engine cannot express:
- lunar Islamic holidays (TR Ramazan/Kurban Bayramı, AL Bajrams, BA Bajrams, MK Ramazan Bajram);
- weekend-substitute days (BG, RS, MK, AL; and the GR Labour Day move the package predicts for 2027).
Here every pack is compared with the package for 2024-2030 with `observed=False` and the lunar holidays removed;
everything else must match exactly. Albania's Easter Mondays are statutory substitute days for the Easter Sundays
(always a Sunday), so the pack models them and the test checks them against the package's observed set separately.
"""
import random

import holidays
import pytest
from stdnum import iso11649
from stdnum.al import nipt
from stdnum.bg import vat as bg_vat
from stdnum.cy import vat as cy_vat
from stdnum.gr import vat as gr_vat
from stdnum.iso7064 import mod_97_10
from stdnum.mk import edb
from stdnum.ro import cf as ro_cf
from stdnum.ro import cui as ro_cui
from stdnum.rs import pib
from stdnum.tr import vkn
from stdnum.ua import edrpou

from eurl import banking
from eurl.calendar import days_off
from eurl.locales import load
from eurl.locales import al, ba, bg, cy, ge, gr, mk, ro, rs, tr, ua
from eurl.money import format_money, parse_money

PACKS = ("BG", "RO", "GR", "CY", "AL", "BA", "RS", "MK", "TR", "UA", "GE")
YEARS = range(2024, 2031)
# Substrings of the package's names for the lunar holidays the packs do not model.
LUNAR = {"TR": ("Ramazan Bayramı", "Kurban Bayramı"), "AL": ("Bajramit",), "BA": ("Bajram",), "MK": ("Бајрам",)}


def _package(country, year):
    theirs = holidays.country_holidays(country, years=year, observed=False)
    lunar = LUNAR.get(country, ())
    # a date is dropped only when every holiday on it is lunar (the package joins names with "; ")
    out = {d for d, name in theirs.items() if not all(any(s in part for s in lunar) for part in name.split("; "))}
    return out


def _al_easter_mondays(year):
    return {d for d, rule in days_off(al.HOLIDAYS, year).items() if "E hëna pas Pashkëve" in rule.names["sqi"]}


@pytest.mark.parametrize("country", PACKS)
def test_holidays_match_package_without_lunar_and_substitute_days(country):
    locale = load(country)
    for year in YEARS:
        ours = set(days_off(locale.holidays, year, public_only=True))
        theirs = _package(country, year)
        if country == "AL":
            # Easter Monday = the substitute day for Easter Sunday; the package lists it only as an observed day,
            # one day later when Monday is already a substitute day (2027: 1 May on a Saturday -> 3 May).
            mondays = _al_easter_mondays(year)
            observed = holidays.country_holidays("AL", years=year)
            substitutes = {d for d, name in observed.items() if "Pashkëve" in name and "shtyrë" in name}
            assert len(mondays) == len(substitutes) and all(
                any(0 <= (s - m).days <= 1 for s in substitutes) for m in mondays), (year, mondays, substitutes)
            ours -= mondays
        assert ours == theirs, (country, year, sorted(ours ^ theirs))


@pytest.mark.parametrize("country", ["TR", "AL", "BA", "MK"])
def test_lunar_holidays_are_documented(country):
    locale = load(country)
    module = {"TR": tr, "AL": al, "BA": ba, "MK": mk}[country]
    text = " ".join(locale.notes)
    assert "lunar" in text and "NOT MODELLED" in text
    assert all(name in text for name in module.LUNAR_HOLIDAYS)


def test_ukraine_martial_law():
    assert load("UA").holidays == ()
    for year in YEARS:
        assert not holidays.country_holidays("UA", years=year)
        suspended = set(days_off(ua.STATUTORY_SUSPENDED, year))
        assert suspended == set(holidays.country_holidays("UA", years=year, categories=("workday",))), year


def test_identifiers_against_stdnum():
    rng = random.Random(11)
    for _ in range(500):
        v = bg.vat_id(rng, bg.eik(rng))
        assert bg_vat.is_valid(v) and bg.vat_id_valid(v)
        c = ro.cui(rng)
        assert ro_cui.is_valid(c) and ro_cf.is_valid(ro.vat_id(rng, c)) and ro.vat_id_valid(ro.vat_id(rng, c))
        v = gr.vat_id(rng, gr.afm(rng))
        assert gr_vat.is_valid(v) and gr.vat_id_valid(v)
        v = cy.vat_id(rng, cy.company_number(rng))
        assert cy_vat.is_valid(v) and cy.vat_id_valid(v)
        n = al.nipt(rng)
        assert nipt.is_valid(n) and al.vat_id_valid(n)
        p = rs.pib(rng)
        assert pib.is_valid(p) and rs.vat_id_valid(p)
        e = mk.edb(rng)
        assert edb.is_valid(e) and mk.vat_id_valid(mk.vat_id(rng, e))
        k = tr.vkn(rng)
        assert vkn.is_valid(k) and tr.vat_id_valid(k)
        u = ua.edrpou(rng)
        assert edrpou.is_valid(u) and ua.vat_id_valid(ua.vat_id(rng, u))
        assert ua.vat_id(rng, u)[:7] == u[:7]


def test_real_world_examples_and_invalid_ones():
    # public examples from the python-stdnum documentation
    assert bg.vat_id_valid("BG175074752") and not bg.vat_id_valid("BG175074751")
    assert ro.vat_id_valid("RO18547290") and not ro.vat_id_valid("RO18547291")
    assert gr.vat_id_valid("EL094259216") and not gr.vat_id_valid("EL123456781")
    assert cy.vat_id_valid("CY10259033P") and not cy.vat_id_valid("CY10259033Z")
    assert al.vat_id_valid("J91402501L") and al.vat_id_valid("AL K22218003V") and not al.vat_id_valid("Z22218003V")
    assert rs.vat_id_valid("101134702") and not rs.vat_id_valid("101134703")
    assert mk.vat_id_valid("MK4030000375897") and not mk.vat_id_valid("MK4030000375890")
    assert tr.vat_id_valid("4540536920") and not tr.vat_id_valid("4540536921")
    assert ua._edrpou_check("3285596") == "1" and ua._edrpou_check("3285596") != "8"
    assert not ge.vat_id_valid("12345678") and not ua.vat_id_valid("123456789012")   # region code 89


def test_formats_without_stdnum_validator():
    """BA (JIB/PDV broj), GE (identification code) and the UA VAT payer's ІПН: no stdnum module."""
    rng = random.Random(4)
    for _ in range(300):
        j = ba.jib(rng)
        assert len(j) == 13 and j[0] == "4" and ba.vat_id_valid(ba.vat_id(rng, j)) and len(ba.vat_id(rng, j)) == 12
        g = ge.company_code(rng)
        assert len(g) == 9 and g.isdigit() and ge.vat_id_valid(g)
    assert not ba.vat_id_valid("200000000000")


def test_payment_references():
    rng = random.Random(9)
    for country in ("BG", "RO", "GR", "CY"):
        assert load(country).payment_reference is banking.rf_reference
    for _ in range(300):
        assert iso11649.is_valid(banking.rf_reference(rng))
        ref = rs.model97(rng)
        assert ref.startswith("97 ") and rs.model97_valid(ref)
        digits = ref[3:]
        assert mod_97_10.is_valid(digits[2:] + digits[:2])
    for country in ("AL", "BA", "MK", "TR", "UA", "GE"):
        assert load(country).payment_reference(rng)
    assert not rs.model97_valid("97 00" + "1234567890")


def test_money_and_non_eu():
    examples = {"BG": "1\u00a0234,50 лв.", "RO": "1.234,50 lei", "GR": "1.234,50 €", "CY": "1.234,50 €",
                "AL": "1\u00a0234,50 Lekë", "BA": "1.234,50 KM", "RS": "1.234,50 дин.", "MK": "1.234,50 ден.",
                "TR": "1.234,50 TL", "UA": "1\u00a0234,50 грн", "GE": "1\u00a0234,50 ₾"}
    for country, text in examples.items():
        locale = load(country)
        assert format_money(123450, locale.money) == text
        assert parse_money(text) == 123450
        assert locale.eu_member == (country in ("BG", "RO", "GR", "CY"))
    assert set(load("BA").vat_bp.values()) == {1700} and set(load("GE").vat_bp.values()) == {1800}
    assert load("BG").money.currency == "BGN" and any("2026-01-01" in n for n in load("BG").notes)
