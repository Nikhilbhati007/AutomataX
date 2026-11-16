"""Phase 2 unit tests for regex compilation, dataset generation, splits, and characteristic samples."""

from itertools import product
import re

import pytest

from core import REFERENCE_LANGUAGES, are_equivalent, get_reference_dfa, get_reference_language
from data import (
    generate_characteristic_sample,
    generate_dataset,
    generate_train_test_split,
    regex_to_dfa,
)


def _all_strings_up_to(alphabet: tuple[str, ...], max_len: int) -> list[str]:
    out: list[str] = []
    for ell in range(max_len + 1):
        for combo in product(alphabet, repeat=ell):
            out.append("".join(combo))
    return out


@pytest.mark.parametrize(
    ("pattern", "alphabet"),
    [
        ("(a|b)*ab", ("a", "b")),
        ("(0|10*1)*", ("0", "1")),
        ("a+b?", ("a", "b")),
        ("(ab)*", ("a", "b")),
        ("", ("a", "b")),
    ],
)
def test_regex_to_dfa_matches_python_re(pattern: str, alphabet: tuple[str, ...]):
    dfa = regex_to_dfa(pattern, alphabet=alphabet)
    compiled = re.compile(pattern)
    for s in _all_strings_up_to(alphabet, 6):
        expected = compiled.fullmatch(s) is not None
        assert dfa.matches(s) is expected, f"Regex {pattern!r} mismatch on {s!r}"


def test_regex_equivalence_with_reference_dfas():
    assert are_equivalent(
        regex_to_dfa("(a|b)*ab", alphabet=("a", "b")),
        get_reference_dfa("ends_with_ab"),
    ) == (True, None)
    assert are_equivalent(
        regex_to_dfa("(0|10*1)*", alphabet=("0", "1")),
        get_reference_dfa("even_ones"),
    ) == (True, None)


def test_regex_validation_errors():
    with pytest.raises(ValueError):
        regex_to_dfa("(ab", alphabet=("a", "b"))
    with pytest.raises(ValueError):
        regex_to_dfa("*a", alphabet=("a", "b"))
    with pytest.raises(ValueError):
        regex_to_dfa("ac", alphabet=("a", "b"))


@pytest.mark.parametrize("sampling_mode", ["uniform", "length_stratified", "random_walk"])
def test_generate_dataset_sampling_modes_and_balance(sampling_mode: str):
    dfa = get_reference_dfa("ends_with_ab")
    data = generate_dataset(
        dfa,
        min_length=1,
        max_length=7,
        size=40,
        positive_ratio=0.5,
        sampling_mode=sampling_mode,  # type: ignore[arg-type]
        seed=42,
    )
    assert len(data) == 40
    assert len({ex.string for ex in data}) == 40
    for ex in data:
        assert 1 <= len(ex.string) <= 7
        assert ex.label == ex.true_label == dfa.matches(ex.string)

    pos_count = sum(1 for ex in data if ex.label)
    assert 15 <= pos_count <= 25


def test_length_stratified_covers_every_length():
    lang = get_reference_language("even_ones")
    data = generate_dataset(
        lang,
        min_length=0,
        max_length=5,
        size=30,
        sampling_mode="length_stratified",
        seed=7,
    )
    lengths = {len(ex.string) for ex in data}
    assert lengths == {0, 1, 2, 3, 4, 5}


def test_dataset_reproducibility_and_noise_injection():
    d1 = generate_dataset("a(a|b)*", alphabet=("a", "b"), size=50, noise_rate=0.2, seed=123)
    d2 = generate_dataset("a(a|b)*", alphabet=("a", "b"), size=50, noise_rate=0.2, seed=123)
    assert d1 == d2

    noisy = [ex for ex in d1 if ex.is_noisy]
    assert len(noisy) == 10  # round(50 * 0.2)
    for ex in noisy:
        assert ex.label is (not ex.true_label)


def test_train_test_split_has_longer_disjoint_clean_test_strings():
    split = generate_train_test_split(
        get_reference_language("third_from_end_a"),
        train_min_length=0,
        train_max_length=5,
        train_size=40,
        test_min_length=6,
        test_max_length=10,
        test_size=60,
        noise_rate=0.1,
        seed=99,
    )

    assert len(split.train) == 40
    assert len(split.test) == 60
    assert split.metadata["noisy_train_count"] == 4

    train_strs = {ex.string for ex in split.train}
    test_strs = {ex.string for ex in split.test}
    assert train_strs.isdisjoint(test_strs)

    for ex in split.train:
        assert 0 <= len(ex.string) <= 5
    for ex in split.test:
        assert 6 <= len(ex.string) <= 10
        assert not ex.is_noisy


def test_sparse_or_empty_class_terminates_cleanly():
    # Length >= 3 with regex "a": zero positive examples exist at length 3..5.
    data = generate_dataset("a", alphabet=("a", "b"), min_length=3, max_length=5, size=10, seed=1)
    assert len(data) == 10
    assert all(ex.label is False for ex in data)


@pytest.mark.parametrize("language_id", sorted(REFERENCE_LANGUAGES.keys()))
def test_characteristic_sample_properties(language_id: str):
    dfa = get_reference_dfa(language_id).minimize()
    sample = generate_characteristic_sample(dfa)
    assert sample

    # All labels match ground truth, no duplicates.
    strings = [ex.string for ex in sample]
    assert len(strings) == len(set(strings))
    for ex in sample:
        assert ex.label == ex.true_label == dfa.matches(ex.string)

    # Every state in the minimal DFA must be visited by at least one prefix of the sample.
    prefixes = {s[:i] for s in strings for i in range(len(s) + 1)}
    visited_states = set()
    for p in prefixes:
        _, path = dfa.accepts(p)
        visited_states.add(path[-1])
    assert visited_states == dfa.states
