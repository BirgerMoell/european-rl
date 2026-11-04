"""Command line: list environments, show a task, qualify, export RL rows.

  python -m eurl.cli list
  python -m eurl.cli show ENV [--seed N] [--split S] [--language L]
  python -m eurl.cli check ENV [--cases N] [--out report.json]
  python -m eurl.cli export ENV --split train --count N [--language L ...] --out rows.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys

from eurl.core import load, manifests
from eurl.validation import qualify, save_report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="eurl")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    s = sub.add_parser("show")
    s.add_argument("env")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--split", default="dev")
    s.add_argument("--language")
    c = sub.add_parser("check")
    c.add_argument("env")
    c.add_argument("--cases", type=int)
    c.add_argument("--out")
    e = sub.add_parser("export")
    e.add_argument("env")
    e.add_argument("--split", default="train")
    e.add_argument("--count", type=int, required=True, help="tasks per language")
    e.add_argument("--language", nargs="*")
    e.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    if a.cmd == "list":
        for m in manifests():
            print(f"{m['id']:<28} {m['interaction']:<13} {','.join(m['languages'])}")
        return 0
    if a.cmd == "show":
        env = load(a.env)
        env.reset(a.seed, a.split, a.language)
        print(env.public_prompt())
        print("\n--- reference:", env.reference_completion())
        print("--- meta:", json.dumps(env._task.meta, ensure_ascii=False))
        return 0
    if a.cmd == "check":
        report = qualify(a.env, a.cases)
        report = save_report(a.out, {"environment": a.env, **report}) if a.out else report
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if a.cmd == "export":
        env = load(a.env)
        rows = 0
        with open(a.out, "w", encoding="utf-8") as f:
            for language in a.language or env.languages:
                for seed in range(a.count):
                    env.reset(seed, a.split, language)
                    row = {"id": f"{a.env}:{a.split}:{language}:{seed}",
                           "messages": [{"role": "user", "content": env.public_prompt()}],
                           "ground_truth": json.dumps(env.ground_truth(), ensure_ascii=False),
                           "dataset": "eurl_typed" if env.interaction == "typed_answer" else "eurl_tool",
                           "language": language, "locale": env._task.locale,
                           "level": env._task.meta.get("level")}
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    rows += 1
        print(f"wrote {rows} rows to {a.out}", file=sys.stderr)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
