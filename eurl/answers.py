"""Answer extraction and typed scoring (ported from svenska-rl `svrl.answers`, language-neutral).

Every typed task asks for a final line `ANSWER: <answer>`; JSON answers may span several lines after it. Reasoning
before the line is ignored and a `<think>...</think>` trace is stripped. Only the LAST `ANSWER:` counts, and an
answer that hedges (several amounts or dates) does not parse, so listing candidates never earns reward.
`ANSWER: UNKNOWN` is the abstention: correct exactly when the task is unanswerable.

Answer specs are JSON-serialisable, so exported ground truth can be scored without the generator:
  {"type": "money", "value": <minor units>, "minor_digits": 2}
  {"type": "date", "value": "YYYY-MM-DD"}
  {"type": "datetime", "date": "YYYY-MM-DD", "time": "HH:MM"}
  {"type": "integer", "value": int}
  {"type": "text", "value": str, "aliases": [...]}
  {"type": "abstain"}
  {"type": "mapping", "value": {key: value}, "partial": bool}   per-key credit; {"money": minor} values match any
                                                                  single amount equal to it; null = key absent/null
  {"type": "strings", "value": [str, ...]}                      multiset F1
`reward` is 1.0 only for a fully correct answer unless the spec allows partial credit; abstaining on an answerable
task always scores 0.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import unicodedata
from collections import Counter
from typing import Optional

from eurl.i18n import ABSTAIN, ANSWER_KEY
from eurl.money import MoneyFormat, format_money, parse_money

MAX_ANSWER_CHARS = 4000
_LINE = re.compile(rf"(?im)^\s*\**\s*{ANSWER_KEY}\s*\**\s*:\s*")


def strip_reasoning(text: str) -> str:
    text = text or ""
    return text.rsplit("</think>", 1)[1] if "</think>" in text else text


def final_answer(text: str) -> Optional[str]:
    body = strip_reasoning(text)
    matches = list(_LINE.finditer(body))
    if not matches:
        return None
    answer = body[matches[-1].end():].strip()
    answer = re.sub(r"^\*+\s*|\s*\*+$", "", answer)
    answer = re.sub(r"^```(?:json)?\s*|\s*```$", "", answer).strip()
    if not answer or len(answer) > MAX_ANSWER_CHARS:
        return None
    return answer


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").casefold()
    return re.sub(r"\s+", " ", text).strip()


def key_norm(key) -> str:
    text = unicodedata.normalize("NFKD", str(key).strip().casefold())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def is_abstention(answer: Optional[str]) -> bool:
    return answer is not None and norm(answer).strip(" .!`") == norm(ABSTAIN)


def first_line(answer: str) -> str:
    return answer.splitlines()[0].strip() if answer else ""


def parse_json(answer: Optional[str]):
    if answer is None:
        return None
    starts = [i for i in (answer.find("{"), answer.find("[")) if i >= 0]
    if not starts:
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(answer[min(starts):])
        return value
    except json.JSONDecodeError:
        return None


def parse_date(text: Optional[str]) -> Optional[dt.date]:
    found = re.findall(r"\b(\d{4})-(\d{2})-(\d{2})\b", text or "")
    if len(found) != 1:
        return None
    try:
        return dt.date(*map(int, found[0]))
    except ValueError:
        return None


def parse_time(text: Optional[str]) -> Optional[str]:
    found = re.findall(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b", text or "")
    if len(found) != 1:
        return None
    return f"{int(found[0][0]):02d}:{found[0][1]}"


def score_answer(spec: dict, text: str) -> dict:
    answer = final_answer(text)
    if answer is None:
        return {"reward": 0.0, "score": 0.0, "parsed": None, "reason": "no ANSWER line"}
    if spec["type"] == "abstain":
        ok = is_abstention(answer)
        return {"reward": float(ok), "score": float(ok), "parsed": answer[:200], "reason": "abstain"}
    if is_abstention(answer):
        return {"reward": 0.0, "score": 0.0, "parsed": ABSTAIN, "reason": "abstained on answerable task"}
    kind = spec["type"]
    if kind == "money":
        value = parse_money(first_line(answer), spec.get("minor_digits", 2))
        ok = value == spec["value"]
        return {"reward": float(ok), "score": float(ok), "parsed": value, "reason": kind}
    if kind == "date":
        value = parse_date(first_line(answer))
        ok = value is not None and value.isoformat() == spec["value"]
        return {"reward": float(ok), "score": float(ok), "parsed": value and value.isoformat(), "reason": kind}
    if kind == "datetime":
        line = first_line(answer)
        d, t = parse_date(line), parse_time(re.sub(r"\d{4}-\d{2}-\d{2}", " ", line))
        ok = d is not None and d.isoformat() == spec["date"] and t == spec["time"]
        return {"reward": float(ok), "score": float(ok), "parsed": [d and d.isoformat(), t], "reason": kind}
    if kind == "integer":
        found = re.findall(r"-?\d[\d   ]*", first_line(answer))
        value = int(re.sub(r"[   ]", "", found[0])) if len(found) == 1 else None
        ok = value == spec["value"]
        return {"reward": float(ok), "score": float(ok), "parsed": value, "reason": kind}
    if kind == "text":
        targets = {norm(spec["value"]), *(norm(a) for a in spec.get("aliases", []))}
        ok = norm(first_line(answer)).strip(" .") in targets
        return {"reward": float(ok), "score": float(ok), "parsed": first_line(answer)[:200], "reason": kind}
    if kind == "mapping":
        value = parse_json(answer)
        if not isinstance(value, dict):
            return {"reward": 0.0, "score": 0.0, "parsed": None, "reason": "no JSON object"}
        expected = {key_norm(k): v for k, v in spec["value"].items()}
        got = {key_norm(k): v for k, v in value.items()}
        hits = sum(_value_matches(v, got.get(k)) for k, v in expected.items())
        extra = len([k for k in got if k not in expected and got[k] is not None])
        score = max(0.0, (hits - extra) / len(expected))
        exact = hits == len(expected) and not extra
        return {"reward": 1.0 if exact else (score if spec.get("partial") else 0.0), "score": score,
                "parsed": value, "reason": kind}
    if kind == "strings":
        value = parse_json(answer)
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            return {"reward": 0.0, "score": 0.0, "parsed": None, "reason": "no JSON list of strings"}
        got, expected = Counter(x.strip() for x in value), Counter(spec["value"])
        tp = sum((got & expected).values())
        total = sum(got.values()) + sum(expected.values())
        f1 = 2 * tp / total if total else 1.0
        exact = got == expected
        return {"reward": 1.0 if exact else (f1 if spec.get("partial") else 0.0), "score": f1,
                "parsed": value[:50], "reason": kind}
    raise ValueError(f"unknown answer type: {kind}")


def _value_matches(expected, got) -> bool:
    if expected is None:
        return got is None
    if isinstance(expected, dict) and "money" in expected:
        return got is not None and parse_money(str(got)) == expected["money"]
    return got is not None and norm(str(got)) == norm(str(expected))


def render_reference(spec: dict, money_format: Optional[MoneyFormat] = None) -> str:
    """A canonical correct completion (qualification only, never shown to agents)."""
    kind = spec["type"]
    fmt = money_format or MoneyFormat("EUR", "€")
    if kind == "abstain":
        return f"{ANSWER_KEY}: {ABSTAIN}"
    if kind == "money":
        return f"{ANSWER_KEY}: {format_money(spec['value'], fmt)}"
    if kind == "date" or kind == "text" or kind == "integer":
        return f"{ANSWER_KEY}: {spec['value']}"
    if kind == "datetime":
        return f"{ANSWER_KEY}: {spec['date']} {spec['time']}"
    if kind == "mapping":
        value = {k: (format_money(v["money"], fmt) if isinstance(v, dict) and "money" in v else v)
                 for k, v in spec["value"].items()}
        return f"{ANSWER_KEY}: " + json.dumps(value, ensure_ascii=False)
    if kind == "strings":
        return f"{ANSWER_KEY}: " + json.dumps(spec["value"], ensure_ascii=False)
    raise ValueError(kind)
