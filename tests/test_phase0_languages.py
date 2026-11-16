"""Phase 0 tests for reference language specifications and project layout."""

import pytest

from core.languages import (
    DEFAULT_ALPHABETS,
    REFERENCE_LANGUAGES,
    get_reference_language,
)


def test_initial_alphabets_in_scope():
    assert DEFAULT_ALPHABETS["binary"] == ("0", "1")
    assert DEFAULT_ALPHABETS["ab"] == ("a", "b")


def test_six_reference_languages_defined():
    expected_ids = {
        "even_ones",
        "ends_with_ab",
        "no_aa",
        "length_div_3",
        "exactly_two_as",
        "third_from_end_a",
    }
    assert set(REFERENCE_LANGUAGES.keys()) == expected_ids


@pytest.mark.parametrize("language_id", sorted(REFERENCE_LANGUAGES.keys()))
def test_reference_language_examples(language_id: str):
    lang = get_reference_language(language_id)
    assert lang.positive_examples
    assert lang.negative_examples
    assert lang.expected_min_dfa_states >= 2

    for s in lang.positive_examples:
        lang.validate_string(s)
        assert lang.accepts(s) is True, f"{language_id} should accept {s!r}"

    for s in lang.negative_examples:
        lang.validate_string(s)
        assert lang.accepts(s) is False, f"{language_id} should reject {s!r}"


def test_validate_string_rejects_out_of_alphabet_symbol():
    lang = get_reference_language("even_ones")
    with pytest.raises(ValueError):
        lang.validate_string("01a")


def test_get_reference_language_unknown_id():
    with pytest.raises(KeyError):
        get_reference_language("nonexistent_lang")

