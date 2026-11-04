"""A tools-only agent for meeting_reschedule that records its conversation, for warm-start SFT data.

The baselines showed our 9B checkpoints cannot yet run this multi-step task (they guess dates instead of reading the
request and repeat failing calls), so RL has no signal. Like the synthetic agent trajectories of Kimi K2 and
DeepSeek-V3.2, this agent solves tasks through the public tools only, batching independent calls in one turn, and
every recorded trajectory is kept only if the environment rewards it 1.0.

Each trajectory is a chat in the OpenAI / Hermes format our template v2.1 renders: the user turn (instruction), then
assistant turns with `tool_calls`, `tool` messages with the JSON results, and a final assistant message.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from zoneinfo import ZoneInfo

from environments.meeting_reschedule.environment import text


def _hm(x: str) -> dt.time:
    return dt.time(*map(int, x.split(":")))


class Recorder:
    def __init__(self, env):
        self.env = env
        self.messages = [{"role": "user", "content": env.public_prompt()}]

    def turn(self, calls: list) -> list:
        """One assistant turn with several tool calls; returns the results in order."""
        self.messages.append({"role": "assistant", "content": "",
                              "tool_calls": [{"type": "function", "function": {"name": n, "arguments": a}}
                                             for n, a in calls]})
        results = []
        for name, args in calls:
            out = self.env.step({"tool": name, "arguments": args})
            obs = out["observation"]
            self.messages.append({"role": "tool", "content": json.dumps(obs, ensure_ascii=False)})
            if "result" not in obs:
                raise RuntimeError(f"tool error in a reference trajectory: {obs}")
            results.append(obs["result"])
        return results

    def finish(self, final: str) -> dict:
        self.messages.append({"role": "assistant", "content": final})
        return self.env.step({"final": final})


def solve(env) -> tuple:
    """Run one episode through the tools; returns (messages, step result)."""
    rec = Recorder(env)
    lang = env._task.language
    t = text(lang)
    [inbox] = rec.turn([("list_inbox", {})])
    [mail] = rec.turn([("read_email", {"id": inbox[0]["id"]})])
    requester, organizer = mail["from"], mail["to"][0]
    original, monday, friday = re.findall(r"\d{4}-\d{2}-\d{2}", mail["body"])[:3]
    [org_events] = rec.turn([("list_events", {"email": organizer, "from_date": original, "to_date": original})])
    meeting = next(e for e in org_events if e["id"] == "evt-1")
    emails = meeting["attendees"]
    people = {e: p[0] for e, p in zip(emails, rec.turn([("find_person", {"name": e}) for e in emails]))}
    countries = sorted({p["country"] for p in people.values()})
    batch = [("get_office", {"country": c}) for c in countries] + \
            [("list_days_off", {"country": c, "from_date": monday, "to_date": friday}) for c in countries]
    out = rec.turn(batch)
    offices = dict(zip(countries, out[:len(countries)]))
    off = {c: {d["date"] for d in days} for c, days in zip(countries, out[len(countries):])}
    calendars = rec.turn([("list_events", {"email": e, "from_date": monday, "to_date": friday}) for e in emails])
    a0 = dt.datetime.strptime(meeting["start"], "%Y-%m-%d %H:%M")
    a1 = dt.datetime.strptime(meeting["end"], "%Y-%m-%d %H:%M")
    minutes = int((a1 - a0).total_seconds() // 60)
    state = {}
    for e, events in zip(emails, calendars):
        tz = ZoneInfo(people[e]["timezone"])
        busy = [(dt.datetime.strptime(x["start"], "%Y-%m-%d %H:%M").replace(tzinfo=tz),
                 dt.datetime.strptime(x["end"], "%Y-%m-%d %H:%M").replace(tzinfo=tz)) for x in events if x["id"] != "evt-1"]
        office = offices[people[e]["country"]]
        state[e] = {"tz": tz, "hours": office["office_hours"].split("–"), "lunch": office["lunch"].split("–"),
                    "off": off[people[e]["country"]], "busy": busy}
    # events that start before the week but run into it (e.g. a trip that began on Sunday) are listed from Monday on
    # only if they start in range; the generator never starts blocking events before the week, so this is complete

    def free(p, start):
        s, end = start.astimezone(p["tz"]), (start + dt.timedelta(minutes=minutes)).astimezone(p["tz"])
        if s.date() != end.date() or s.weekday() >= 5 or s.date().isoformat() in p["off"]:
            return False
        if s.time() < _hm(p["hours"][0]) or end.time() > _hm(p["hours"][1]):
            return False
        if s.time() < _hm(p["lunch"][1]) and end.time() > _hm(p["lunch"][0]):
            return False
        return not any(s < b and a < end for a, b in p["busy"])

    slot, cur = None, dt.datetime.fromisoformat(monday).replace(tzinfo=dt.timezone.utc) - dt.timedelta(hours=3)
    stop = dt.datetime.fromisoformat(friday).replace(tzinfo=dt.timezone.utc) + dt.timedelta(days=1)
    while cur < stop:
        if all(free(p, cur) for p in state.values()):
            slot = cur
            break
        cur += dt.timedelta(minutes=30)
    title = meeting["title"]
    if slot is None:
        rec.turn([("send_email", {"to": [requester], "subject": t["request_subject"].format(title=title),
                                  "body": t["no_slot_reply"].format(title=title)})])
        return rec.messages, rec.finish(t["done"])
    org = state[organizer]
    lo = slot.astimezone(org["tz"])
    rec.turn([("move_event", {"event_id": "evt-1", "date": f"{lo:%Y-%m-%d}", "time": f"{lo:%H:%M}",
                              "timezone": str(org["tz"])})])
    notices = []
    for e in emails:
        if e == organizer:
            continue
        x = slot.astimezone(state[e]["tz"])
        notices.append(("send_email", {"to": [e], "subject": t["notice_subject"].format(title=title),
                                       "body": t["notice"].format(title=title, date=f"{x:%Y-%m-%d}",
                                                                  time=f"{x:%H:%M}", tz=str(state[e]["tz"]))}))
    rec.turn(notices)
    return rec.messages, rec.finish(t["done"])
