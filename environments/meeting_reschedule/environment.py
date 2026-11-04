"""Reschedule a meeting across offices in different countries, then tell every participant the new time in their
own local time.

The model is the assistant of the meeting organiser. A participant e-mails (in their own language) that they cannot
attend; the meeting must move to the earliest slot in the given week when every participant is free:
- inside their own office hours and outside lunch, both in their own local time;
- not on a weekend or a day off in their own country;
- not overlapping their other meetings.
Then every participant except the organiser gets an e-mail stating the new date and time in their own time zone. If
no slot exists, the meeting stays and the requester gets a reply.

Levels (meta.level): 1 one office; 2 two countries; 3 three countries, the week often contains a day off somewhere
and calendars are busier.

Scoring is on the end state, all or nothing:
- the event (same id, same attendees and length) starts at the expected UTC time, or is unchanged when no slot exists;
- each recipient is on exactly one sent mail containing their local date (YYYY-MM-DD) and time (HH:MM);
- nobody else gets mail, and no other event changes.
"""
from __future__ import annotations

import datetime as dt
import json
from functools import lru_cache
from pathlib import Path

from eurl.calendar import days_off
from eurl.contract import Tool, ToolEnvironment, ToolError, ToolTask
from eurl.locales import PACKS
from eurl.world import Event, Mail, first_common_slot, local, make_world

TEXT_DIR = Path(__file__).parent / "text"


@lru_cache(maxsize=None)
def text(lang: str) -> dict:
    return json.loads((TEXT_DIR / f"{lang}.json").read_text(encoding="utf-8"))


def languages() -> tuple:
    return tuple(sorted(p.stem for p in TEXT_DIR.glob("*.json")))


def _countries_with_text() -> list:
    from eurl.locales import load
    langs = set(languages())
    return [c.upper() for c in PACKS if set(load(c).languages) & langs]


def _fmt(d: dt.datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M")


def _tools(lang: str) -> list:
    def list_inbox(state):
        return [{"id": m.id, "from": m.sender, "subject": m.subject} for m in state.inbox]

    def read_email(state, id):
        for m in state.inbox:
            if m.id == id:
                return {"id": m.id, "from": m.sender, "to": m.to, "subject": m.subject, "body": m.body}
        raise ToolError(f"no e-mail with id {id}")

    def find_person(state, name):
        q = name.strip().casefold()
        hits = [p for p in state.people if q in p.name.casefold() or q == p.email.casefold()]
        if not hits:
            raise ToolError(f"nobody matches {name!r}")
        return [{"name": p.name, "email": p.email, "company": p.office.company, "country": p.office.country,
                 "city": p.office.city, "timezone": p.office.locale.timezone} for p in hits]

    def get_office(state, country):
        office = next((o for o in state.offices if o.country == country.upper()), None)
        if office is None:
            raise ToolError(f"no office in {country}")
        return {"company": office.company, "country": office.country, "timezone": office.locale.timezone,
                "office_hours": "–".join(office.locale.office_hours), "lunch": "–".join(office.locale.lunch),
                "weekend": ["Saturday", "Sunday"]}

    def list_days_off(state, country, from_date, to_date):
        office = next((o for o in state.offices if o.country == country.upper()), None)
        if office is None:
            raise ToolError(f"no office in {country}")
        try:
            a, b = dt.date.fromisoformat(from_date), dt.date.fromisoformat(to_date)
        except ValueError as error:
            raise ToolError(f"dates must be YYYY-MM-DD: {error}")
        out = []
        for year in range(a.year, b.year + 1):
            for d, rule in sorted(days_off(office.locale.holidays, year).items()):
                if a <= d <= b:
                    out.append({"date": d.isoformat(), "name": rule.names.get(office.locale.language, ""),
                                "statutory": rule.public})
        return out

    def list_events(state, email, from_date, to_date):
        person = next((p for p in state.people if p.email == email), None)
        if person is None:
            raise ToolError(f"unknown person {email}")
        try:
            a, b = dt.date.fromisoformat(from_date), dt.date.fromisoformat(to_date)
        except ValueError as error:
            raise ToolError(f"dates must be YYYY-MM-DD: {error}")
        out = []
        for e in sorted(state.events, key=lambda e: e.start):
            start = local(e.start, person.office)
            if email in e.attendees and a <= start.date() <= b:
                end = local(e.start + dt.timedelta(minutes=e.minutes), person.office)
                out.append({"id": e.id, "title": e.title, "start": _fmt(start), "end": _fmt(end),
                            "timezone": person.office.locale.timezone, "attendees": e.attendees})
        return out

    def move_event(state, event_id, date, time, timezone):
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        e = next((e for e in state.events if e.id == event_id), None)
        if e is None:
            raise ToolError(f"no event {event_id}")
        try:
            start = dt.datetime.combine(dt.date.fromisoformat(date), dt.time.fromisoformat(time),
                                        tzinfo=ZoneInfo(timezone))
        except (ValueError, ZoneInfoNotFoundError) as error:
            raise ToolError(f"invalid date, time or timezone: {error}")
        e.start = start.astimezone(dt.timezone.utc)
        return {"id": e.id, "start_utc": _fmt(e.start)}

    def send_email(state, to, subject, body):
        if not to or not all(isinstance(x, str) for x in to):
            raise ToolError("`to` must be a non-empty list of e-mail addresses")
        unknown = [x for x in to if x not in {p.email for p in state.people}]
        if unknown:
            raise ToolError(f"unknown recipients: {unknown}")
        mail = Mail(f"out-{len(state.outbox) + 1}", "assistant", list(to), subject, body,
                    dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc))
        state.outbox.append(mail)
        return {"id": mail.id, "sent": True}

    s = {"type": "string"}
    return [
        Tool("list_inbox", "List the e-mails in the organiser's inbox.", {"type": "object", "properties": {}, "required": []}, list_inbox),
        Tool("read_email", "Read one e-mail.", {"type": "object", "properties": {"id": s}, "required": ["id"]}, read_email),
        Tool("find_person", "Look up colleagues by name or e-mail: e-mail, office country, city and time zone.",
             {"type": "object", "properties": {"name": s}, "required": ["name"]}, find_person),
        Tool("get_office", "Office hours, lunch break and time zone of the group's office in a country (ISO code, e.g. FI).",
             {"type": "object", "properties": {"country": s}, "required": ["country"]}, get_office),
        Tool("list_days_off", "Public holidays and customary days off of an office's country between two dates (YYYY-MM-DD).",
             {"type": "object", "properties": {"country": s, "from_date": s, "to_date": s},
              "required": ["country", "from_date", "to_date"]}, list_days_off),
        Tool("list_events", "A person's calendar between two dates (YYYY-MM-DD), shown in that person's local time.",
             {"type": "object", "properties": {"email": s, "from_date": s, "to_date": s},
              "required": ["email", "from_date", "to_date"]}, list_events),
        Tool("move_event", "Move an event to a new start: local date (YYYY-MM-DD), time (HH:MM) and IANA time zone.",
             {"type": "object", "properties": {"event_id": s, "date": s, "time": s, "timezone": s},
              "required": ["event_id", "date", "time", "timezone"]}, move_event, mutates=True),
        Tool("send_email", "Send an e-mail from the organiser.",
             {"type": "object", "properties": {"to": {"type": "array"}, "subject": s, "body": s},
              "required": ["to", "subject", "body"]}, send_email, mutates=True),
    ]


class MeetingReschedule(ToolEnvironment):
    id = "meeting_reschedule"

    @property
    def languages(self) -> tuple:
        from eurl.locales import load
        have = set(languages())
        langs = {lang for c in _countries_with_text() for lang in load(c).languages if lang in have}
        return tuple(sorted(langs | ({"eng"} if "eng" in have else set())))

    def generate(self, rng, language=None) -> ToolTask:
        from eurl.locales import load as load_locale
        countries = _countries_with_text()
        level = rng.choice([1, 2, 3])
        lang = language or rng.choice(self.languages)
        # English is the group office language: an English instruction may come from any office
        home = rng.choice(countries if lang == "eng" else [c for c in countries if lang in load_locale(c).languages])
        others = [c for c in countries if c != home]
        chosen = [home] + rng.sample(others, min(level - 1, len(others)))
        # from level 2, usually include an office in another UTC offset (the time-zone skill)
        def offset(c):
            from zoneinfo import ZoneInfo
            return dt.datetime(2026, 1, 15, 12, tzinfo=ZoneInfo(load_locale(c).timezone)).utcoffset()
        shifted = [c for c in others if offset(c) != offset(home)]
        if level >= 2 and shifted and all(offset(c) == offset(home) for c in chosen) and rng.random() < 0.8:
            chosen[-1] = rng.choice(shifted)
        world = make_world(rng, chosen, staff_per_office=3)
        have = set(languages())
        for p in world.people:  # people speak one of their country's languages (Catalan, Basque, Swedish in FI, …)
            spoken = [x for x in p.office.locale.languages if x in have]
            if spoken:
                p.language = rng.choice(spoken)
        if lang != "eng":
            world.people[0].language = lang   # the organiser reads the instruction in their own language
        t = text(lang)
        organizer = world.people[0]
        pool = [p for p in world.people[1:]]
        attendees = [organizer] + rng.sample(pool, min(len(pool), rng.randint(2, 2 + level)))
        # the target week: often one with a day off in a participant's country
        mondays = [dt.date(2026, 1, 5) + dt.timedelta(weeks=w) for w in range(48)]
        if level == 3 and rng.random() < 0.7:
            holiday_weeks = [m for m in mondays if any(
                m <= d < m + dt.timedelta(days=5) for p in attendees
                for d in days_off(p.office.locale.holidays, m.year))]
            week = rng.choice(holiday_weeks or mondays)
        else:
            week = rng.choice(mondays)
        minutes = rng.choice([30, 60, 60, 90])
        title = rng.choice(t["titles"])
        # original slot: the week before, in the organiser's office hours
        orig = dt.datetime.combine(week - dt.timedelta(days=7 - rng.randint(0, 4)), dt.time(rng.choice([9, 10, 13, 14])),
                                   tzinfo=organizer.office.tz).astimezone(dt.timezone.utc)
        emails = [p.email for p in attendees]
        world.events.append(Event("evt-1", title, orig, minutes, emails, organizer.email))
        # busy calendars in the target week
        n_busy = rng.randint(3 * level, 6 + 4 * level)
        for i in range(n_busy):
            p = rng.choice(attendees)
            day = week + dt.timedelta(days=rng.randint(0, 4))
            start = dt.datetime.combine(day, dt.time(rng.randint(8, 16), rng.choice([0, 30])), tzinfo=p.office.tz)
            world.events.append(Event(f"evt-{i + 2}", rng.choice(t["busy_titles"]), start.astimezone(dt.timezone.utc),
                                      rng.choice([30, 60, 90, 120]), [p.email], p.email))
        # the requester is away at the start of the week (travel, a course): the slot is rarely Monday morning
        requester = rng.choice(attendees[1:])
        away_hours = rng.choice([0, 4, 10, 24, 28, 34, 48])
        if away_hours:
            start = dt.datetime.combine(week, dt.time(0), tzinfo=requester.office.tz)
            world.events.append(Event("evt-away", rng.choice(t["busy_titles"]), start.astimezone(dt.timezone.utc),
                                      away_hours * 60 + (14 * 60 if away_hours % 24 else 0), [requester.email],
                                      requester.email))
        # sometimes make the week impossible: one attendee is fully booked
        impossible = rng.random() < 0.1
        if impossible:
            p = rng.choice(attendees[1:])
            for d in range(5):
                start = dt.datetime.combine(week + dt.timedelta(days=d), dt.time(6), tzinfo=p.office.tz)
                world.events.append(Event(f"evt-block-{d}", t["busy_titles"][0], start.astimezone(dt.timezone.utc),
                                          14 * 60, [p.email], p.email))
        target = first_common_slot(world, attendees, week, 5, minutes, ignore_event="evt-1")
        rlang = requester.language if requester.language in languages() else lang
        rt = text(rlang)
        orig_local = local(orig, requester.office)
        body = rng.choice(rt["request"]).format(
            title=title, original=f"{_fmt(orig_local)} ({requester.office.locale.timezone})",
            monday=week.isoformat(), friday=(week + dt.timedelta(days=4)).isoformat(),
            organizer=organizer.name.split()[0], name=requester.name)
        world.inbox.append(Mail("mail-1", requester.email, [organizer.email], rt["request_subject"].format(title=title),
                                body, orig - dt.timedelta(days=2)))
        instruction = rng.choice(t["instruction"]).format(organizer=organizer.name, company=organizer.office.company)
        recipients = [p for p in attendees if p is not organizer]

        def check(state, final):
            evt = next(e for e in state.events if e.id == "evt-1")
            others_ok = all(_same(e, o) for e, o in zip(sorted(state.events, key=lambda e: e.id)[1:],
                                                          sorted(world.events, key=lambda e: e.id)[1:]))
            unchanged_meta = evt.minutes == minutes and evt.attendees == emails and len(state.events) == len(world.events)
            allowed = {p.email for p in recipients}
            stray = [x for m in state.outbox for x in m.to if x not in allowed]
            if target is None:
                moved = evt.start != orig
                replies = [m for m in state.outbox if m.to == [requester.email] or set(m.to) == {requester.email}]
                ok = not moved and unchanged_meta and others_ok and len(state.outbox) == 1 and len(replies) == 1
                return {"reward": float(ok), "score": float(ok), "case": "no_slot", "moved": moved,
                        "mails": len(state.outbox)}
            per = {}
            for p in recipients:
                mails = [m for m in state.outbox if p.email in m.to]
                loc = local(target, p.office)
                per[p.email] = len(mails) == 1 and loc.strftime("%Y-%m-%d") in mails[0].body and \
                    loc.strftime("%H:%M") in mails[0].body
            moved_ok = evt.start == target
            ok = moved_ok and unchanged_meta and others_ok and not stray and all(per.values())
            score = (moved_ok + sum(per.values()) / len(per)) / 2 if not stray and others_ok else 0.0
            return {"reward": float(ok), "score": score, "case": "slot", "moved_ok": moved_ok,
                    "notified": sum(per.values()), "recipients": len(per), "stray": stray}

        week_end = (week + dt.timedelta(days=4)).isoformat()
        reference = [{"tool": "list_inbox", "arguments": {}}, {"tool": "read_email", "arguments": {"id": "mail-1"}}]
        for p in attendees:
            reference.append({"tool": "list_events", "arguments": {"email": p.email, "from_date": week.isoformat(),
                                                                   "to_date": week_end}})
        if target is None:
            reference.append({"tool": "send_email", "arguments": {
                "to": [requester.email], "subject": rt["request_subject"].format(title=title),
                "body": rt["no_slot_reply"].format(title=title)}})
        else:
            org_local = local(target, organizer.office)
            reference.append({"tool": "move_event", "arguments": {
                "event_id": "evt-1", "date": org_local.strftime("%Y-%m-%d"), "time": org_local.strftime("%H:%M"),
                "timezone": organizer.office.locale.timezone}})
            for p in recipients:
                loc = local(target, p.office)
                pt = text(p.language) if p.language in languages() else t
                reference.append({"tool": "send_email", "arguments": {
                    "to": [p.email], "subject": pt["notice_subject"].format(title=title),
                    "body": pt["notice"].format(title=title, date=loc.strftime("%Y-%m-%d"), time=loc.strftime("%H:%M"),
                                                tz=p.office.locale.timezone)}})
        reference.append({"final": t["done"]})
        meta = {"level": level, "countries": chosen, "attendees": len(attendees), "week": week.isoformat(),
                "no_slot": target is None, "target_utc": target and _fmt(target), "request_language": rlang}
        return ToolTask(instruction, world, _tools(lang), check, reference, lang, home,
                        max_steps=10 + 6 * len(attendees), meta=meta)  # ~5 lookups per participant + overhead


def _plan(env, slot, when_for) -> list:
    """Move evt-1 to `slot` (UTC) and notify every participant with the time `when_for(person)` gives."""
    world = env._task.state
    evt = next(e for e in world.events if e.id == "evt-1")
    organizer = world.person(evt.organizer)
    org_local = local(slot, organizer.office)
    actions = [{"tool": "move_event", "arguments": {"event_id": "evt-1", "date": org_local.strftime("%Y-%m-%d"),
                                                    "time": org_local.strftime("%H:%M"),
                                                    "timezone": organizer.office.locale.timezone}}]
    for email in evt.attendees:
        if email == organizer.email:
            continue
        shown = when_for(world.person(email))
        actions.append({"tool": "send_email", "arguments": {"to": [email], "subject": evt.title,
                                                            "body": f"New time: {shown:%Y-%m-%d %H:%M}"}})
    return actions + [{"final": "done"}]


def _probe_context(env):
    world = env._task.state
    evt = next(e for e in world.events if e.id == "evt-1")
    people = [world.person(e) for e in evt.attendees]
    week = dt.date.fromisoformat(env._task.meta["week"])
    return world, evt, people, week


def _organizer_only(env):
    world, evt, people, week = _probe_context(env)
    slot = first_common_slot(world, [world.person(evt.organizer)], week, 5, evt.minutes, ignore_event="evt-1")
    target = env._task.meta["target_utc"]
    if slot is None or (target and _fmt(slot) == target):
        return None
    return _plan(env, slot, lambda p: local(slot, p.office))


def _organizer_timezone(env):
    world, evt, people, _ = _probe_context(env)
    target = env._task.meta["target_utc"]
    if target is None:
        return None
    slot = dt.datetime.strptime(target, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
    organizer = world.person(evt.organizer)
    if len({local(slot, p.office).utcoffset() for p in people}) == 1:
        return None  # everyone shares the organiser's offset: the shortcut is the right answer
    return _plan(env, slot, lambda p: local(slot, organizer.office))


def _ignore_days_off(env):
    world, evt, people, week = _probe_context(env)
    saved = [(p.office, p.office.locale) for p in people]
    import dataclasses
    for office in {id(p.office): p.office for p in people}.values():
        office.locale = dataclasses.replace(office.locale, holidays=())
    slot = first_common_slot(world, people, week, 5, evt.minutes, ignore_event="evt-1")
    for office, locale in saved:
        office.locale = locale
    target = env._task.meta["target_utc"]
    if slot is None or (target and _fmt(slot) == target):
        return None
    return _plan(env, slot, lambda p: local(slot, p.office))


def _same(a: Event, b: Event) -> bool:
    return (a.id, a.start, a.minutes, a.attendees) == (b.id, b.start, b.minutes, b.attendees)


MeetingReschedule.extra_probe_plans = lambda self: {"organizer_only_slot": _organizer_only,
                                                    "organizer_timezone_notice": _organizer_timezone,
                                                    "ignore_days_off": _ignore_days_off}


def create():
    return MeetingReschedule()
