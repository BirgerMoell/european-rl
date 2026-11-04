"""Amount due on an invoice, under the issuing subsidiary's national VAT rules.

Levels (meta.level):
  1  standard-rated lines only; the rate is printed on each line
  2  mixed categories; rates printed on each line
  3  + line discounts and an earlier part payment; lines show only a VAT category, and the rates come from the
     company handbook excerpt for the issuing country (the model has to look them up)
  4  + a credit note (standard rate) and rounding of the amount due to whole currency units
  5  + intra-EU business customers (EU issuers only): with the customer's VAT number on the invoice no VAT is
     charged (reverse charge); without it, the issuing country's rates apply
About 12 % of tasks are unanswerable (a price is missing, or a category is missing from the handbook); then the
only correct answer is `ANSWER: UNKNOWN`.

Text: one JSON file per language in text/<iso639-3>.json. A language runs in every locale pack of a country that
uses it (eurl.languages); English runs in all packs as the group office language.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from eurl.contract import TypedEnvironment, TypedTask
from eurl.languages import LANGUAGES
from eurl.locales import PACKS
from eurl.locales import load as load_locale
from eurl.money import format_money, round_half_up

TEXT_DIR = Path(__file__).parent / "text"
ITEMS = {  # key: (VAT category, base price range in euro cents)
    "consulting": ("standard", (6000, 18000)),
    "office_supplies": ("standard", (500, 4000)),
    "software": ("standard", (2000, 9000)),
    "coffee": ("food", (1200, 3500)),
    "hotel": ("accommodation", (7000, 16000)),
    "book": ("books", (1500, 6000)),
    "train": ("passenger_transport", (3000, 12000)),
}
CATEGORIES = ("standard", "food", "accommodation", "books", "passenger_transport")
TEXT_KEYS = ("intro", "head_rate", "head_cat", "disc", "discount", "rules", "handbook", "missing_price", "credit",
             "paid", "round", "rc_rule", "buyer_vat", "buyer_novat", "question", "items", "categories", "countries")


@lru_cache(maxsize=None)
def text(lang: str) -> dict:
    data = json.loads((TEXT_DIR / f"{lang}.json").read_text(encoding="utf-8"))
    missing = [k for k in TEXT_KEYS if k not in data]
    if missing:
        raise ValueError(f"{lang}: missing text keys {missing}")
    return data


def languages() -> tuple:
    return tuple(sorted(p.stem for p in TEXT_DIR.glob("*.json")))


def locales_for(lang: str) -> tuple:
    packs = {p.upper() for p in PACKS}
    if lang == "eng":
        return tuple(sorted(packs))
    return tuple(c for c in LANGUAGES[lang].countries if c in packs)


def _company(rng, locale) -> str:
    return f"{rng.choice(locale.company_stems)} {rng.choice(locale.company_suffixes)}"


def _pct(bp: int, decimal: str) -> str:
    return (f"{bp // 100}" if bp % 100 == 0 else f"{bp / 100:g}".replace(".", decimal)) + " %"


def compute_due(lines, vat_bp, credit_net=0, credit_bp=0, paid=0, round_to=0, reverse_charge=False):
    """Ground truth. lines: [(qty, unit_price, discount_pct, category)] in minor units."""
    total = 0
    for qty, price, discount, category in lines:
        gross = qty * price
        net = gross - round_half_up(gross * discount, 100)
        vat = 0 if reverse_charge else round_half_up(net * vat_bp[category], 10000)
        total += net + vat
    credit_vat = 0 if reverse_charge else round_half_up(credit_net * credit_bp, 10000)
    due = total - credit_net - credit_vat - paid
    if round_to > 1:
        due = round_half_up(due, round_to) * round_to
    return due


class FinanceAmountDue(TypedEnvironment):
    id = "finance_amount_due"
    abstention = True

    @property
    def languages(self) -> tuple:
        return tuple(lang for lang in languages() if locales_for(lang))

    def generate(self, rng, language=None) -> TypedTask:
        lang = language or rng.choice(self.languages)
        t = text(lang)
        country = rng.choice(locales_for(lang))
        loc = load_locale(country)
        f = loc.money
        level = rng.choice([1, 2, 3, 4, 5])
        if level == 5 and not loc.eu_member:
            level = 4
        keys = [k for k, (cat, _) in ITEMS.items() if level > 1 or cat == "standard"]
        n_lines = rng.randint(2, len(keys) if level == 1 else 3 + min(level, 3))
        lines = []
        for key in rng.sample(keys, n_lines):
            category, (lo, hi) = ITEMS[key]
            cents = rng.randint(lo, hi) * loc.price_scale + rng.choice([0, 0, 0, 50, 7, 33, 99]) * loc.price_scale
            price = cents if f.minor_digits == 2 else max(1, cents // 100)
            discount = rng.choice([0, 0, 5, 10, 15, 20, 25]) if level >= 3 else 0
            lines.append((rng.randint(1, 12), price, discount, category, t["items"][key]))
        seller = _company(rng, loc)
        reverse_charge, buyer_line = False, ""
        if level == 5:
            eu_others = [c.upper() for c in PACKS if c.upper() != country and load_locale(c).eu_member]
            buyer_country = rng.choice(eu_others)
            bloc = load_locale(buyer_country)
            customer = _company(rng, bloc)
            fields = {"customer": customer, "city": rng.choice(bloc.cities),
                      "buyer_country": t["countries"][buyer_country]}
            if rng.random() < 0.6:
                reverse_charge = True
                buyer_line = t["buyer_vat"].format(vat=bloc.vat_id(rng, bloc.company_id(rng)), **fields)
            else:
                buyer_line = t["buyer_novat"].format(**fields)
        else:
            customer = _company(rng, loc)
            while customer == seller:
                customer = _company(rng, loc)
        unit = 10 ** f.minor_digits
        round_to = unit if level >= 4 else 0
        vat_bp = loc.vat_bp
        credit_net = 0
        if level >= 4:  # a credit note of at most 40 % of the net amount, in whole currency units
            net_total = sum(q * p - round_half_up(q * p * d, 100) for q, p, d, _, _ in lines)
            credit_net = max(1, rng.randint(1, max(1, net_total * 4 // 10 // unit))) * unit
        base = [l[:4] for l in lines]
        before_paid = compute_due(base, vat_bp, credit_net, vat_bp["standard"], 0, 0, reverse_charge)
        paid = round_half_up(before_paid * rng.choice([20, 25, 30, 40, 50]), 100) \
            if level >= 3 and rng.random() < .6 and before_paid > 0 else 0
        due = compute_due(base, vat_bp, credit_net, vat_bp["standard"], paid, round_to, reverse_charge)

        missing = rng.random() < .12
        hidden_line, dropped_category = None, None
        if missing:
            if level >= 3 and rng.random() < .5:
                dropped_category = rng.choice(sorted({l[3] for l in lines}))
            else:
                hidden_line = rng.randrange(len(lines))
        number = f"2025-{rng.randint(1000, 9999)}"
        date = f"2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        rows = []
        for i, (qty, price, discount, category, name) in enumerate(lines):
            shown_price = t["missing_price"] if i == hidden_line else format_money(price, f)
            disc = f", {t['discount'].format(p=discount)}" if discount else ""
            vat_cell = _pct(vat_bp[category], f.decimal) if level <= 2 else t["categories"][category]
            rows.append(f"| {i + 1} | {name} | {qty} | {shown_price} | {vat_cell}{disc} |")
        head = (t["head_rate"] if level <= 2 else t["head_cat"]).format(disc=t["disc"] if level >= 3 else "")
        out = [rng.choice(t["intro"]).format(customer=customer, number=number, seller=seller,
                                             country=t["countries"][country], date=date)]
        if buyer_line:
            out.append(buyer_line)
        out += ["", head, "|---|---|---|---|---|", *rows, ""]
        if level <= 2:
            out.append(t["rules"])
        else:
            shown = [c for c in CATEGORIES if c != dropped_category]
            rng.shuffle(shown)
            rates = "; ".join(f"{t['categories'][c]} {_pct(vat_bp[c], f.decimal)}" for c in shown)
            out.append(t["handbook"].format(country=t["countries"][country], rates=rates))
        if level == 5:
            out.append(t["rc_rule"])
        if credit_net:
            out.append(t["credit"].format(amount=format_money(credit_net, f)))
        if paid:
            out.append(t["paid"].format(amount=format_money(paid, f)))
        if round_to:
            out.append(t["round"].format(unit=f.currency))
        out.append(rng.choice(t["question"]))
        spec = {"type": "abstain"} if missing else {"type": "money", "value": due, "minor_digits": f.minor_digits}
        other = next(c.upper() for c in PACKS if c.upper() != country)
        meta = {"level": level, "unanswerable": missing, "lines": len(lines), "locale": country,
                "reverse_charge": reverse_charge, "currency": f.currency,
                "due_other_treatment": None if missing or level != 5 else compute_due(
                    base, vat_bp, credit_net, vat_bp["standard"], paid, round_to, not reverse_charge),
                "due_without_discounts": None if missing or level < 3 else compute_due(
                    [(q, p, 0, c) for q, p, _, c, _ in lines], vat_bp, credit_net, vat_bp["standard"], paid,
                    round_to, reverse_charge),
                "due_other_country": None if missing or reverse_charge else compute_due(
                    base, load_locale(other).vat_bp, credit_net, load_locale(other).vat_bp["standard"], paid,
                    round_to, False)}
        return TypedTask("\n".join(out), spec, "money", lang, country, meta)

    def extra_probes(self, prompt: str) -> dict:
        m, f = self._task.meta, load_locale(self._task.locale).money
        value = self._task.spec.get("value")
        probes = {}
        for name, key in (("wrong_vat_treatment", "due_other_treatment"), ("ignore_discounts", "due_without_discounts"),
                          ("wrong_country_vat", "due_other_country")):
            if m.get(key) is not None and m[key] != value:
                probes[name] = f"ANSWER: {format_money(m[key], f)}"
        if value is not None:
            probes["off_by_one_unit"] = f"ANSWER: {format_money(value - 10 ** f.minor_digits, f)}"
        return probes


def create():
    return FinanceAmountDue()
