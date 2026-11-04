# european-rl

**Verifiable RL environments for office, document and agentic work in the 36 languages of
[OpenEuroLLM](https://openeurollm.eu/).**

Almost every stateful agent or office environment used in post-training today (τ²-bench, AppWorld, NVIDIA's
Workplace Assistant, OfficeBench, TheAgentCompany, Spreadsheet-RL) is English-only. None of them encodes how work
is done in Europe: national VAT rules and intra-EU reverse charge, VAT and company numbers with their check digits,
IBAN and SEPA references, national holidays, formats and formal registers. european-rl builds that, one
**locale pack** per country, on a shared synthetic company group with subsidiaries across Europe.

It grows out of [svenska-rl](https://github.com/BirgerMoell/svenska-rl) (the Swedish environments and their
contract) and implements the design in
[european-rl: design](https://birgermoell.github.io/qwen35-posttrain/OELLM_EUROPEAN_RL.html), part of the
[OpenEuroLLM 9B post-training record](https://birgermoell.github.io/qwen35-posttrain/).

## Principles

1. **Localise the world, don't translate the text.** Amounts, identifiers, dates and names come from the locale
   pack; only the prose is translated, so answers stay exact in every language.
2. **Rules live in documents.** From the middle difficulty levels, the rules are in a company-handbook excerpt the
   model has to read, not in the question.
3. **Hard to solve, easy to verify.** Ground truth comes from the simulator; every environment ships a reference
   answer and an independent solver test that re-derives the answer from the public prompt.
4. **Shortcuts must not pay.** Contract v0.3 ([docs/environment-contract.md](docs/environment-contract.md))
   qualifies every environment per language with shortcut probes (empty, abstain-always, copy a number, hedge,
   wrong country's rules, wrong VAT treatment, …): each must earn ≤ 0.3 mean reward.
5. **One answer convention in every language:** a final line `ANSWER: <value>`, abstention `ANSWER: UNKNOWN`.

## Status

| Part | State |
|---|---|
| Languages | all 36 OpenEuroLLM / EUROPA languages (`eurl/languages.py`) |
| Locale packs | 36 countries: EU-27 + IS, NO, AL, BA, RS, MK, TR, UA, GE (money format, local date style, holidays, VAT snapshot 2025, company and VAT IDs with check digits, payment references, names) |
| Oracles | holidays vs the `holidays` package 2024–2030 (lunar and substitute-day calendars in `tests/test_locale_southeast.py`); identifiers and references vs python-stdnum |
| Names | gender-consistent surnames (PL, CZ, SK, LT, LV, BG, MK, GR, Icelandic patronymics) (`eurl/names.py`) |
| `finance_amount_due` | typed answer, 5 levels (national VAT, handbook lookup, discounts, credit notes, rounding, intra-EU reverse charge); contract passed in 36 languages |
| `meeting_reschedule` | tool episode in the synthetic company group: time zones, local office hours and lunch, national days off, cross-lingual requests, notify each participant in their own local time; contract passed in 36 languages; a tools-only solver solves every tested task |
| `business_arithmetic` | exact business arithmetic in local number formats (percentages, VAT in/out, chained discounts, line totals, conversion, splits with remainder, simple interest, margin pricing); slip probes; contract passed in 36 languages |
| `formal_email` | instruction following: formal register (per-language pronoun lists), local money and date formats, exact names, local subject and closing, no code-switching, length, bullets; contract passed in 36 languages |

Tool environments can run behind `python -m eurl.serve` (stdlib HTTP service: reset / step / finish sessions) for
remote RL trainers. Contract reports: `runs/contract-*.json`. First baselines on OpenEuroLLM 9B checkpoints (default / thinking mode):

| Environment | Reward | Note |
|---|---|---|
| business_arithmetic | 0.32–0.40 | level 1 ≈ 0.5, levels 2–3 ≈ 0.2–0.4: in the learnable band |
| finance_amount_due | 0.06–0.11 | levels 1–3 at 8–25 %; arithmetic slips dominate |
| formal_email | 0.11–0.13 (v1 checks) | v1 checks were too strict (vocative names, currency codes, long dates) and were relaxed in v2 |
| meeting_reschedule | ≈ 0.01 | the v1 step budget truncated honest agents; raised to 10 + 6 per participant |

**Text review.** Interface strings and task templates outside English are LLM-written and marked `"llm"` in
`eurl/i18n.py` and each manifest; they are not yet reviewed by native speakers. VAT rates are a dated policy
snapshot (`vat_as_of`, `vat_verified = False`) and are always stated in the task.

## Language coverage

English runs everywhere as the group office language; every other language needs a locale pack of a country that
uses it.

| Code | Language | Countries | Locale pack | Strings |
|---|---|---|---|---|
| bul | Bulgarian | BG | ✓ BG | llm |
| ces | Czech | CZ | ✓ CZ | llm |
| dan | Danish | DK | ✓ DK | llm |
| deu | German | DE, AT, LU, BE | ✓ DE, AT, LU, BE | llm |
| ell | Greek | GR, CY | ✓ GR, CY | llm |
| eng | English | IE, MT | ✓ IE, MT | author |
| est | Estonian | EE | ✓ EE | llm |
| fin | Finnish | FI | ✓ FI | llm |
| fra | French | FR, BE, LU | ✓ FR, BE, LU | llm |
| gle | Irish | IE | ✓ IE | llm |
| hrv | Croatian | HR | ✓ HR | llm |
| hun | Hungarian | HU | ✓ HU | llm |
| ita | Italian | IT | ✓ IT | llm |
| lav | Latvian | LV | ✓ LV | llm |
| lit | Lithuanian | LT | ✓ LT | llm |
| mlt | Maltese | MT | ✓ MT | llm |
| nld | Dutch | NL, BE | ✓ NL, BE | llm |
| pol | Polish | PL | ✓ PL | llm |
| por | Portuguese | PT | ✓ PT | llm |
| ron | Romanian | RO | ✓ RO | llm |
| slk | Slovak | SK | ✓ SK | llm |
| slv | Slovenian | SI | ✓ SI | llm |
| spa | Spanish | ES | ✓ ES | llm |
| swe | Swedish | SE, FI | ✓ SE, FI | llm |
| cat | Catalan | ES | ✓ ES | llm |
| eus | Basque | ES | ✓ ES | llm |
| glg | Galician | ES | ✓ ES | llm |
| isl | Icelandic | IS | ✓ IS | llm |
| nor | Norwegian | NO | ✓ NO | llm |
| sqi | Albanian | AL | ✓ AL | llm |
| bos | Bosnian | BA | ✓ BA | llm |
| srp | Serbian | RS | ✓ RS | llm |
| mkd | Macedonian | MK | ✓ MK | llm |
| tur | Turkish | TR | ✓ TR | llm |
| ukr | Ukrainian | UA | ✓ UA | llm |
| kat | Georgian | GE | ✓ GE | llm |

## Use

```bash
python -m eurl.cli list
python -m eurl.cli show finance_amount_due --language pol --seed 3
python -m eurl.cli check finance_amount_due                 # contract v0.3, all languages
python -m eurl.cli export finance_amount_due --split train --count 200 --out rows.jsonl
pip install -e ".[dev]" && python -m pytest -q
```

The runtime needs only the Python standard library (3.9+). Exported rows have chat `messages`, a JSON
`ground_truth` (the answer spec) and `dataset: eurl_typed`; score a completion with
`eurl.answers.score_answer(json.loads(row["ground_truth"])["spec"], completion)`.

## Roadmap

M1 finance desk and multilingual instruction following in more locales, with L1 baselines on our checkpoints ·
M2 the office world (mail, calendar, contacts, files, ledger) as a multi-turn tool service with injected errors ·
M3 a first expert RL run · M4 simulated customers and citizens, and the remaining locale packs. See the design
document for details.

## License

Apache-2.0. All data is synthetic; no real people, companies or accounts.
