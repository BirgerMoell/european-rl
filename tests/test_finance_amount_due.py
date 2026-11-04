"""finance_amount_due: an independent solver re-derives every answer from the public prompt alone (table, handbook
excerpt, credit note, payment, rounding and reverse-charge sentences), in every language, and must agree with the
generator. Then the contract qualification."""
import re

import pytest

from environments.finance_amount_due.environment import FinanceAmountDue, languages, text
from eurl.money import parse_money, round_half_up
from eurl.validation import validate_typed

ROW = re.compile(r"^\| (\d+) \| (.+?) \| (\d+) \| (.+?) \| (.+?) \|$", re.M)


def _pct(text):
    return round(float(text.replace(",", ".")) * 100)


def _sentence_amount(prompt, template):
    """The amount between the template's text before and after {amount} (works for any locale format)."""
    before, after = template.split("{amount}")
    m = re.search(re.escape(before) + r"(.+?)" + (re.escape(after[:8]) if after else r"$"), prompt, re.M)
    return parse_money(m.group(1)) if m else None


def solve(prompt: str, lang: str):
    t = text(lang)
    if t["missing_price"] in prompt:
        return "abstain"
    names = {v: k for k, v in t["categories"].items()}
    rates = {}
    hb = t["handbook"].split("{rates}")[0].split("{country}")[1]
    if hb.strip(":, ") and hb in prompt:
        tail = prompt.split(hb, 1)[1].split(". ", 1)[0]
        for part in tail.split("; "):
            m = re.match(r"\s*(.+?) (\d+(?:[.,]\d+)?) %", part)
            rates[names[m.group(1)]] = _pct(m.group(2))
    reverse_charge = t["buyer_vat"].split("{vat}")[0].split("{buyer_country}")[1] in prompt
    total = 0
    for _, _, qty, price, cell in ROW.findall(prompt):
        parts = [p.strip() for p in cell.split(", ") if p.strip()]
        discount = 0
        rest = []
        for p in parts:
            d = re.fullmatch(t["discount"].replace("{p}", r"(\d+)"), p)
            if d:
                discount = int(d.group(1))
            else:
                rest.append(p)
        cell_text = ", ".join(rest)
        rate_match = re.fullmatch(r"(\d+(?:[.,]\d+)?) %", cell_text)
        if rate_match:
            bp = _pct(rate_match.group(1))
        else:
            category = names[cell_text]
            if category not in rates:
                return "abstain"
            bp = rates[category]
        gross = int(qty) * parse_money(price)
        net = gross - round_half_up(gross * discount, 100)
        total += net + (0 if reverse_charge else round_half_up(net * bp, 10000))
    credit = _sentence_amount(prompt, t["credit"]) or 0
    if credit:
        standard = rates.get("standard")
        total -= credit + (0 if reverse_charge else round_half_up(credit * standard, 10000))
    paid = _sentence_amount(prompt, t["paid"]) or 0
    total -= paid
    if t["round"].split("{unit}")[0].strip() in prompt:
        total = round_half_up(total, 100) * 100
    return total


@pytest.mark.parametrize("lang", languages())
def test_independent_solver_agrees(lang):
    env = FinanceAmountDue()
    for seed in range(150):
        env.reset(seed, "dev", lang)
        expected = "abstain" if env._task.spec["type"] == "abstain" else env._task.spec["value"]
        assert solve(env.public_prompt(), lang) == expected, (lang, seed, env._task.meta)


def test_levels_and_locales_are_covered():
    env = FinanceAmountDue()
    seen = set()
    for seed in range(400):
        env.reset(seed, "train")
        seen.add((env._task.meta["level"], env._task.locale))
    assert {lvl for lvl, _ in seen} == {1, 2, 3, 4, 5}
    from eurl.locales import PACKS
    assert {loc for _, loc in seen} == {p.upper() for p in PACKS}


def test_contract_qualification():
    report = validate_typed("finance_amount_due", cases=60)
    assert report["status"] == "passed"
    assert not report["missing_string_tables"]
    assert max(report["probe_mean_reward"].values()) <= 0.3


def test_text_files_are_complete():
    from eurl.languages import LANGUAGES
    countries = {c for lang in LANGUAGES.values() for c in lang.countries}
    assert len(countries) == 36
    eng = text("eng")
    for lang in languages():
        t = text(lang)
        assert lang in LANGUAGES, lang
        assert set(t["countries"]) == countries, (lang, countries ^ set(t["countries"]))
        assert set(t["items"]) == set(eng["items"]) and set(t["categories"]) == set(eng["categories"])
        assert len(t["intro"]) >= 3 and len(t["question"]) >= 2
        assert t["handbook"].index("{country}") < t["handbook"].index("{rates}")
        assert "{p}" in t["discount"] and t["_review"] in ("author", "llm") or t["_review"].startswith("native:")
        for key in ("credit", "paid"):
            assert t[key].count("{amount}") == 1
