"""Tests for Automata Architect: ε-NFA, NFA, DFA, Hopcroft interchange & simulation."""

from __future__ import annotations

import pytest

from core.algorithms import (
    architect_automata,
    are_equivalent,
    nfa_remove_epsilon,
    parse_custom_transitions,
    simulate_automaton,
)
from core.dfa import DFA
from core.nfa import NFA
from data.regex import regex_to_nfa
from web.api import (
    ArchitectCompileRequest,
    ArchitectSimulateRequest,
    api_architect_compile,
    api_architect_presets,
    api_architect_simulate,
    nfa_to_cytoscape,
)


# ---------------------------------------------------------------------------
# Core Algorithm Tests
# ---------------------------------------------------------------------------

def test_nfa_remove_epsilon_ends_with_ab():
    """Verify that removing epsilon from Thompson NFA preserves language equivalence."""
    pattern = "(a|b)*ab"
    eps_nfa = regex_to_nfa(pattern, alphabet=("a", "b"))
    assert any("" in eps_nfa.transitions.get(s, {}) for s in eps_nfa.states)

    nfa_no_eps = nfa_remove_epsilon(eps_nfa)
    assert not any("" in nfa_no_eps.transitions.get(s, {}) for s in nfa_no_eps.states)

    test_strings = ["", "a", "b", "ab", "aab", "bab", "aba", "abb", "abab", "bbab"]
    for s in test_strings:
        assert eps_nfa.matches(s) == nfa_no_eps.matches(s), f"Mismatch on {s!r}"


def test_nfa_remove_epsilon_contains_00():
    """Verify epsilon removal on binary pattern (0|1)*00(0|1)*."""
    pattern = "(0|1)*00(0|1)*"
    eps_nfa = regex_to_nfa(pattern, alphabet=("0", "1"))
    nfa_no_eps = nfa_remove_epsilon(eps_nfa)

    test_strings = ["00", "100", "0100", "101", "0", "1", "001", "1001", ""]
    for s in test_strings:
        assert eps_nfa.matches(s) == nfa_no_eps.matches(s), f"Mismatch on {s!r}"


def test_parse_custom_transitions():
    """Test parsing custom transition grammar text."""
    custom_text = """
    # start: q0
    # accept: q2
    q0, a -> q1
    q0, b -> q0
    q1, b -> q2
    q1, eps -> q0
    """
    nfa = parse_custom_transitions(custom_text)
    assert "q0" in nfa.states
    assert "q1" in nfa.states
    assert "q2" in nfa.states
    assert nfa.start == "q0"
    assert nfa.accept_states == {"q2"}
    assert nfa.matches("ab")
    assert not nfa.matches("a")


def test_architect_automata_4_way_interchange():
    """Test full 4-stage compilation: eps_nfa, nfa, dfa, min_dfa."""
    res = architect_automata(pattern="a*b+", alphabet=("a", "b"))
    assert "eps_nfa" in res
    assert "nfa" in res
    assert "dfa" in res
    assert "min_dfa" in res

    eps_nfa: NFA = res["eps_nfa"]  # type: ignore[assignment]
    nfa_obj: NFA = res["nfa"]      # type: ignore[assignment]
    dfa_obj: DFA = res["dfa"]      # type: ignore[assignment]
    min_dfa: DFA = res["min_dfa"]  # type: ignore[assignment]

    # Verify language equivalence across all 4 representations
    test_strings = ["b", "ab", "aab", "abb", "a", "ba", ""]
    for s in test_strings:
        v1 = eps_nfa.matches(s)
        v2 = nfa_obj.matches(s)
        v3 = dfa_obj.matches(s)
        v4 = min_dfa.matches(s)
        assert v1 == v2 == v3 == v4, f"Mismatch on {s!r}: {v1}, {v2}, {v3}, {v4}"


def test_simulate_automaton():
    """Test step-by-step simulation on both NFA and DFA."""
    res = architect_automata(pattern="(a|b)*ab", alphabet=("a", "b"))
    eps_nfa = res["eps_nfa"]
    min_dfa = res["min_dfa"]

    # Test positive string "aab"
    sim_nfa = simulate_automaton(eps_nfa, "aab")  # type: ignore[arg-type]
    assert sim_nfa["accepted"] is True
    assert len(sim_nfa["steps"]) == 4

    sim_dfa = simulate_automaton(min_dfa, "aab")  # type: ignore[arg-type]
    assert sim_dfa["accepted"] is True
    assert len(sim_dfa["steps"]) == 4

    # Test negative string "aba"
    sim_dfa_neg = simulate_automaton(min_dfa, "aba")  # type: ignore[arg-type]
    assert sim_dfa_neg["accepted"] is False


def test_nfa_to_cytoscape():
    """Verify nfa_to_cytoscape correctly tags epsilon edges."""
    res = architect_automata(pattern="(a|b)*ab", alphabet=("a", "b"))
    eps_nfa = res["eps_nfa"]
    elements = nfa_to_cytoscape(eps_nfa.to_dict())  # type: ignore[union-attr]

    nodes = [e for e in elements if "source" not in e["data"]]
    edges = [e for e in elements if "source" in e["data"]]
    assert len(nodes) == len(eps_nfa.states)  # type: ignore[union-attr]
    assert len(edges) > 0
    eps_edges = [e for e in edges if e["data"].get("is_epsilon")]
    assert len(eps_edges) > 0


# ---------------------------------------------------------------------------
# API Endpoint Tests (direct function invocation)
# ---------------------------------------------------------------------------

def test_api_architect_presets():
    """Verify preset catalog endpoint."""
    presets = api_architect_presets()
    assert len(presets) >= 5
    ids = [p["id"] for p in presets]
    assert "ends_with_ab" in ids
    assert "contains_00" in ids


def test_api_architect_compile():
    """Verify pattern compilation endpoint."""
    req = ArchitectCompileRequest(pattern="(a|b)*ab", alphabet=["a", "b"])
    data = api_architect_compile(req)
    assert "eps_nfa" in data
    assert "nfa" in data
    assert "dfa" in data
    assert "min_dfa" in data
    assert "telemetry" in data

    assert len(data["eps_nfa"]["cytoscape"]) > 0
    assert len(data["min_dfa"]["cytoscape"]) > 0


def test_api_architect_simulate():
    """Verify simulation endpoint across machine types."""
    # Test on eps_nfa
    req_nfa = ArchitectSimulateRequest(
        machine_type="eps_nfa",
        pattern="(a|b)*ab",
        alphabet=["a", "b"],
        string="aab",
    )
    data_nfa = api_architect_simulate(req_nfa)
    assert data_nfa["accepted"] is True
    assert len(data_nfa["steps"]) == 4

    # Test on min_dfa
    req_dfa = ArchitectSimulateRequest(
        machine_type="min_dfa",
        pattern="(a|b)*ab",
        alphabet=["a", "b"],
        string="aba",
    )
    data_dfa = api_architect_simulate(req_dfa)
    assert data_dfa["accepted"] is False
