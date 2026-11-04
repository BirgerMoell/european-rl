"""Contract qualification (v0.3) and paired evaluation statistics. Finite tests cannot prove that an environment
has no bugs.

Typed environments are qualified per language: determinism, task diversity, disjoint splits, the reference answer
earns 1.0 (also after reasoning text and after a think block), shortcut probes earn at most 0.3 mean reward, the
abstention share is in range, and the language has an interface-string table.
"""
from __future__ import annotations

import json
import math
import random
import re
from datetime import datetime, timezone
from pathlib import Path

from eurl import i18n
from eurl.core import load, source_digest
from eurl.i18n import ABSTAIN, ANSWER_KEY
from eurl.money import _AMOUNT, parse_money

PROBE_MAX_MEAN = 0.3
ABSTAIN_RANGE = (0.03, 0.3)


def paired_bootstrap(before, after, repetitions=2000):
    if len(before) != len(after) or len(before) < 2:
        raise ValueError("paired evaluation needs at least two matching cases")
    if [r["seed"] for r in before] != [r["seed"] for r in after]:
        raise ValueError("evaluation cases differ")
    delta = [b["reward"] - a["reward"] for a, b in zip(before, after)]
    if any(not math.isfinite(x) for x in delta):
        raise ValueError("non-finite rewards")
    rng = random.Random(1729)
    samples = sorted(sum(rng.choices(delta, k=len(delta))) / len(delta) for _ in range(repetitions))
    return {"delta": sum(delta) / len(delta),
            "ci95": [samples[int(repetitions * .025)], samples[int(repetitions * .975)]]}


def save_report(path, report):
    report = dict(report, schema_version=1, source_sha256=source_digest(),
                  created_at=datetime.now(timezone.utc).isoformat())
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def typed_probes(env, prompt: str) -> dict:
    """Shortcut completions that must not pay off."""
    a = f"{ANSWER_KEY}:"
    amounts = [m for m in _AMOUNT.findall(prompt) if parse_money(m) is not None]
    nums = re.findall(r"\d+(?:[.,]\d+)?", prompt)
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", prompt)
    probes = {
        "empty": "", "no_answer_line": "I have calculated it.", "bare_answer": a,
        "abstain": f"{a} {ABSTAIN}",
        "first_number": f"{a} {nums[0]}" if nums else f"{a} 0",
        "last_amount": f"{a} {amounts[-1]}" if amounts else f"{a} 0",
        "largest_amount": f"{a} {max(amounts, key=lambda x: parse_money(x) or 0)}" if amounts else f"{a} 0",
        "all_numbers": f"{a} " + " ".join(nums[:40]),
        "first_date": f"{a} {dates[0]} 08:00" if dates else f"{a} 2026-01-01 08:00",
        "json_empty_object": f"{a} {{}}", "json_empty_list": f"{a} []",
        "think_only": f"<think>{a} 1</think>",
    }
    if env._task.answer_type == "mapping":
        keys = list(env._task.spec.get("value", {}))
        probes["all_zero"] = f"{a} " + json.dumps({k: 0 for k in keys})
    probes.update(env.extra_probes(prompt))
    return probes


def validate_typed(environment_id: str, cases: int = 100, languages=None) -> dict:
    env = load(environment_id)
    languages = list(languages or env.languages)
    per_language, probe_rewards, abstain_tasks, total = {}, {}, 0, 0
    for language in languages:
        split_prompts = {}
        for split in ("train", "dev", "eval"):
            prompts = set()
            for seed in range(cases):
                obs = env.reset(seed, split, language)
                prompt, spec = env.public_prompt(), json.dumps(env._task.spec, sort_keys=True)
                if obs != env.reset(seed, split, language) or prompt != env.public_prompt() or \
                        spec != json.dumps(env._task.spec, sort_keys=True):
                    raise ValueError("reset is not deterministic")
                if env._task.language != language:
                    raise ValueError(f"task language {env._task.language} != requested {language}")
                ref = env.reference_completion()
                for completion in (ref, "Let me work it out.\n\n" + ref, f"<think>draft\n{ANSWER_KEY}: 0</think>\n" + ref):
                    env.reset(seed, split, language)
                    if env.step(completion)["reward"] != 1.0:
                        raise ValueError(f"reference not rewarded ({language}, seed {seed}, {split}): {completion[-200:]}")
                abstain_tasks += env._task.spec["type"] == "abstain"
                total += 1
                for name, completion in typed_probes(env, prompt).items():
                    if completion == ref:
                        continue
                    env.reset(seed, split, language)
                    probe_rewards.setdefault(name, []).append(env.step(completion)["reward"])
                for bad in (None, 42, {}, [f"{ANSWER_KEY}: 1"]):
                    env.reset(seed, split, language)
                    if env.step(bad)["reward"] != 0:
                        raise ValueError("non-text completion rewarded")
                prompts.add(prompt)
            if len(prompts) < cases * 0.9:
                raise ValueError(f"insufficient task diversity ({language}, {split})")
            split_prompts[split] = prompts
        if any(split_prompts[x] & split_prompts[y] for x, y in (("train", "dev"), ("train", "eval"), ("dev", "eval"))):
            raise ValueError(f"prompt overlap between splits ({language})")
        per_language[language] = {"unique_prompts": sum(len(p) for p in split_prompts.values()),
                                  "strings": i18n.REVIEW.get(language, "missing (English fallback)")}
    probe_means = {k: sum(v) / len(v) for k, v in probe_rewards.items()}
    exploitable = {k: round(v, 3) for k, v in probe_means.items() if v > PROBE_MAX_MEAN}
    if exploitable:
        raise ValueError(f"shortcut probes earn too much reward: {exploitable}")
    abstain_rate = abstain_tasks / total
    if env.abstention and not ABSTAIN_RANGE[0] <= abstain_rate <= ABSTAIN_RANGE[1]:
        raise ValueError(f"abstention share {abstain_rate:.2f} outside {ABSTAIN_RANGE}")
    if not env.abstention and abstain_tasks:
        raise ValueError("unanswerable tasks in an environment that does not declare abstention")
    missing = [lang for lang in languages if lang not in i18n.STRINGS]
    return {"status": "passed", "contract": "0.3", "interaction": "typed_answer", "cases_per_split": cases,
            "languages": per_language, "reference_success": 1.0, "abstain_share": round(abstain_rate, 3),
            "missing_string_tables": missing,
            "probe_mean_reward": {k: round(v, 3) for k, v in sorted(probe_means.items())}}


def validate_tools(environment_id: str, cases: int = 40, languages=None) -> dict:
    """Tool episodes, per language: determinism, the reference reaches 1.0, malformed actions are errors that do
    not end the episode, the step limit holds, read-only spam earns nothing, dropping a required state change
    costs the reward, and environment shortcut plans (`extra_probe_plans`) stay at or below 0.3."""
    import hashlib
    from eurl.contract import run_actions
    env = load(environment_id)
    languages = list(languages or env.languages)
    probe_rewards, per_language = {}, {}
    for language in languages:
        split_tasks = {}
        for split in ("train", "dev", "eval"):
            tasks = set()
            for seed in range(cases):
                obs = env.reset(seed, split, language)
                if obs != env.reset(seed, split, language):
                    raise ValueError("reset is not deterministic")
                result = run_actions(env, env.reference_actions())
                if result["reward"] != 1.0 or not result["terminated"]:
                    raise ValueError(f"reference not rewarded ({language}, seed {seed}, {split}): {result['info']}")
                try:
                    env.step({"final": "again"})
                except RuntimeError:
                    pass
                else:
                    raise ValueError("terminated episode accepted another action")
                env.reset(seed, split, language)
                probe_rewards.setdefault("finish_immediately", []).append(env.step({"final": "Done."})["reward"])
                env.reset(seed, split, language)
                names = sorted(t["function"]["name"] for t in obs["tools"])
                for bad in ({"tool": "does_not_exist", "arguments": {}}, {"tool": names[0], "arguments": "x"},
                            {"tool": names[0], "arguments": {"unknown_arg": 1}}, 17, {"x": 1},
                            "<tool_call>{not json</tool_call>"):
                    step = env.step(bad)
                    if step["terminated"] or "error" not in step["observation"]:
                        raise ValueError(f"malformed action not reported as an error: {bad!r}")
                env.reset(seed, split, language)
                reader = next(t for t in env._task.tools if not t.mutates and not t.parameters.get("required"))
                step = {"terminated": False, "truncated": False}
                for _ in range(env._task.max_steps + 1):
                    step = env.step({"tool": reader.name, "arguments": {}})
                    if step["terminated"] or step["truncated"]:
                        break
                if not step["truncated"]:
                    raise ValueError("step limit not enforced")
                probe_rewards.setdefault("read_until_limit", []).append(step["reward"])
                ref = env.reference_actions()
                mutating = [i for i, a in enumerate(ref) if "tool" in a and env._tools[a["tool"]].mutates]
                if mutating:
                    env.reset(seed, split, language)
                    partial = run_actions(env, [a for i, a in enumerate(ref) if i != mutating[0]])
                    if partial["reward"] >= 1.0:
                        raise ValueError("dropping a required state change still earns full reward")
                for name, plan in env.extra_probe_plans().items():
                    env.reset(seed, split, language)
                    plan_actions = plan(env)
                    if plan_actions is None:
                        continue
                    probe_rewards.setdefault(name, []).append(run_actions(env, plan_actions)["reward"])
                tasks.add(hashlib.sha256((obs["instruction"] + json.dumps(ref, sort_keys=True, ensure_ascii=False)
                                          ).encode()).hexdigest())
            if len(tasks) < cases * 0.9:
                raise ValueError(f"insufficient task diversity ({language}, {split})")
            split_tasks[split] = tasks
        if any(split_tasks[x] & split_tasks[y] for x, y in (("train", "dev"), ("train", "eval"), ("dev", "eval"))):
            raise ValueError(f"task overlap between splits ({language})")
        per_language[language] = {"tasks": sum(len(v) for v in split_tasks.values())}
    probe_means = {k: sum(v) / len(v) for k, v in probe_rewards.items()}
    exploitable = {k: round(v, 3) for k, v in probe_means.items() if v > PROBE_MAX_MEAN}
    if exploitable:
        raise ValueError(f"shortcut probes earn too much reward: {exploitable}")
    return {"status": "passed", "contract": "0.3", "interaction": "tool_episode", "cases_per_split": cases,
            "languages": per_language, "reference_success": 1.0,
            "probe_mean_reward": {k: round(v, 3) for k, v in sorted(probe_means.items())}}


def qualify(environment_id: str, cases=None, languages=None) -> dict:
    env = load(environment_id)
    if env.interaction == "typed_answer":
        return validate_typed(environment_id, cases or 100, languages)
    if env.interaction == "tool_episode":
        return validate_tools(environment_id, cases or 40, languages)
    raise ValueError(f"unknown interaction: {env.interaction}")
