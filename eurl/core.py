"""Environment discovery, seeding and source digests."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]


def task_rng(environment_id: str, seed: int, split: str, language: Optional[str] = None) -> random.Random:
    """SHA-256 namespaced generator. A fixed language gets its own namespace, so per-language exports are disjoint
    streams; with language=None the environment draws the language (and locale) itself."""
    if split not in ("train", "dev", "eval"):
        raise ValueError("split must be train, dev, or eval")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    key = f"{environment_id}:{split}:{seed}" + (f":{language}" if language else "")
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def manifests() -> list:
    result = []
    for path in sorted((ROOT / "environments").glob("*/manifest.json")):
        data = json.loads(path.read_text())
        if data["id"] != path.parent.name:
            raise ValueError(f"manifest id mismatch: {path}")
        result.append(data)
    return result


def load(environment_id: str):
    available = {m["id"] for m in manifests()}
    if environment_id not in available:
        raise ValueError(f"unknown environment: {environment_id}")
    env = importlib.import_module(f"environments.{environment_id}.environment").create()
    if env.id != environment_id:
        raise ValueError("environment id differs from manifest")
    return env


def source_digest() -> str:
    digest = hashlib.sha256()
    paths = [ROOT / "pyproject.toml"]
    for base in ("eurl", "environments", "tests"):
        paths.extend(p for p in (ROOT / base).rglob("*")
                     if p.suffix in (".py", ".json") and "__pycache__" not in p.parts)
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()
