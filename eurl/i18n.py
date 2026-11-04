"""Interface strings per language: answer-format hints and tool-episode messages, one JSON file per language in
eurl/strings/<iso639-3>.json (adding a language is adding a file).

The answer keyword `ANSWER:` and the abstention token `UNKNOWN` are the same in every language (one convention for
the model to learn, shared with our eu_qa suite); the explanation around them is localised. Each file's `_review`
records who checked it: "author" (written by the maintainer), "llm" (written or translated by an LLM, not yet
reviewed by a native speaker) or "native:<who>". Languages without a file fall back to English and are flagged by
the contract check.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

ANSWER_KEY = "ANSWER"
ABSTAIN = "UNKNOWN"
KEYS = ("money", "date", "datetime", "integer", "text", "mapping", "strings", "abstain", "done", "err_action",
        "err_tool", "err_args_object", "err_missing", "err_unknown_arg", "err_type", "err_enum")

_DIR = Path(__file__).parent / "strings"
STRINGS: Dict[str, Dict[str, str]] = {}
REVIEW: Dict[str, str] = {}
for _path in sorted(_DIR.glob("*.json")):
    _data = json.loads(_path.read_text(encoding="utf-8"))
    REVIEW[_path.stem] = _data.pop("_review", "unknown")
    STRINGS[_path.stem] = _data


def text(lang: str, key: str, **slots) -> str:
    table = STRINGS.get(lang, STRINGS["eng"])
    return table.get(key, STRINGS["eng"][key]).format(**slots)
