"""Phase 1 unit tests for DFA, NFA, subset construction, minimization, and equivalence."""

from itertools import product

import pytest

from core import (
    DFA,
    EPSILON,
    NFA,
    REFERENCE_LANGUAGES,
    are_equivalent,
    build_third_from_end_a_nfa,
    get_reference_dfa,
    get_reference_language,
    minimize_dfa,
    nfa_to_dfa,
)


def _all_strings_up_to(alphabet: tuple[str, ...], max_len: int) -> list[str]:
    strings: list[str] = []
    for length in range(max_len + 1):
        for combo in product(alphabet, repeat=length):
            strings.append("".join(combo))
    return strings


@pytest.mark.parametrize("language_id", sorted(REFERENCE_LANGUAGES.keys()))
def test_reference_dfa_matches_oracle_and_paths(language_id: str):
    lang = get_reference_language(language_id)
    dfa = get_reference_dfa(language_id)

    for s in _all_strings_up_to(lang.alphabet, 8):
        accepted, path = dfa.accepts(s)
        assert accepted is lang.accepts(s), f"{language_id} mismatch on {s!r}"
        assert len(path) == len(s) + 1
        assert path[0] == dfa.start
        assert (path[-1] in dfa.accept_states) is accepted


@pytest.mark.parametrize("language_id", sorted(REFERENCE_LANGUAGES.keys()))
def test_reference_dfa_minimization_and_equivalence(language_id: str):
    lang = get_reference_language(language_id)
    dfa = get_reference_dfa(language_id)
    minimized = minimize_dfa(dfa)

    assert len(minimized.states) == lang.expected_min_dfa_states
    assert minimized.is_equivalent_to(dfa) == (True, None)
    assert are_equivalent(dfa, minimized) == (True, None)


@pytest.mark.parametrize("language_id", sorted(REFERENCE_LANGUAGES.keys()))
def test_equivalence_returns_valid_counterexample_when_perturbed(language_id: str):
    dfa = get_reference_dfa(language_id)
    # Flip membership of the start state to guarantee a differing machine.
    flipped_accepts = set(dfa.accept_states)
    if dfa.start in flipped_accepts:
        flipped_accepts.remove(dfa.start)
    else:
        flipped_accepts.add(dfa.start)

    perturbed = DFA(
        states=dfa.states,
        alphabet=dfa.alphabet,
        transitions=dfa.transitions,
        start=dfa.start,
        accept_states=flipped_accepts,
    )

    eq, witness = are_equivalent(dfa, perturbed)
    assert eq is False
    assert witness == ""
    assert dfa.matches(witness) != perturbed.matches(witness)


def test_third_from_end_a_nfa_vs_dfa_blowup():
    nfa = build_third_from_end_a_nfa()
    lang = get_reference_language("third_from_end_a")
    assert len(nfa.states) == lang.expected_nfa_states == 4

    for s in _all_strings_up_to(("a", "b"), 7):
        accepted, path = nfa.accepts(s)
        assert accepted is lang.accepts(s)
        assert len(path) == len(s) + 1

    subset_dfa = nfa_to_dfa(nfa)
    ref_dfa = get_reference_dfa("third_from_end_a")
    assert are_equivalent(subset_dfa, ref_dfa) == (True, None)
    assert len(minimize_dfa(subset_dfa).states) == 8


def test_nfa_with_epsilon_transitions_and_cycles():
    # Language: strings of 0 or more 'a's followed by 0 or more 'b's, using epsilon bridges & cycle.
    nfa = NFA(
        states={"q0", "q1", "q2", "q3"},
        alphabet=("a", "b"),
        transitions={
            "q0": {"a": {"q0"}, EPSILON: {"q1"}},
            "q1": {EPSILON: {"q2"}},
            "q2": {"b": {"q2"}, EPSILON: {"q3"}},
            "q3": {EPSILON: {"q1"}},  # epsilon cycle q1 -> q2 -> q3 -> q1
        },
        start="q0",
        accept_states={"q3"},
    )

    dfa = nfa.to_dfa()
    for s in _all_strings_up_to(("a", "b"), 5):
        expected = ("ba" not in s)
        assert nfa.matches(s) is expected
        assert dfa.matches(s) is expected

    minimized = dfa.minimize()
    # Minimal DFA for a*b* has 3 states: seeing a's (accept), seeing b's (accept), dead (seen 'ba').
    assert len(minimized.states) == 3
    assert are_equivalent(dfa, minimized) == (True, None)


def test_minimize_merges_equivalent_states_and_prunes_unreachable():
    # Non-minimal DFA for "ends with 'a'" with duplicate states and unreachable island.
    bloated = DFA(
        states={"s0", "s1", "s2", "s3", "unreach1", "unreach2"},
        alphabet=("a", "b"),
        transitions={
            "s0": {"a": "s1", "b": "s0"},
            "s1": {"a": "s2", "b": "s3"},
            "s2": {"a": "s1", "b": "s0"},  # equivalent to s1
            "s3": {"a": "s1", "b": "s0"},  # equivalent to s0
            "unreach1": {"a": "unreach2", "b": "unreach1"},
            "unreach2": {"a": "unreach2", "b": "unreach2"},
        },
        start="s0",
        accept_states={"s1", "s2", "unreach2"},
    )

    minimized = minimize_dfa(bloated)
    assert len(minimized.states) == 2
    assert are_equivalent(bloated, minimized) == (True, None)


def test_partial_dfa_simulation_and_completion():
    # Partial DFA accepting only "ab"
    partial = DFA(
        states={"q0", "q1", "q2"},
        alphabet=("a", "b"),
        transitions={
            "q0": {"a": "q1"},
            "q1": {"b": "q2"},
            "q2": {},
        },
        start="q0",
        accept_states={"q2"},
    )

    assert partial.is_complete() is False
    assert partial.accepts("ab") == (True, ["q0", "q1", "q2"])
    assert partial.accepts("b") == (False, ["q0"])
    assert partial.accepts("aba") == (False, ["q0", "q1", "q2"])

    completed = partial.complete()
    assert completed.is_complete() is True
    assert are_equivalent(partial, completed) == (True, None)


def test_degenerate_empty_and_universal_languages():
    empty_lang = DFA(
        states={"q0", "q1"},
        alphabet=("0", "1"),
        transitions={"q0": {"0": "q1", "1": "q1"}, "q1": {"0": "q0", "1": "q0"}},
        start="q0",
        accept_states=set(),
    )
    min_empty = minimize_dfa(empty_lang)
    assert len(min_empty.states) == 1
    assert min_empty.accept_states == frozenset()

    universal_lang = DFA(
        states={"q0", "q1"},
        alphabet=("0", "1"),
        transitions={"q0": {"0": "q1", "1": "q1"}, "q1": {"0": "q0", "1": "q0"}},
        start="q0",
        accept_states={"q0", "q1"},
    )
    min_univ = minimize_dfa(universal_lang)
    assert len(min_univ.states) == 1
    assert len(min_univ.accept_states) == 1


def test_shortest_counterexample_from_equivalence():
    d1 = get_reference_dfa("ends_with_ab")
    # Accepts only "a" instead of strings ending in "ab"
    d2 = DFA(
        states={"q0", "q1", "dead"},
        alphabet=("a", "b"),
        transitions={
            "q0": {"a": "q1", "b": "dead"},
            "q1": {"a": "dead", "b": "dead"},
            "dead": {"a": "dead", "b": "dead"},
        },
        start="q0",
        accept_states={"q1"},
    )
    eq, counterexample = are_equivalent(d1, d2)
    assert eq is False
    # Shortest string where d1 ("ends with ab") and d2 (only "a") differ is "a" (length 1).
    assert counterexample == "a"
    assert d1.matches("a") is False
    assert d2.matches("a") is True


def test_dfa_serialization_roundtrip_and_validation():
    dfa = get_reference_dfa("exactly_two_as")
    restored = DFA.from_dict(dfa.to_dict())
    assert restored.is_equivalent_to(dfa) == (True, None)
    assert restored.states == dfa.states
    assert restored.accept_states == dfa.accept_states

    with pytest.raises(ValueError):
        dfa.accepts("abx")

    other_alpha = get_reference_dfa("even_ones")
    with pytest.raises(ValueError):
        are_equivalent(dfa, other_alpha)

