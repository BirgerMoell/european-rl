"""The shared synthetic company group: subsidiaries in several countries, staff, calendars and a mailbox.

Generated from a seed and the locale packs, so tool environments share one consistent world: every person works in
a subsidiary with its country's time zone, office hours, lunch and public holidays. Times are stored in UTC and
shown to the model in each office's local time.
"""
from __future__ import annotations

import datetime as dt
import random
from dataclasses import dataclass, field
from typing import Dict, List
from zoneinfo import ZoneInfo

from eurl.calendar import days_off
from eurl.locales import Locale, load as load_locale

GROUP_STEMS = ("Aurora", "Meridian", "Borealis", "Lumen", "Atlas", "Helix", "Nordia", "Solvia", "Vertex", "Alba")


@dataclass
class Office:
    country: str
    company: str
    city: str
    locale: Locale

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.locale.timezone)


@dataclass
class Person:
    name: str
    email: str
    office: Office
    language: str


@dataclass
class Event:
    id: str
    title: str
    start: dt.datetime        # UTC, timezone-aware
    minutes: int
    attendees: List[str]      # e-mail addresses
    organizer: str


@dataclass
class Mail:
    id: str
    sender: str
    to: List[str]
    subject: str
    body: str
    sent: dt.datetime


@dataclass
class World:
    group: str
    offices: List[Office]
    people: List[Person]
    events: List[Event] = field(default_factory=list)
    inbox: List[Mail] = field(default_factory=list)
    outbox: List[Mail] = field(default_factory=list)

    def person(self, email: str) -> Person:
        return next(p for p in self.people if p.email == email)


def _slug(text: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalnum() or ch == ".")


def make_world(rng: random.Random, countries: List[str], staff_per_office: int = 4) -> World:
    group = rng.choice(GROUP_STEMS)
    domain = f"{_slug(group)}-group.example"
    offices, people, used = [], [], set()
    for country in countries:
        loc = load_locale(country)
        office = Office(country, f"{group} {loc.name} {rng.choice(loc.company_suffixes)}", rng.choice(loc.cities), loc)
        offices.append(office)
        for _ in range(staff_per_office):
            while True:
                first, last = rng.choice(loc.first_names), rng.choice(loc.last_names)
                email = f"{_slug(first)}.{_slug(last)}@{domain}"
                if email not in used:
                    used.add(email)
                    break
            people.append(Person(f"{first} {last}", email, office, loc.language))
    return World(group, offices, people)


def local(d: dt.datetime, office: Office) -> dt.datetime:
    return d.astimezone(office.tz)


def _hm(text: str) -> dt.time:
    h, m = map(int, text.split(":"))
    return dt.time(h, m)


def is_free(world: World, person: Person, start: dt.datetime, minutes: int, ignore_event: str = "") -> bool:
    """Within the person's local office hours, outside lunch, not on a local day off or weekend, no overlap."""
    office = person.office
    loc_start = local(start, office)
    loc_end = local(start + dt.timedelta(minutes=minutes), office)
    if loc_start.date() != loc_end.date() or loc_start.weekday() in office.locale.weekend:
        return False
    if loc_start.date() in days_off(office.locale.holidays, loc_start.year):
        return False
    open_, close = _hm(office.locale.office_hours[0]), _hm(office.locale.office_hours[1])
    if loc_start.time() < open_ or loc_end.time() > close or (loc_end.time() == dt.time(0) and close != dt.time(0)):
        return False
    lunch_a, lunch_b = _hm(office.locale.lunch[0]), _hm(office.locale.lunch[1])
    if loc_start.time() < lunch_b and loc_end.time() > lunch_a:
        return False
    end = start + dt.timedelta(minutes=minutes)
    for e in world.events:
        if e.id == ignore_event or person.email not in e.attendees:
            continue
        e_end = e.start + dt.timedelta(minutes=e.minutes)
        if start < e_end and e.start < end:
            return False
    return True


def first_common_slot(world: World, people: List[Person], first_day: dt.date, days: int, minutes: int,
                      step: int = 30, ignore_event: str = "") -> dt.datetime | None:
    """Earliest UTC start on a `step`-minute grid (UTC, aligned to the hour) where everyone is free."""
    t = dt.datetime.combine(first_day, dt.time(0), tzinfo=dt.timezone.utc) - dt.timedelta(hours=3)
    end = dt.datetime.combine(first_day + dt.timedelta(days=days), dt.time(0), tzinfo=dt.timezone.utc)
    while t < end:
        if all(is_free(world, p, t, minutes, ignore_event) for p in people):
            return t
        t += dt.timedelta(minutes=step)
    return None
