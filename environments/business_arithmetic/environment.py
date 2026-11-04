"""Exact business arithmetic in local number formats: the calculations office work depends on.

Our baselines showed the 9B checkpoints fail invoices mostly through arithmetic slips (581.88 × 25.5 % written as
148.25), so this environment trains the calculations themselves, exact to the minor unit, with numbers and answers in
the locale's own format (decimal comma or point, grouping). Commercial rounding (half up) at the end of each task
unless the task says otherwise.

Task types (meta.kind) and levels (meta.level):
  1  percent_of, add_vat, line_total
  2  remove_vat, discount_chain, convert, split
  3  interest, margin_price, discount_then_vat, convert_then_vat
Every task is answerable (no abstention). Shortcut probes cover the classic slips: truncating instead of rounding,
removing VAT by multiplying by (1 - rate), adding chained discounts, splitting without the remainder rule.

Text: text/<iso639-3>.json per language (one short template per task type).
"""
from __future__ import annotations

import json
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

from eurl.contract import TypedEnvironment, TypedTask
from eurl.languages import LANGUAGES
from eurl.locales import PACKS
from eurl.locales import load as load_locale
from eurl.money import format_money

TEXT_DIR = Path(__file__).parent / "text"
LEVELS = {1: ("percent_of", "add_vat", "line_total"), 2: ("remove_vat", "discount_chain", "convert", "split"),
          3: ("interest", "margin_price", "discount_then_vat", "convert_then_vat")}
CURRENCIES = ("EUR", "SEK", "PLN", "CZK", "HUF", "DKK", "NOK", "RON", "CHF", "GBP", "USD")


@lru_cache(maxsize=None)
def text(lang: str) -> dict:
    return json.loads((TEXT_DIR / f"{lang}.json").read_text(encoding="utf-8"))


def languages() -> tuple:
    return tuple(sorted(p.stem for p in TEXT_DIR.glob("*.json")))


def locales_for(lang: str) -> tuple:
    packs = {p.upper() for p in PACKS}
    return tuple(sorted(packs)) if lang == "eng" else tuple(c for c in LANGUAGES[lang].countries if c in packs)


def half_up(x: Fraction) -> int:
    """Commercial rounding of a non-negative or negative exact value to an integer (halves away from zero)."""
    sign = -1 if x < 0 else 1
    x = abs(x)
    return sign * int((x * 2 + 1) // 2)


def number(value: Fraction, decimals: int, loc) -> str:
    """A plain number (rate, quantity, exchange rate) in the locale's decimal style, without grouping."""
    if decimals == 0:
        return str(int(value))
    scaled = half_up(value * 10 ** decimals)
    whole, frac = divmod(abs(scaled), 10 ** decimals)
    return ("-" if scaled < 0 else "") + f"{whole}{loc.money.decimal}{frac:0{decimals}d}"


class BusinessArithmetic(TypedEnvironment):
    id = "business_arithmetic"
    abstention = False

    @property
    def languages(self) -> tuple:
        return tuple(lang for lang in languages() if locales_for(lang))

    def generate(self, rng, language=None) -> TypedTask:
        lang = language or rng.choice(self.languages)
        t = text(lang)
        loc = load_locale(rng.choice(locales_for(lang)))
        f = loc.money
        unit = 10 ** f.minor_digits
        level = rng.choice([1, 2, 3])
        kind = rng.choice(LEVELS[level])

        def amount(lo=10, hi=5000):  # in minor units
            major = rng.randint(lo, hi) * loc.price_scale
            return major * unit + (rng.randint(0, unit - 1) if unit > 1 else 0)

        def money(m):
            return format_money(m, f)

        def pct():
            return Fraction(rng.choice([5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 27]) * 10 +
                            rng.choice([0, 0, 0, 5]), 10)

        slips = {}
        if kind == "percent_of":
            a, p = amount(), pct()
            exact = Fraction(a) * p / 100
            due = half_up(exact)
            slips["truncated"] = int(exact)
            prompt = t["percent_of"].format(p=number(p, 1 if p.denominator > 1 else 0, loc), amount=money(a))
        elif kind == "add_vat":
            a, p = amount(), pct()
            exact = Fraction(a) * (100 + p) / 100
            due = half_up(exact)
            slips["truncated"] = int(exact)
            prompt = t["add_vat"].format(p=number(p, 1 if p.denominator > 1 else 0, loc), amount=money(a))
        elif kind == "line_total":
            lines = [(rng.randint(1, 25), amount(1, 400)) for _ in range(rng.randint(2, 4))]
            due = sum(q * u for q, u in lines)
            slips["drop_last_line"] = sum(q * u for q, u in lines[:-1])
            rows = "\n".join(t["line"].format(qty=q, price=money(u)) for q, u in lines)
            prompt = t["line_total"].format(lines=rows)
        elif kind == "remove_vat":
            gross, p = amount(), pct()
            exact = Fraction(gross) * 100 / (100 + p)
            due = half_up(exact)
            slips["multiply_by_1_minus_rate"] = half_up(Fraction(gross) * (100 - p) / 100)
            prompt = t["remove_vat"].format(p=number(p, 1 if p.denominator > 1 else 0, loc), amount=money(gross))
        elif kind == "discount_chain":
            a = amount()
            p1, p2 = Fraction(rng.choice([5, 10, 15, 20, 25, 30])), Fraction(rng.choice([2, 3, 5, 10]))
            exact = Fraction(a) * (100 - p1) / 100 * (100 - p2) / 100
            due = half_up(exact)
            slips["added_discounts"] = half_up(Fraction(a) * (100 - p1 - p2) / 100)
            prompt = t["discount_chain"].format(amount=money(a), p1=int(p1), p2=int(p2))
        elif kind in ("convert", "convert_then_vat"):
            other = rng.choice([c for c in CURRENCIES if c != f.currency])
            rate = Fraction(rng.randint(1000, 300000), 10000)          # local units per 1 unit of `other`, 4 decimals
            src_major = Fraction(rng.randint(1000, 500000), 100)        # amount in the other currency, 2 decimals
            exact = src_major * rate * unit
            if kind == "convert":
                due = half_up(exact)
                slips["divided_by_rate"] = half_up(src_major / rate * unit)
                prompt = t["convert"].format(src=number(src_major, 2, loc), cur=other, rate=number(rate, 4, loc),
                                             local=f.currency)
            else:
                p = pct()
                net = half_up(exact)
                due = half_up(Fraction(net) * (100 + p) / 100)
                slips["vat_skipped"] = net
                prompt = t["convert_then_vat"].format(src=number(src_major, 2, loc), cur=other,
                                                      rate=number(rate, 4, loc), local=f.currency,
                                                      p=number(p, 1 if p.denominator > 1 else 0, loc))
        elif kind == "split":
            total, n = amount(100, 9000), rng.randint(3, 9)
            share, rest = divmod(total, n)
            due = share + rest            # the first person pays the remainder (so the shares add up exactly)
            slips["equal_share_rounded"] = half_up(Fraction(total, n))
            prompt = t["split"].format(amount=money(total), n=n)
        elif kind == "interest":
            a = amount(1000, 20000)
            r = Fraction(rng.choice([15, 20, 25, 30, 35, 40, 45, 50, 60, 75]), 10)
            months = rng.choice([3, 4, 6, 8, 9, 10, 18])
            exact = Fraction(a) * r / 100 * months / 12
            due = half_up(exact)
            slips["full_year"] = half_up(Fraction(a) * r / 100)
            prompt = t["interest"].format(amount=money(a), r=number(r, 1, loc), months=months)
        elif kind == "margin_price":
            cost, m = amount(), Fraction(rng.choice([10, 15, 20, 25, 30, 35, 40]))
            exact = Fraction(cost) * 100 / (100 - m)
            due = half_up(exact)
            slips["markup_instead_of_margin"] = half_up(Fraction(cost) * (100 + m) / 100)
            prompt = t["margin_price"].format(cost=money(cost), m=int(m))
        else:  # discount_then_vat
            a, d, p = amount(), Fraction(rng.choice([5, 10, 15, 20])), pct()
            net = half_up(Fraction(a) * (100 - d) / 100)
            due = half_up(Fraction(net) * (100 + p) / 100)
            slips["vat_before_discount_rounding"] = half_up(Fraction(a) * (100 - d) / 100 * (100 + p) / 100)
            prompt = t["discount_then_vat"].format(amount=money(a), d=int(d),
                                                   p=number(p, 1 if p.denominator > 1 else 0, loc))
        instruction = prompt + "\n\n" + t["rounding"]
        spec = {"type": "money", "value": due, "minor_digits": f.minor_digits}
        meta = {"level": level, "kind": kind, "locale": loc.country, "currency": f.currency,
                "slips": {k: v for k, v in slips.items() if v != due}}
        return TypedTask(instruction, spec, "money", lang, loc.country, meta)

    def extra_probes(self, prompt: str) -> dict:
        f = load_locale(self._task.locale).money
        probes = {f"slip_{k}": f"ANSWER: {format_money(v, f)}" for k, v in self._task.meta["slips"].items()}
        probes["off_by_one_minor_unit"] = f"ANSWER: {format_money(self._task.spec['value'] + 1, f)}"
        return probes


def create():
    return BusinessArithmetic()
