"""Hand-crafted reference DFAs and NFAs for the Phase 0 benchmark languages."""

from __future__ import annotations

from core.dfa import DFA
from core.nfa import NFA


def build_even_ones_dfa() -> DFA:
    """Minimal 2-state DFA accepting binary strings with an even number of 1s."""
    return DFA(
        states={"even", "odd"},
        alphabet=("0", "1"),
        transitions={
            "even": {"0": "even", "1": "odd"},
            "odd": {"0": "odd", "1": "even"},
        },
        start="even",
        accept_states={"even"},
    )


def build_ends_with_ab_dfa() -> DFA:
    """Minimal 3-state DFA accepting strings over {a, b} ending in 'ab'."""
    return DFA(
        states={"q0", "q_a", "q_ab"},
        alphabet=("a", "b"),
        transitions={
            "q0": {"a": "q_a", "b": "q0"},
            "q_a": {"a": "q_a", "b": "q_ab"},
            "q_ab": {"a": "q_a", "b": "q0"},
        },
        start="q0",
        accept_states={"q_ab"},
    )


def build_no_aa_dfa() -> DFA:
    """Minimal 3-state DFA accepting strings over {a, b} without 'aa'."""
    return DFA(
        states={"q0", "q_a", "dead"},
        alphabet=("a", "b"),
        transitions={
            "q0": {"a": "q_a", "b": "q0"},
            "q_a": {"a": "dead", "b": "q0"},
            "dead": {"a": "dead", "b": "dead"},
        },
        start="q0",
        accept_states={"q0", "q_a"},
    )


def build_length_div_3_dfa() -> DFA:
    """Minimal 3-state DFA accepting strings over {a, b} of length divisible by 3."""
    return DFA(
        states={"r0", "r1", "r2"},
        alphabet=("a", "b"),
        transitions={
            "r0": {"a": "r1", "b": "r1"},
            "r1": {"a": "r2", "b": "r2"},
            "r2": {"a": "r0", "b": "r0"},
        },
        start="r0",
        accept_states={"r0"},
    )


def build_exactly_two_as_dfa() -> DFA:
    """Minimal 4-state DFA accepting strings over {a, b} with exactly two 'a's."""
    return DFA(
        states={"c0", "c1", "c2", "c3plus"},
        alphabet=("a", "b"),
        transitions={
            "c0": {"a": "c1", "b": "c0"},
            "c1": {"a": "c2", "b": "c1"},
            "c2": {"a": "c3plus", "b": "c2"},
            "c3plus": {"a": "c3plus", "b": "c3plus"},
        },
        start="c0",
        accept_states={"c2"},
    )


def build_third_from_end_a_nfa() -> NFA:
    """4-state NFA accepting strings over {a, b} whose 3rd symbol from end is 'a'."""
    return NFA(
        states={"s0", "s1", "s2", "s3"},
        alphabet=("a", "b"),
        transitions={
            "s0": {"a": {"s0", "s1"}, "b": {"s0"}},
            "s1": {"a": {"s2"}, "b": {"s2"}},
            "s2": {"a": {"s3"}, "b": {"s3"}},
            "s3": {},
        },
        start="s0",
        accept_states={"s3"},
    )


def build_third_from_end_a_dfa() -> DFA:
    """Minimal 8-state DFA accepting strings whose 3rd symbol from end is 'a'."""
    return build_third_from_end_a_nfa().to_dfa().minimize()


REFERENCE_DFAS: dict[str, DFA] = {
    "even_ones": build_even_ones_dfa(),
    "ends_with_ab": build_ends_with_ab_dfa(),
    "no_aa": build_no_aa_dfa(),
    "length_div_3": build_length_div_3_dfa(),
    "exactly_two_as": build_exactly_two_as_dfa(),
    "third_from_end_a": build_third_from_end_a_dfa(),
}


def get_reference_dfa(language_id: str) -> DFA:
    """Return the reference DFA for a Phase 0 benchmark language."""
    if language_id not in REFERENCE_DFAS:
        available = ", ".join(sorted(REFERENCE_DFAS))
        raise KeyError(f"Unknown language {language_id!r}. Available: {available}")
    return REFERENCE_DFAS[language_id]

