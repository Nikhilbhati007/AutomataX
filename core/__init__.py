"""Core automata engine: DFA, NFA, conversions, minimization, and equivalence."""

from core.algorithms import (
    architect_automata,
    are_equivalent,
    minimize_dfa,
    nfa_remove_epsilon,
    nfa_to_dfa,
    parse_custom_transitions,
    simulate_automaton,
)
from core.dfa import DFA
from core.languages import DEFAULT_ALPHABETS, REFERENCE_LANGUAGES, ReferenceLanguage, get_reference_language
from core.nfa import EPSILON, NFA
from core.reference_machines import REFERENCE_DFAS, build_third_from_end_a_nfa, get_reference_dfa

__all__ = [
    "DFA",
    "EPSILON",
    "NFA",
    "DEFAULT_ALPHABETS",
    "REFERENCE_DFAS",
    "REFERENCE_LANGUAGES",
    "ReferenceLanguage",
    "architect_automata",
    "are_equivalent",
    "build_third_from_end_a_nfa",
    "get_reference_dfa",
    "get_reference_language",
    "minimize_dfa",
    "nfa_remove_epsilon",
    "nfa_to_dfa",
    "parse_custom_transitions",
    "simulate_automaton",
]
