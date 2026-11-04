# Adding a country or a language

european-rl covers the 36 OpenEuroLLM languages through **locale packs** (one per country) and **text files**
(one per language). Both are plain files; nothing else needs editing.

## A locale pack: `eurl/locales/<cc>.py`

`<cc>` is the ISO 3166-1 alpha-2 code in lower case. The module defines `LOCALE = Locale(...)`
(`eurl/locales/__init__.py`) and is discovered automatically. Rules:

1. **Facts are real; data is synthetic.** Every fact must be correct for the year in `vat_as_of` (2025):
   - holidays, VAT rates, money format, identifier check digits, time zone;
   - company and person names are invented, cities are real.

   Cite sources in `vat_source` and `notes`. Leave `vat_verified=False`; a person sets it after checking.
2. **Holidays** use the rules in `eurl/calendar.py`: `fixed`, `easter_rule`, `orthodox_rule`, `weekday_from`.
   - Statutory public holidays have `public=True`.
   - Customary days off (e.g. Christmas Eve where offices close but the law does not say so) have `public=False`.
   - National holidays only. Regional ones go in `notes`.
   - `names` holds the holiday's name in every language of the pack.
   - Tests compare the pack with the `holidays` package for 2024–2030. They must match exactly, either our public
     set or our full set of days off.
3. **VAT** (`vat_bp`, basis points: 2550 = 25.5 %) for every category in `eurl.locales.VAT_CATEGORIES`:
   - categories: standard, food, accommodation, books, passenger_transport, restaurant;
   - use the rate that applies to typical goods and services in the category (food = basic groceries,
     books = printed books, passenger_transport = domestic rail or bus);
   - **non-EU countries** use their VAT/GST equivalent and set `eu_member=False`;
   - a country with one flat rate uses it for every category, with a note.
4. **Identifiers.**
   - `company_id(rng)` produces a national company number in display form.
   - `vat_id(rng, company_id)` produces the VAT identification number, with the country prefix for EU members.
   - `vat_id_valid(value)` checks it.
   - Implement check digits **in the pack module** (not in shared files). Where python-stdnum has a validator for
     the country, the pack's test must check generated numbers with it.
5. **Payments.**
   - `payment_reference(rng)` is the national structured reference if the country has one with a known check
     algorithm. Otherwise use `banking.rf_reference` (SEPA countries) or a plain invoice-number reference.
   - The country must exist in `banking.IBAN_LENGTH`.
6. **Money** (`MoneyFormat`): ISO 4217 code, symbol as written locally, decimal and grouping separators, symbol
   position, `minor_digits` (0 only where the currency has no minor unit in practice, e.g. ISK).
   - `price_scale` is a rough euro-to-local factor for synthetic prices (an integer ≥ 1).
   - `format_money` → `parse_money` must round-trip.
7. **Names and places.**
   - 12 common given names, 12 common family names, 8 real cities.
   - 10 invented company-name stems that sound local, and the local legal-form suffixes.
   - **No real company names, no offensive or historically loaded words** (concentration camps, massacres, slurs,
     political figures).
   - Read the list once more before committing.
8. **Office hours and lunch** as locally typical.

Add a test file `tests/test_locale_<cc>.py`, or one per batch. Beyond the shared tests in `tests/test_locales.py`
(which already run on every pack) it holds:
- the stdnum cross-checks;
- at least one known-valid real-world identifier example, if a public one exists;
- one known invalid example.

## A language: two JSON files

- `eurl/strings/<iso639-3>.json`: the interface strings. Copy `eng.json` and translate the values. Keep every key,
  every `{placeholder}`, and the literal `ANSWER:` and `UNKNOWN`. Set `"_review": "llm"`.
- `environments/finance_amount_due/text/<iso639-3>.json`: the task text. Copy `eng.json` and translate.
  - Keep the structure: `intro` and `question` are lists of alternative phrasings (3 and 2), with the same
    placeholders.
  - In `handbook`, `{country}` must come before `{rates}`.
  - `discount` must contain `{p}`.
  - `items`, `categories` and `countries` are dicts with the same keys as `eng.json`. **`countries` names all 36
    countries in `eurl/languages.py`.**
  - Use the register a business document in that language would use. Prefer the formal address where the
    language distinguishes it.
  - Set `"_review": "llm"`.

A language only runs once a locale pack of one of its countries exists (`eurl/languages.py` lists them).
English runs in every pack.

## Before you commit

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m eurl.cli check finance_amount_due --cases 40
```

Both must pass. The independent solver test (`tests/test_finance_amount_due.py`) re-solves tasks in your new
language from the prompt text alone; if it fails, the template is ambiguous. Fix the template, not the test.
