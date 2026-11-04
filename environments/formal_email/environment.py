"""Write a business e-mail that follows language- and locale-specific requirements (instruction following).

The facts arrive in neutral formats (ISO date, "1234.50 EUR"), and the e-mail must render them the local way. Each
task combines the always-on requirements (the local subject label, a standard local closing) with 2–4 of:
- formal register: the formal pronoun of address must be used and the informal one never (only for languages that
  distinguish them: German Sie/du, French vous/tu, Polish Pan/Pani vs ty, …);
- the amount exactly in the local money format (e.g. "1.234,50 €", "1 234,50 zł");
- the date exactly in the local date style (e.g. "04.03.2026", "4.3.2026", "04/03/2026");
- the recipient's full name exactly as written, diacritics included;
- no English words mixed into a non-English e-mail;
- a word range;
- an exact number of bullet points.
Reward is strict (1 only if every requirement holds); `score` is the fraction met.

Text: text/<iso639-3>.json per language (instructions, topics, requirement phrases, pronouns, closings, filler).
"""
from __future__ import annotations

import datetime as dt
import json
from functools import lru_cache
from pathlib import Path

from eurl.contract import TypedEnvironment, TypedTask
from eurl.languages import LANGUAGES
from eurl.locales import PACKS, format_date
from eurl.locales import load as load_locale
from eurl.money import format_money
from eurl.names import full_name

TEXT_DIR = Path(__file__).parent / "text"
ENGLISH_MARKERS = ["the", "and", "please", "regards", "dear", "thank", "your", "invoice", "payment", "meeting"]


@lru_cache(maxsize=None)
def text(lang: str) -> dict:
    return json.loads((TEXT_DIR / f"{lang}.json").read_text(encoding="utf-8"))


def languages() -> tuple:
    return tuple(sorted(p.stem for p in TEXT_DIR.glob("*.json")))


def locales_for(lang: str) -> tuple:
    packs = {p.upper() for p in PACKS}
    return tuple(c for c in LANGUAGES[lang].countries if c in packs)


class FormalEmail(TypedEnvironment):
    id = "formal_email"
    abstention = False

    @property
    def languages(self) -> tuple:
        return tuple(lang for lang in languages() if locales_for(lang))

    def generate(self, rng, language=None) -> TypedTask:
        lang = language or rng.choice(self.languages)
        t = text(lang)
        country = rng.choice(locales_for(lang))
        loc = load_locale(country)
        want_accent = rng.random() < 0.7  # prefer names with diacritics: copying them exactly is part of the task
        for _ in range(20):
            name = " ".join(full_name(rng, loc))
            if not want_accent or not name.isascii():
                break
        company = f"{rng.choice(loc.company_stems)} {rng.choice(loc.company_suffixes)}"
        sender = " ".join(full_name(rng, loc))
        amount = rng.randint(50, 20000) * 100 * loc.price_scale + rng.choice([0, 50, 25, 90, 5])
        if loc.money.minor_digits == 0:
            amount = amount // 100 * 100
        date = dt.date(2026, 1, 1) + dt.timedelta(days=rng.randint(0, 360))
        neutral_amount = f"{amount // 100}.{amount % 100:02d} {loc.money.currency}" if loc.money.minor_digits else \
            f"{amount // 100} {loc.money.currency}"
        topic_key = rng.choice(sorted(t["topics"]))
        topic = t["topics"][topic_key].format(amount=neutral_amount, date=date.isoformat())
        local_amount = format_money(amount if loc.money.minor_digits else amount // 100, loc.money)
        local_date = format_date(date, loc.date_style)

        checks = [{"kind": "first_line_starts", "value": t["subject_label"]},
                  {"kind": "ends_with_any", "values": t["closings"]}]
        req = [t["req"]["subject"].format(label=t["subject_label"]),
               t["req"]["closing"].format(examples=" / ".join(t["closings"][:2]))]
        optional = ["amount", "date", "name", "words", "bullets"]
        if t.get("formal"):
            optional.append("formal")
        if lang != "eng":
            optional.append("no_english")
        chosen = rng.sample(optional, rng.randint(2, 4))
        bullets = rng.randint(2, 4) if "bullets" in chosen else 0
        # word counts differ by language (compounding, inflection): ranges scale with the language's factor
        factor = t.get("word_factor", 1.0)
        words = tuple(int(x * factor) for x in rng.choice([(50, 130), (80, 170), (100, 200)])) \
            if "words" in chosen else None
        for key in chosen:
            if key == "formal":
                checks.append({"kind": "contains_any_word", "words": t["formal"]["formal"], "case": True})
                checks.append({"kind": "not_contains_word", "words": t["formal"]["informal"]})
                req.append(t["req"]["formal"])
            elif key == "amount":
                major, minor_part = divmod(amount, 100) if loc.money.minor_digits else (amount // 100, 0)
                checks.append({"kind": "local_amount", "whole": major,
                               "minor": f"{minor_part:02d}" if loc.money.minor_digits else "",
                               "decimal": loc.money.decimal, "group": loc.money.group})
                # a neutral example of the local style (not the answer), so the requirement is well-defined
                req.append(t["req"]["amount"] + f" ({format_money(123456 if loc.money.minor_digits else 1234, loc.money)})")
            elif key == "date":
                checks.append({"kind": "local_date", "date": date.isoformat(), "style": loc.date_style})
                req.append(t["req"]["date"] + f" ({format_date(dt.date(2026, 1, 7), loc.date_style)})")
            elif key == "name":
                checks.append({"kind": "name_stems", "parts": name.split()})
                req.append(t["req"]["name"])
            elif key == "no_english":
                checks.append({"kind": "not_contains_word", "words": ENGLISH_MARKERS})
                req.append(t["req"]["no_english"])
            elif key == "words":
                checks.append({"kind": "word_range", "min": words[0], "max": words[1]})
                req.append(t["req"]["words"].format(min=words[0], max=words[1]))
            elif key == "bullets":
                checks.append({"kind": "bullets", "count": bullets})
                req.append(t["req"]["bullets"].format(n=bullets))
        rng.shuffle(req)
        instruction = rng.choice(t["instruction"]).format(
            name=name, company=company, city=rng.choice(loc.cities), topic=topic, sender=sender,
            requirements="\n".join(f"{i + 1}. {r}" for i, r in enumerate(req)))
        spec = {"type": "constraints", "checks": checks}
        meta = {"chosen": chosen, "topic": topic_key, "locale": country,
                "ref": {"name": name, "sender": sender, "amount": local_amount, "date": local_date,
                        "iso_date": date.isoformat(), "neutral_amount": neutral_amount,
                        "bullets": bullets, "words": words, "topic": topic_key}}
        return TypedTask(instruction, spec, "text", lang, country, meta)

    def public_prompt(self) -> str:
        return self._task.instruction  # free text: no ANSWER line is asked for

    def reference_completion(self) -> str:
        """A compliant e-mail built from the language's phrases, padded with filler to the word range."""
        from eurl.answers import _words
        t, r = text(self._task.language), self._task.meta["ref"]
        subject = t["ref_subject"][r["topic"]]
        body = t["ref_body"][r["topic"]].format(amount=r["amount"], date=r["date"])
        head = t["subject_label"] + (subject if subject.startswith(" ") else " " + subject)
        lines = [head, "", t["ref_greeting"].format(name=r["name"]), "", body]
        for i in range(r["bullets"]):
            lines.append(f"- {t['ref_bullets'][i]}")
        closing = [t["closings"][0], r["sender"]]
        lo, hi = r["words"] or (0, 10 ** 6)
        filler = list(t["ref_filler"])
        while len(_words("\n".join(lines + closing))) < lo and filler:
            lines.insert(5, filler.pop(0))
        lines += [""] + closing
        out = "\n".join(lines)
        assert len(_words(out)) <= hi, "reference e-mail longer than the word range"
        return out

    def reference_variants(self, ref: str) -> list:
        return [ref, "<think>draft</think>\n" + ref]

    def extra_probes(self, prompt: str) -> dict:
        t, r = text(self._task.language), self._task.meta["ref"]
        ref = self.reference_completion()
        chosen = self._task.meta["chosen"]
        probes = {"echo_prompt": prompt}
        if "formal" in chosen:
            probes["informal_register"] = ref + "\n" + t["formal"]["informal"][0]
        if "amount" in chosen or "date" in chosen:
            iso = self._task.meta["ref"]["iso_date"]
            neutral = self._task.meta["ref"]["neutral_amount"].split()[0]
            probes["neutral_formats"] = ref.replace(r["amount"], neutral).replace(r["date"], iso)
        if "name" in chosen:
            import unicodedata
            plain = unicodedata.normalize("NFKD", r["name"]).encode("ascii", "ignore").decode()
            if plain != r["name"]:
                probes["name_without_diacritics"] = ref.replace(r["name"], plain)
        probes["no_closing"] = "\n".join(ref.splitlines()[:-2])
        probes["english_email"] = "Subject: Invoice\n\nDear customer,\n\nplease pay the invoice.\n\nKind regards"
        return probes


def create():
    return FormalEmail()
