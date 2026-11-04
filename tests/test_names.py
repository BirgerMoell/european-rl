import random

import pytest

from eurl.locales import PACKS, load
from eurl.names import FEMALE, FEMININE, full_name


@pytest.mark.parametrize("country", sorted(FEMALE))
def test_gender_agreement(country):
    loc = load(country)
    assert FEMALE[country] <= set(loc.first_names), "female names must come from the pack"
    assert set(FEMININE.get(country, {})) <= set(loc.last_names), "mapped surnames must come from the pack"
    rng = random.Random(1)
    for _ in range(500):
        first, last = full_name(rng, loc)
        female = first in FEMALE[country]
        if country == "IS":
            assert last.endswith("dóttir") == female
        elif female and country in FEMININE:
            assert last not in FEMININE[country], (first, last)       # never the masculine form
        else:
            assert last in loc.last_names


def test_every_pack_produces_names():
    rng = random.Random(2)
    for code in PACKS:
        first, last = full_name(rng, load(code))
        assert first and last
