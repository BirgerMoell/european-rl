"""Public holidays and working days per country, from declarative rules.

A locale pack lists its rules; this module evaluates them for a year. Rule kinds:
- fixed(month, day)                 the same date every year
- easter(offset)                    Western (Gregorian) Easter Sunday + offset days
- orthodox(offset)                  Orthodox Easter Sunday (Julian computus, Gregorian date) + offset days
- weekday_from(weekday, month, first_day)   the first such weekday in the 7 days from a date, e.g. Swedish
  Midsummer Day (the Saturday 20–26 June) or All Saints' Day (the Saturday 31 October–6 November)
- each rule has `public` (a statutory public holiday) or not (a customary non-working day such as Christmas Eve
  in Sweden, which companies treat as a day off); and an optional `since` year.

Tests compare the public rules with the `holidays` package for several years.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Dict, Iterable, Optional


def easter(year: int) -> dt.date:
    """Gregorian Easter Sunday (anonymous Gregorian algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = (h + l_ - 7 * m + 114) % 31 + 1
    return dt.date(year, month, day)


def orthodox_easter(year: int) -> dt.date:
    """Orthodox Easter Sunday as a Gregorian date (Meeus' Julian algorithm + 13 days, valid 1900–2099)."""
    a, b, c = year % 4, year % 7, year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month = (d + e + 114) // 31
    day = (d + e + 114) % 31 + 1
    return dt.date(year, month, day) + dt.timedelta(days=13)


@dataclass(frozen=True)
class Rule:
    kind: str                       # fixed | easter | orthodox | weekday_from
    names: Dict[str, str]           # language code (ISO 639-3) -> local name
    month: int = 0
    day: int = 0
    offset: int = 0
    weekday: int = 0                # Monday = 0
    public: bool = True
    since: Optional[int] = None
    until: Optional[int] = None

    def date(self, year: int) -> Optional[dt.date]:
        if (self.since and year < self.since) or (self.until and year > self.until):
            return None
        if self.kind == "fixed":
            return dt.date(year, self.month, self.day)
        if self.kind == "easter":
            return easter(year) + dt.timedelta(days=self.offset)
        if self.kind == "orthodox":
            return orthodox_easter(year) + dt.timedelta(days=self.offset)
        if self.kind == "weekday_from":
            start = dt.date(year, self.month, self.day)
            return start + dt.timedelta(days=(self.weekday - start.weekday()) % 7)
        raise ValueError(self.kind)


def fixed(month: int, day: int, names: Dict[str, str], **kw) -> Rule:
    return Rule("fixed", names, month=month, day=day, **kw)


def easter_rule(offset: int, names: Dict[str, str], **kw) -> Rule:
    return Rule("easter", names, offset=offset, **kw)


def orthodox_rule(offset: int, names: Dict[str, str], **kw) -> Rule:
    return Rule("orthodox", names, offset=offset, **kw)


def weekday_from(weekday: int, month: int, first_day: int, names: Dict[str, str], **kw) -> Rule:
    """The first `weekday` (Monday = 0) on or after month/first_day."""
    return Rule("weekday_from", names, month=month, day=first_day, weekday=weekday, **kw)


def days_off(rules: Iterable[Rule], year: int, public_only: bool = False) -> Dict[dt.date, Rule]:
    out: Dict[dt.date, Rule] = {}
    for rule in rules:
        if public_only and not rule.public:
            continue
        d = rule.date(year)
        if d is not None:
            out.setdefault(d, rule)
    return out


def is_working_day(rules: Iterable[Rule], d: dt.date, weekend: tuple = (5, 6)) -> bool:
    return d.weekday() not in weekend and d not in days_off(rules, d.year)


def add_working_days(rules, d: dt.date, n: int, weekend: tuple = (5, 6)) -> dt.date:
    rules = list(rules)
    step = 1 if n >= 0 else -1
    remaining = abs(n)
    while remaining:
        d += dt.timedelta(days=step)
        if is_working_day(rules, d, weekend):
            remaining -= 1
    return d
