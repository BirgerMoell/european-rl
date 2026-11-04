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

## Status (M0)

| Part | State |
|---|---|
| Language registry | the 36 OpenEuroLLM / EUROPA languages (`eurl/languages.py`) |
| Payment identifiers | IBAN for 36 countries, ISO 11649 RF, Swedish OCR, Finnish viitenumero, Norwegian KID, Belgian structured communication; tested against python-stdnum |
| Calendar | Western and Orthodox Easter, declarative holiday rules; tested against the `holidays` package |
| Locale packs | SE, DE, FR, PL, FI (money format, holidays, VAT snapshot 2025, company and VAT IDs with check digits, names) |
| Environments | `finance_amount_due` in eng, swe, deu, fra, pol, fin: 5 levels incl. handbook lookup and intra-EU reverse charge; contract passed; independent solver agrees on all tested tasks |

**Text review.** Interface strings and task templates outside English are LLM-written and marked `"llm"` in
`eurl/i18n.py` and each manifest; they are not yet reviewed by native speakers. VAT rates are a dated policy
snapshot (`vat_as_of`, `vat_verified = False`) and are always stated in the task.

## Language coverage

English runs everywhere as the group office language; every other language needs a locale pack of a country that
uses it.

| Code | Language | Countries | Locale pack | Strings |
|---|---|---|---|---|
| bul | Bulgarian | BG | — | — |
| ces | Czech | CZ | — | — |
| dan | Danish | DK | — | — |
| deu | German | DE, AT, LU, BE | ✓ DE | llm |
| ell | Greek | GR, CY | — | — |
| eng | English | IE, MT | — | author |
| est | Estonian | EE | — | — |
| fin | Finnish | FI | ✓ FI | llm |
| fra | French | FR, BE, LU | ✓ FR | llm |
| gle | Irish | IE | — | — |
| hrv | Croatian | HR | — | — |
| hun | Hungarian | HU | — | — |
| ita | Italian | IT | — | — |
| lav | Latvian | LV | — | — |
| lit | Lithuanian | LT | — | — |
| mlt | Maltese | MT | — | — |
| nld | Dutch | NL, BE | — | — |
| pol | Polish | PL | ✓ PL | llm |
| por | Portuguese | PT | — | — |
| ron | Romanian | RO | — | — |
| slk | Slovak | SK | — | — |
| slv | Slovenian | SI | — | — |
| spa | Spanish | ES | — | — |
| swe | Swedish | SE, FI | ✓ SE, FI | llm |
| cat | Catalan | ES | — | — |
| eus | Basque | ES | — | — |
| glg | Galician | ES | — | — |
| isl | Icelandic | IS | — | — |
| nor | Norwegian | NO | — | — |
| sqi | Albanian | AL | — | — |
| bos | Bosnian | BA | — | — |
| srp | Serbian | RS | — | — |
| mkd | Macedonian | MK | — | — |
| tur | Turkish | TR | — | — |
| ukr | Ukrainian | UA | — | — |
| kat | Georgian | GE | — | — |

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
