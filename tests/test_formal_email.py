"""formal_email: the rule checks behave as specified, the reference passes, and qualification holds."""
from environments.formal_email.environment import FormalEmail, text
from eurl.answers import check, score_answer
from eurl.validation import validate_typed


def test_checks():
    assert check({"kind": "contains_any_word", "words": ["Sie"], "case": True}, "Könnten Sie das prüfen?")
    assert not check({"kind": "contains_any_word", "words": ["Sie"], "case": True}, "sie kommen morgen")
    assert not check({"kind": "not_contains_word", "words": ["du"]}, "Kannst du das prüfen?")
    assert check({"kind": "not_contains_word", "words": ["du"]}, "Durchgehend höflich.")   # no substring hits
    assert check({"kind": "word_range", "min": 2, "max": 3}, "eins zwei-drei vier")
    assert check({"kind": "first_line_starts", "value": "Betreff:"}, "**Betreff:** Rechnung\n\nText")
    assert check({"kind": "ends_with_any", "values": ["Mit freundlichen Grüßen"]}, "Text\n\nMit freundlichen Grüßen\nAnna")
    assert check({"kind": "bullets", "count": 2}, "a\n- eins\n- zwei\nb")
    assert not check({"kind": "bullets", "count": 2}, "- eins\n- zwei\n* drei")


def test_reference_and_think_block():
    env = FormalEmail()
    for lang in env.languages:
        for seed in range(30):
            env.reset(seed, "dev", lang)
            ref = env.reference_completion()
            assert score_answer(env._task.spec, ref)["reward"] == 1.0, (lang, seed)
            assert score_answer(env._task.spec, "<think>plan</think>\n" + ref)["reward"] == 1.0
            assert score_answer(env._task.spec, "")["reward"] == 0.0


def test_formal_languages_have_both_lists():
    for lang in FormalEmail().languages:
        t = text(lang)
        if t.get("formal"):
            assert t["formal"]["formal"] and t["formal"]["informal"]


def test_contract_qualification():
    report = validate_typed("formal_email", cases=40)
    assert report["status"] == "passed" and max(report["probe_mean_reward"].values()) <= 0.3
