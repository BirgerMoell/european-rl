"""business_arithmetic: an independent solver parses each prompt through its own template (placeholders become
capture groups) and recomputes the answer with exact fractions; then the contract qualification."""
import re
from fractions import Fraction

import pytest

from environments.business_arithmetic.environment import BusinessArithmetic, text
from eurl.locales import load
from eurl.money import parse_money
from eurl.validation import validate_typed


def _match(template, prompt):
    pattern = re.escape(template)
    for name in re.findall(r"\{(\w+)\}", template):
        pattern = pattern.replace(re.escape("{" + name + "}"), f"(?P<{name}>.+?)", 1)
        pattern = pattern.replace(re.escape("{" + name + "}"), f"(?P={name})")
    return re.match(pattern, prompt, re.S)


def _num(s, loc):
    return Fraction(s.replace(loc.money.decimal, ".")) if loc.money.decimal != "." else Fraction(s)


def _half_up(x):
    return int((abs(x) * 2 + 1) // 2) * (-1 if x < 0 else 1)


def solve(env):
    t, loc = text(env._task.language), load(env._task.locale)
    digits, prompt = loc.money.minor_digits, env._task.instruction.split("\n\n" + t["rounding"])[0]
    unit = 10 ** digits
    money = lambda s: parse_money(s, digits)
    for kind in ("percent_of", "add_vat", "line_total", "remove_vat", "discount_chain", "convert_then_vat", "convert",
                 "split", "interest", "margin_price", "discount_then_vat"):
        m = _match(t[kind], prompt)
        if not m:
            continue
        g = m.groupdict()
        if kind == "percent_of":
            return _half_up(money(g["amount"]) * _num(g["p"], loc) / 100)
        if kind == "add_vat":
            return _half_up(money(g["amount"]) * (100 + _num(g["p"], loc)) / 100)
        if kind == "line_total":
            line = re.escape(t["line"]).replace(re.escape("{qty}"), r"(\d+)").replace(re.escape("{price}"), r"(.+)")
            return sum(int(q) * money(p) for q, p in re.findall(line, g["lines"]))
        if kind == "remove_vat":
            return _half_up(Fraction(money(g["amount"])) * 100 / (100 + _num(g["p"], loc)))
        if kind == "discount_chain":
            return _half_up(Fraction(money(g["amount"])) * (100 - int(g["p1"])) / 100 * (100 - int(g["p2"])) / 100)
        if kind == "convert":
            return _half_up(_num(g["src"], loc) * _num(g["rate"], loc) * unit)
        if kind == "convert_then_vat":
            net = _half_up(_num(g["src"], loc) * _num(g["rate"], loc) * unit)
            return _half_up(Fraction(net) * (100 + _num(g["p"], loc)) / 100)
        if kind == "split":
            share, rest = divmod(money(g["amount"]), int(g["n"]))
            return share + rest
        if kind == "interest":
            return _half_up(Fraction(money(g["amount"])) * _num(g["r"], loc) / 100 * int(g["months"]) / 12)
        if kind == "margin_price":
            return _half_up(Fraction(money(g["cost"])) * 100 / (100 - int(g["m"])))
        if kind == "discount_then_vat":
            net = _half_up(Fraction(money(g["amount"])) * (100 - int(g["d"])) / 100)
            return _half_up(Fraction(net) * (100 + _num(g["p"], loc)) / 100)
    raise AssertionError("no template matched: " + prompt[:200])


@pytest.mark.parametrize("lang", BusinessArithmetic().languages)
def test_independent_solver_agrees(lang):
    env = BusinessArithmetic()
    for seed in range(120):
        env.reset(seed, "dev", lang)
        assert solve(env) == env._task.spec["value"], (lang, seed, env._task.meta)


def test_contract_qualification():
    report = validate_typed("business_arithmetic", cases=40)
    assert report["status"] == "passed" and max(report["probe_mean_reward"].values()) <= 0.3
