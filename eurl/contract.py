"""Environment contract v0.3 (docs/environment-contract.md): typed free-form answers and multi-turn tool episodes.

Ported from svenska-rl contract v0.2 with two changes: every task carries a `language` (ISO 639-3) and a `locale`
(country pack), and interface text comes from `eurl.i18n`, so one environment serves many languages.

TypedEnvironment  one prompt, one completion ending in `ANSWER: ...`, scored by an answer spec.
ToolEnvironment   the model calls tools that read and change a simulated system over several turns; the episode
                  ends with a final message (or the step limit) and is scored on the resulting STATE.
Ground truth always comes from simulator state, never from a model.
"""
from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from eurl import answers, i18n
from eurl.core import task_rng
from eurl.locales import load as load_locale
from eurl.money import format_money


@dataclass
class TypedTask:
    instruction: str
    spec: dict
    answer_type: str
    language: str                 # ISO 639-3
    locale: str                   # ISO 3166-1 alpha-2 of the locale pack
    meta: dict = field(default_factory=dict)


class TypedEnvironment:
    id = ""
    contract = "0.3"
    interaction = "typed_answer"
    abstention = False
    partial_reward = False

    def generate(self, rng, language: Optional[str] = None) -> TypedTask:
        raise NotImplementedError

    def reset(self, seed: int = 0, split: str = "train", language: Optional[str] = None) -> dict:
        self._seed, self._split = seed, split
        self._task = self.generate(task_rng(self.id, seed, split, language), language)
        if self.partial_reward:
            self._task.spec = {**self._task.spec, "partial": True}
        self._done = False
        return self.observation()

    def observation(self) -> dict:
        return {"instruction": self.public_prompt(), "answer_type": self._task.answer_type, "max_steps": 1,
                "language": self._task.language}

    def public_prompt(self) -> str:
        t = self._task
        example = format_money(123450, load_locale(t.locale).money) if t.answer_type == "money" else ""
        hint = i18n.text(t.language, t.answer_type, example=example)
        if self.abstention:
            hint += " " + i18n.text(t.language, "abstain")
        return f"{t.instruction.rstrip()}\n\n{hint}"

    def step(self, completion: Any) -> dict:
        if not hasattr(self, "_task"):
            raise RuntimeError("reset before step")
        if self._done:
            raise RuntimeError("episode already terminated")
        self._done = True
        result = answers.score_answer(self._task.spec, completion if isinstance(completion, str) else "")
        return {"observation": {"message": i18n.text(self._task.language, "done")}, "reward": result["reward"],
                "terminated": True, "truncated": False, "info": {**result, "meta": self._task.meta}}

    def reference_completion(self) -> str:
        return answers.render_reference(self._task.spec, load_locale(self._task.locale).money)

    def ground_truth(self) -> dict:
        return {"env": self.id, "seed": self._seed, "split": self._split, "language": self._task.language,
                "locale": self._task.locale, "spec": self._task.spec}

    def extra_probes(self, prompt: str) -> dict:
        """Environment-specific shortcut completions (e.g. the answer under another country's VAT rates)."""
        return {}


# --- tool episodes ----------------------------------------------------------------------------------------------

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable
    mutates: bool = False

    def schema(self) -> dict:
        return {"type": "function", "function": {"name": self.name, "description": self.description,
                                                 "parameters": self.parameters}}


@dataclass
class ToolTask:
    instruction: str
    state: Any
    tools: list
    check: Callable
    reference: list
    language: str
    locale: str
    max_steps: int = 20
    meta: dict = field(default_factory=dict)


class ToolError(Exception):
    """A business-level error raised by a tool; returned to the agent as an error observation."""


def _check_arguments(tool: Tool, arguments: Any, lang: str) -> Optional[str]:
    if not isinstance(arguments, dict):
        return i18n.text(lang, "err_args_object")
    props = tool.parameters.get("properties", {})
    for key in tool.parameters.get("required", []):
        if key not in arguments:
            return i18n.text(lang, "err_missing", key=key)
    types = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}
    for key, value in arguments.items():
        if key not in props:
            return i18n.text(lang, "err_unknown_arg", key=key)
        expected = props[key].get("type")
        if expected in types and (not isinstance(value, types[expected]) or
                                  (expected in ("integer", "number") and isinstance(value, bool))):
            return i18n.text(lang, "err_type", key=key, expected=expected)
        if "enum" in props[key] and value not in props[key]["enum"]:
            return i18n.text(lang, "err_enum", key=key)
    return None


_TOOL_CALL = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.S)


def parse_assistant(text: str) -> list:
    """Hermes/Qwen `<tool_call>{...}</tool_call>` blocks, else one final answer."""
    body = answers.strip_reasoning(text or "")
    calls = []
    for raw in _TOOL_CALL.findall(body):
        try:
            obj = json.loads(raw)
            calls.append({"tool": obj.get("name"), "arguments": obj.get("arguments", {})})
        except (json.JSONDecodeError, AttributeError):
            calls.append({"tool": None, "arguments": None, "malformed": raw[:200]})
    return calls or [{"final": body.strip()}]


class ToolEnvironment:
    id = ""
    contract = "0.3"
    interaction = "tool_episode"

    def generate(self, rng, language: Optional[str] = None) -> ToolTask:
        raise NotImplementedError

    def reset(self, seed: int = 0, split: str = "train", language: Optional[str] = None) -> dict:
        self._seed, self._split = seed, split
        self._task = self.generate(task_rng(self.id, seed, split, language), language)
        self._state = copy.deepcopy(self._task.state)
        self._tools = {t.name: t for t in self._task.tools}
        self._steps, self._done, self.trace = 0, False, []
        return self.observation()

    def observation(self) -> dict:
        return {"instruction": self._task.instruction, "tools": [t.schema() for t in self._task.tools],
                "max_steps": self._task.max_steps, "language": self._task.language}

    def public_prompt(self) -> str:
        return self._task.instruction

    def step(self, action: Any) -> dict:
        if not hasattr(self, "_task"):
            raise RuntimeError("reset before step")
        if self._done:
            raise RuntimeError("episode already terminated")
        lang = self._task.language
        if isinstance(action, str):
            parsed = parse_assistant(action)
            if len(parsed) != 1:
                raise ValueError("one action per step; split multi-call messages with parse_assistant()")
            action = parsed[0]
        self._steps += 1
        if not isinstance(action, dict) or ("final" not in action and "tool" not in action):
            observation = {"error": i18n.text(lang, "err_action")}
            self.trace.append({"action": repr(action)[:200], "observation": observation})
            return self._maybe_truncate(observation)
        if "final" in action:
            return self._finish(str(action["final"]), truncated=False)
        tool = self._tools.get(action.get("tool"))
        if tool is None:
            observation = {"error": i18n.text(lang, "err_tool", name=action.get("tool"))}
        else:
            problem = _check_arguments(tool, action.get("arguments"), lang)
            if problem:
                observation = {"error": problem}
            else:
                try:
                    observation = {"result": tool.fn(self._state, **action["arguments"])}
                except ToolError as error:
                    observation = {"error": str(error)}
        self.trace.append({"action": action, "observation": observation})
        return self._maybe_truncate(observation)

    def _maybe_truncate(self, observation: dict) -> dict:
        if self._steps >= self._task.max_steps:
            return self._finish("", truncated=True, observation=observation)
        return {"observation": observation, "reward": 0.0, "terminated": False, "truncated": False, "info": {}}

    def _finish(self, final: str, truncated: bool, observation: Optional[dict] = None) -> dict:
        self._done = True
        result = self._task.check(self._state, final)
        return {"observation": observation or {"message": i18n.text(self._task.language, "done")},
                "reward": float(result["reward"]), "terminated": not truncated, "truncated": truncated,
                "info": {**result, "steps": self._steps, "meta": self._task.meta}}

    def reference_actions(self) -> list:
        return copy.deepcopy(self._task.reference)

    def extra_probe_plans(self) -> dict:
        """Environment-specific shortcut plans: name -> function(env) returning an action list (or None)."""
        return {}

    def ground_truth(self) -> dict:
        return {"env": self.id, "seed": self._seed, "split": self._split, "language": self._task.language,
                "locale": self._task.locale}


def run_actions(env: ToolEnvironment, actions: list) -> dict:
    result = None
    for action in actions:
        result = env.step(action)
        if result["terminated"] or result["truncated"]:
            return result
    return env.step({"final": ""}) if result is None or not (result["terminated"] or result["truncated"]) else result
