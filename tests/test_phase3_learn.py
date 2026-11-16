"""Phase 3 unit tests for PTA, RPNI, EDSM, and Angluin's L*."""

import pytest

from core import REFERENCE_LANGUAGES, are_equivalent, get_reference_dfa
from data import generate_characteristic_sample, generate_dataset
from learn import (
    build_pta,
    learn_edsm,
    learn_lstar,
    learn_lstar_from_dfa,
    learn_rpni,
    make_dfa_equivalence_oracle,
    make_dfa_membership_oracle,
)


def test_pta_builder_consistency_and_state_ordering():
    examples = [("", True), ("a", False), ("ab", True), ("b", False)]
    pta = build_pta(examples, alphabet=("a", "b"))

    # Root state 0 is epsilon.
    assert pta.start == 0
    assert pta.prefixes[0] == ""
    assert pta.pos_count[0] == 1
    assert pta.neg_count[0] == 0

    dfa = pta.to_dfa()
    for s, lbl in examples:
        assert dfa.matches(s) is lbl

    # Unlabeled intermediate prefixes are not marked accepting.
    # If "aa" was not in training examples, it should not accept.
    assert dfa.matches("aa") is False


def test_pta_rejects_conflicting_labels_in_strict_mode():
    conflicting = [("a", True), ("a", False)]
    with pytest.raises(ValueError, match="Conflicting labels"):
        build_pta(conflicting, strict=True)


@pytest.mark.parametrize("language_id", sorted(REFERENCE_LANGUAGES.keys()))
def test_rpni_recovers_exact_language_from_characteristic_sample(language_id: str):
    target = get_reference_dfa(language_id).minimize()
    char_sample = generate_characteristic_sample(target)

    result = learn_rpni(char_sample, alphabet=target.alphabet)
    eq, counterexample = are_equivalent(result.dfa, target)
    assert eq is True, f"RPNI failed on {language_id}: counterexample {counterexample!r}"
    assert result.metadata["final_states"] == len(target.states)
    assert any(step.step_type == "merge" for step in result.steps)


@pytest.mark.parametrize("language_id", sorted(REFERENCE_LANGUAGES.keys()))
def test_edsm_recovers_exact_language_from_characteristic_sample(language_id: str):
    target = get_reference_dfa(language_id).minimize()
    char_sample = generate_characteristic_sample(target)

    result = learn_edsm(char_sample, alphabet=target.alphabet)
    eq, counterexample = are_equivalent(result.dfa, target)
    assert eq is True, f"EDSM failed on {language_id}: counterexample {counterexample!r}"
    assert result.metadata["final_states"] == len(target.states)
    assert any(step.step_type == "merge" for step in result.steps)


@pytest.mark.parametrize("language_id", sorted(REFERENCE_LANGUAGES.keys()))
def test_lstar_exact_convergence_on_all_reference_languages(language_id: str):
    target = get_reference_dfa(language_id).minimize()
    result = learn_lstar_from_dfa(target)

    eq, counterexample = are_equivalent(result.dfa, target)
    assert eq is True, f"L* failed on {language_id}: counterexample {counterexample!r}"
    assert len(result.dfa.states) == len(target.states)
    assert result.metadata["membership_queries"] > 0
    assert result.metadata["equivalence_queries"] >= 1
    assert any(step.step_type == "lstar_hypothesize" for step in result.steps)


def test_edsm_handles_sparse_random_data():
    target = get_reference_dfa("ends_with_ab")
    data = generate_dataset(
        target,
        min_length=0,
        max_length=6,
        size=35,
        positive_ratio=0.5,
        sampling_mode="length_stratified",
        seed=101,
    )
    result = learn_edsm(data, alphabet=target.alphabet)
    # The learned machine must be consistent with all training data.
    for ex in data:
        assert result.dfa.matches(ex.string) == ex.label


def test_learning_step_serialization():
    target = get_reference_dfa("even_ones")
    sample = generate_characteristic_sample(target)
    result = learn_edsm(sample, alphabet=target.alphabet)

    serialized = result.to_dict()
    assert serialized["algorithm"] == "edsm"
    assert "dfa" in serialized
    assert len(serialized["steps"]) > 0
    for s in serialized["steps"]:
        assert "step_index" in s
        assert "step_type" in s
        assert "description" in s
        assert "data" in s


def test_lstar_manual_oracles():
    target = get_reference_dfa("no_aa")
    mem_oracle = make_dfa_membership_oracle(target)
    eq_oracle = make_dfa_equivalence_oracle(target)

    result = learn_lstar(
        alphabet=target.alphabet,
        membership_oracle=mem_oracle,
        equivalence_oracle=eq_oracle,
    )
    assert are_equivalent(result.dfa, target) == (True, None)

