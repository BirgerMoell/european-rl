# Environment contract v0.3

v0.3 is svenska-rl's contract v0.2 ([environment-contract.md](https://github.com/BirgerMoell/svenska-rl/blob/main/docs/environment-contract.md))
made multilingual. Everything there still holds:
- typed answers or tool episodes;
- seeded train/dev/eval namespaces;
- ground truth from simulator state;
- all business rules available in the task;
- synthetic data only;
- no multiple choice.

## Changes from v0.2

- **Language and locale.** Every task carries `language` (ISO 639-3) and `locale` (country pack). `reset(seed,
  split, language=None)` either draws the language or uses the requested one. A fixed language gets its own seed
  namespace.
- **One answer convention.**
  - The final line is `ANSWER: <value>`; abstention is `ANSWER: UNKNOWN`, in every language.
  - Only the explanation around it is localised (`eurl/i18n.py`).
  - Answer parsing accepts any common European rendering of a value ("1.234,50 €", "1 234,50 zł", "1234.50").
    Hedged answers with several values never parse.
- **Rules may live in documents.** Higher levels move rules from the question into a handbook excerpt (typed
  tasks) or a document tool (tool episodes).
- **Qualification is per language** (`eurl.validation.validate_typed`), for each language:
  - determinism;
  - ≥ 90 % unique prompts per split;
  - disjoint splits;
  - the reference earns 1.0, also after reasoning text and after a think block;
  - every shortcut probe ≤ 0.3 mean reward;
  - abstention share 3–30 % where declared;
  - the report lists which languages lack an interface-string table and the review status of each.
- **Environment-specific probes** (`extra_probes`) cover the failure we most want to rule out in a European
  setting: the right arithmetic under the **wrong country's rules**, the wrong VAT treatment (reverse charge
  applied or missed), and ignored conditions such as discounts.
- **Independent solver test.** Every environment ships a test that re-derives the answer from the public prompt in
  every language and agrees with the generator.

## Evidence levels

Unchanged from svenska-rl (`docs/validation.md` there): contract → L1 baseline (a pinned model on the eval split;
a useful environment leaves 10–90 % room) → L2 real RL training → L3 held-out improvement of ≥ 5 points with a
positive lower bound of the paired 95 % bootstrap interval.
