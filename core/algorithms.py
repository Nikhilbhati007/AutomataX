"""Core automata algorithms: subset construction, Hopcroft minimization, equivalence."""

from __future__ import annotations

from collections import deque

from core.dfa import DFA
from core.nfa import NFA


def _format_subset(subset: frozenset[str]) -> str:
    """Format a set of NFA states into a deterministic DFA state label."""
    if not subset:
        return "∅"
    return "{" + ",".join(sorted(subset)) + "}"


def nfa_to_dfa(nfa: NFA) -> DFA:
    """Convert an NFA (with optional ε-transitions) to a total DFA via subset construction."""
    start_subset = nfa.epsilon_closure({nfa.start})
    subset_to_name: dict[frozenset[str], str] = {start_subset: _format_subset(start_subset)}
    queue: deque[frozenset[str]] = deque([start_subset])
    transitions: dict[str, dict[str, str]] = {}
    accept_states: set[str] = set()

    while queue:
        current = queue.popleft()
        current_name = subset_to_name[current]
        if current & nfa.accept_states:
            accept_states.add(current_name)

        transitions[current_name] = {}
        for sym in nfa.alphabet:
            nxt = nfa.epsilon_closure(nfa.move(current, sym))
            if nxt not in subset_to_name:
                subset_to_name[nxt] = _format_subset(nxt)
                queue.append(nxt)
            transitions[current_name][sym] = subset_to_name[nxt]

    return DFA(
        states=subset_to_name.values(),
        alphabet=nfa.alphabet,
        transitions=transitions,
        start=subset_to_name[start_subset],
        accept_states=accept_states,
    )


def _prune_unreachable(dfa: DFA) -> DFA:
    """Return an equivalent DFA containing only states reachable from `dfa.start`."""
    reachable = dfa.reachable_states()
    if reachable == dfa.states:
        return dfa
    pruned_transitions = {
        state: dict(dfa.transitions[state])
        for state in reachable
    }
    return DFA(
        states=reachable,
        alphabet=dfa.alphabet,
        transitions=pruned_transitions,
        start=dfa.start,
        accept_states=dfa.accept_states & reachable,
    )


def minimize_dfa(dfa: DFA) -> DFA:
    """Minimize a DFA using Hopcroft's partition refinement algorithm.

    Unreachable states are pruned first, partial DFAs are completed with a sink
    state, and equivalence classes are renamed canonically (`q0`, `q1`, ...) in
    BFS order from the start state.
    """
    working = _prune_unreachable(dfa).complete()

    accept = working.accept_states
    non_accept = working.states - accept

    # Degenerate case: all reachable states accept or none accept.
    if not accept or not non_accept:
        is_accepting = bool(accept)
        return DFA(
            states={"q0"},
            alphabet=working.alphabet,
            transitions={"q0": {sym: "q0" for sym in working.alphabet}},
            start="q0",
            accept_states={"q0"} if is_accepting else set(),
        )

    # Precompute inverse transition table: inv[target][sym] = set of source states.
    inv: dict[str, dict[str, set[str]]] = {
        state: {sym: set() for sym in working.alphabet} for state in working.states
    }
    for src in working.states:
        for sym in working.alphabet:
            dst = working.transitions[src][sym]
            inv[dst][sym].add(src)

    partitions: list[frozenset[str]] = [accept, non_accept]
    smaller = accept if len(accept) <= len(non_accept) else non_accept
    worklist: deque[frozenset[str]] = deque([smaller])
    in_worklist: set[frozenset[str]] = {smaller}

    while worklist:
        splitter = worklist.popleft()
        in_worklist.discard(splitter)

        for sym in working.alphabet:
            predecessors: set[str] = set()
            for target in splitter:
                predecessors.update(inv[target][sym])
            if not predecessors:
                continue

            next_partitions: list[frozenset[str]] = []
            for block in partitions:
                inter = block & predecessors
                diff = block - predecessors
                if inter and diff:
                    next_partitions.append(inter)
                    next_partitions.append(diff)
                    if block in in_worklist:
                        in_worklist.remove(block)
                        worklist.remove(block)
                        worklist.append(inter)
                        worklist.append(diff)
                        in_worklist.add(inter)
                        in_worklist.add(diff)
                    else:
                        chosen = inter if len(inter) <= len(diff) else diff
                        worklist.append(chosen)
                        in_worklist.add(chosen)
                else:
                    next_partitions.append(block)
            partitions = next_partitions

    state_to_block: dict[str, frozenset[str]] = {}
    for block in partitions:
        for state in block:
            state_to_block[state] = block

    # Assign canonical names q0, q1, ... in deterministic BFS order from start.
    start_block = state_to_block[working.start]
    block_to_name: dict[frozenset[str], str] = {start_block: "q0"}
    bfs_queue: deque[frozenset[str]] = deque([start_block])
    min_transitions: dict[str, dict[str, str]] = {}
    min_accepts: set[str] = set()

    while bfs_queue:
        block = bfs_queue.popleft()
        name = block_to_name[block]
        rep = next(iter(block))
        if rep in working.accept_states:
            min_accepts.add(name)

        min_transitions[name] = {}
        for sym in working.alphabet:
            target_block = state_to_block[working.transitions[rep][sym]]
            if target_block not in block_to_name:
                block_to_name[target_block] = f"q{len(block_to_name)}"
                bfs_queue.append(target_block)
            min_transitions[name][sym] = block_to_name[target_block]

    return DFA(
        states=block_to_name.values(),
        alphabet=working.alphabet,
        transitions=min_transitions,
        start="q0",
        accept_states=min_accepts,
    )


def are_equivalent(dfa1: DFA, dfa2: DFA) -> tuple[bool, str | None]:
    """Check whether two DFAs recognize the exact same language.

    Uses product construction + BFS to return `(True, None)` if equivalent, or
    `(False, counterexample)` with a shortest distinguishing string if not.
    """
    if set(dfa1.alphabet) != set(dfa2.alphabet):
        raise ValueError(
            f"Cannot compare DFAs with different alphabets: {dfa1.alphabet} vs {dfa2.alphabet}."
        )

    d1 = dfa1.complete()
    d2 = dfa2.complete()
    ordered_alphabet = tuple(sorted(d1.alphabet))

    start_pair = (d1.start, d2.start)
    visited: set[tuple[str, str]] = {start_pair}
    queue: deque[tuple[str, str, str]] = deque([(d1.start, d2.start, "")])

    while queue:
        s1, s2, witness = queue.popleft()
        if (s1 in d1.accept_states) != (s2 in d2.accept_states):
            return False, witness

        for sym in ordered_alphabet:
            n1 = d1.transitions[s1][sym]
            n2 = d2.transitions[s2][sym]
            pair = (n1, n2)
            if pair not in visited:
                visited.add(pair)
                queue.append((n1, n2, witness + sym))

    return True, None

