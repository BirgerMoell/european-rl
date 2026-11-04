"""meeting_reschedule: an independent solver that sees only the request e-mail and tool outputs (no simulator access)
must solve every task (DeepSeek's rule: the solution goes through the tool interface), in every language; then the
contract qualification."""
import datetime as dt
import re
from zoneinfo import ZoneInfo

import pytest

from environments.meeting_reschedule.environment import MeetingReschedule
from eurl.validation import validate_tools


def call(env, tool, **args):
    out = env.step({"tool": tool, "arguments": args})
    assert "result" in out["observation"], out["observation"]
    return out["observation"]["result"]


def solve(env):
    mail_id = call(env, "list_inbox")[0]["id"]
    mail = call(env, "read_email", id=mail_id)
    requester, organizer = mail["from"], mail["to"][0]
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", mail["body"])
    original, monday, friday = dates[0], dates[1], dates[2]
    evt = next(e for e in call(env, "list_events", email=organizer, from_date=original, to_date=original)
               if e["id"] == "evt-1")
    people = {}
    for email in evt["attendees"]:
        info = call(env, "find_person", name=email)[0]
        office = call(env, "get_office", country=info["country"])
        off = {d["date"] for d in call(env, "list_days_off", country=info["country"], from_date=monday, to_date=friday)}
        busy = []
        for e in call(env, "list_events", email=email, from_date=(dt.date.fromisoformat(monday) - dt.timedelta(days=1)).isoformat(),
                      to_date=friday):
            if e["id"] == "evt-1":
                continue
            tz = ZoneInfo(e["timezone"])
            a = dt.datetime.strptime(e["start"], "%Y-%m-%d %H:%M").replace(tzinfo=tz)
            b = dt.datetime.strptime(e["end"], "%Y-%m-%d %H:%M").replace(tzinfo=tz)
            busy.append((a, b))
        people[email] = {"tz": ZoneInfo(info["timezone"]), "hours": office["office_hours"].split("–"),
                         "lunch": office["lunch"].split("–"), "off": off, "busy": busy}
    a0, a1 = dt.datetime.strptime(evt["start"], "%Y-%m-%d %H:%M"), dt.datetime.strptime(evt["end"], "%Y-%m-%d %H:%M")
    minutes = int((a1 - a0).total_seconds() // 60)

    def free(p, start):
        s, e = start.astimezone(p["tz"]), (start + dt.timedelta(minutes=minutes)).astimezone(p["tz"])
        if s.date() != e.date() or s.weekday() >= 5 or s.date().isoformat() in p["off"]:
            return False
        hm = lambda x: dt.time(*map(int, x.split(":")))
        if s.time() < hm(p["hours"][0]) or e.time() > hm(p["hours"][1]):
            return False
        if s.time() < hm(p["lunch"][1]) and e.time() > hm(p["lunch"][0]):
            return False
        return not any(s < b and a < e for a, b in p["busy"])

    t = dt.datetime.fromisoformat(monday).replace(tzinfo=dt.timezone.utc) - dt.timedelta(hours=3)
    end = dt.datetime.fromisoformat(friday).replace(tzinfo=dt.timezone.utc) + dt.timedelta(days=1)
    slot = None
    while t < end:
        if all(free(p, t) for p in people.values()):
            slot = t
            break
        t += dt.timedelta(minutes=30)
    if slot is None:
        env.step({"tool": "send_email", "arguments": {"to": [requester], "subject": "Re", "body": "No time works."}})
        return env.step({"final": "ok"})
    org = people[organizer]
    lo = slot.astimezone(org["tz"])
    call(env, "move_event", event_id="evt-1", date=f"{lo:%Y-%m-%d}", time=f"{lo:%H:%M}", timezone=str(org["tz"]))
    for email, p in people.items():
        if email != organizer:
            x = slot.astimezone(p["tz"])
            call(env, "send_email", to=[email], subject="New time", body=f"{x:%Y-%m-%d} {x:%H:%M}")
    return env.step({"final": "ok"})


@pytest.mark.parametrize("language", MeetingReschedule().languages)
def test_independent_solver_through_tools(language):
    env = MeetingReschedule()
    for seed in range(40):
        env.reset(seed, "dev", language)
        env._task.max_steps = 200  # the solver is not step-efficient
        result = solve(env)
        assert result["reward"] == 1.0, (language, seed, env._task.meta, result["info"])


def test_contract_qualification():
    report = validate_tools("meeting_reschedule", cases=20)
    assert report["status"] == "passed"
    assert max(report["probe_mean_reward"].values()) <= 0.3


def test_solver_trajectories_are_rewarded_and_renderable():
    """Warm-start SFT data: every recorded trajectory reaches reward 1.0 and is a valid tool chat."""
    from environments.meeting_reschedule.solver import solve
    env = MeetingReschedule()
    for language in env.languages[::5]:
        for seed in range(6):
            env.reset(seed, "train", language)
            messages, result = solve(env)
            assert result["reward"] == 1.0, (language, seed, result["info"])
            assert messages[0]["role"] == "user" and messages[-1]["role"] == "assistant"
            for m in messages[1:-1]:
                assert m["role"] in ("assistant", "tool")
                if m["role"] == "assistant":
                    assert m["tool_calls"] and all(isinstance(c["function"]["arguments"], dict) for c in m["tool_calls"])
