"""Money in minor units (cents, öre, grosze) with locale formatting and tolerant parsing.

Formatting follows each locale pack's conventions ("1 234,50 kr", "1.234,50 €", "1 234,50 zł"). Parsing accepts
any common European rendering of ONE amount, with or without currency, because the checked skill is the amount,
not the typography. A separator followed by exactly three digits is a thousands separator; decimals have at most
two digits, so 1,117.67 and 1.117,67 both read as 1117.67. A text with several amounts does not parse (listing candidates never pays).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

NBSP, NNBSP = " ", " "


@dataclass(frozen=True)
class MoneyFormat:
    currency: str          # ISO 4217
    symbol: str            # as written after/before the amount
    decimal: str = ","
    group: str = NBSP
    symbol_first: bool = False
    minor_digits: int = 2


def format_money(minor: int, f: MoneyFormat, with_symbol: bool = True) -> str:
    sign = "-" if minor < 0 else ""
    major, rest = divmod(abs(minor), 10 ** f.minor_digits)
    groups = f"{major:,}".replace(",", f.group)
    text = groups + (f"{f.decimal}{rest:0{f.minor_digits}d}" if f.minor_digits else "")
    if not with_symbol:
        return sign + text
    return f"{sign}{f.symbol}{text}" if f.symbol_first else f"{sign}{text} {f.symbol}"


# Currency words and symbols removed before parsing (any locale: the model may answer in another convention).
_CURRENCY = re.compile(
    r"(?i)(€|\beur(?:o|os)?\b|\bsek\b|\bkr\b|\bkronor\b|\bkroner\b|\bkrónur\b|\bnok\b|\bdkk\b|\bisk\b|zł|\bpln\b"
    r"|\bczk\b|kč|\bhuf\b|\bft\b|\bron\b|\blei\b|\bbgn\b|лв\.?|\bchf\b|\bgbp\b|£|\btry\b|₺|\buah\b|₴|грн\.?"
    r"|\bgel\b|₾|\brsd\b|дин\.?|\bdin\b|\bmkd\b|ден\.?|\ball\b|\blek[eë]?\b|\bbam\b|\bkm\b|:-)")
_AMOUNT = re.compile(r"-?\d{1,3}(?:[   .,'’]\d{3})+(?:[,.]\d{1,2})?|-?\d+(?:[,.]\d{1,2})?")


def parse_money(text: Optional[str], minor_digits: int = 2) -> Optional[int]:
    if text is None:
        return None
    cleaned = _CURRENCY.sub(" ", text).replace("−", "-").strip()
    found = _AMOUNT.findall(cleaned)
    if len(found) != 1:
        return None
    token = found[0]
    negative = token.startswith("-")
    token = token.lstrip("-")
    m = re.fullmatch(r"(\d{1,3}(?:[   .,'’]\d{3})+|\d+)(?:[,.](\d{1,2}))?", token)
    if not m:
        return None
    whole = re.sub(r"[   .,'’]", "", m.group(1))
    frac = (m.group(2) or "0").ljust(minor_digits, "0")[:minor_digits] if minor_digits else ""
    value = int(whole) * 10 ** minor_digits + (int(frac) if frac else 0)
    return -value if negative else value


def round_half_up(numerator: int, denominator: int) -> int:
    """Integer division rounding halves away from zero (commercial rounding)."""
    sign = -1 if (numerator < 0) ^ (denominator < 0) else 1
    n, d = abs(numerator), abs(denominator)
    return sign * ((2 * n + d) // (2 * d))
