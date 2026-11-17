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


def nfa_remove_epsilon(nfa: NFA) -> NFA:
    """Convert an ε-NFA to an equivalent standard NFA without ε-transitions."""
    from core.nfa import EPSILON

    alpha = tuple(nfa.alphabet)
    new_transitions: dict[str, dict[str, set[str]]] = {q: {} for q in nfa.states}
    new_accept: set[str] = set()

    for q in nfa.states:
        closure_q = nfa.epsilon_closure({q})
        if closure_q & nfa.accept_states:
            new_accept.add(q)
        for sym in alpha:
            targets: set[str] = set()
            for p in closure_q:
                targets.update(nfa.transitions.get(p, {}).get(sym, set()))
            if targets:
                new_transitions[q][sym] = set(nfa.epsilon_closure(targets))

    # Prune unreachable states from nfa.start
    reachable: set[str] = {nfa.start}
    queue: list[str] = [nfa.start]
    while queue:
        curr = queue.pop(0)
        for sym, tgs in new_transitions.get(curr, {}).items():
            for t in tgs:
                if t not in reachable:
                    reachable.add(t)
                    queue.append(t)

    pruned_transitions: dict[str, dict[str, set[str]]] = {}
    for s in reachable:
        pruned_transitions[s] = {}
        for sym, tgs in new_transitions.get(s, {}).items():
            valid_tgs = tgs & reachable
            if valid_tgs:
                pruned_transitions[s][sym] = valid_tgs

    return NFA(
        states=reachable,
        alphabet=alpha,
        transitions=pruned_transitions,
        start=nfa.start,
        accept_states=new_accept & reachable,
    )


def parse_custom_transitions(text: str, alphabet: tuple[str, ...] | None = None) -> NFA:
    """Parse custom user-defined transitions into an NFA or DFA.

    Supported syntax:
      # start: q0
      # accept: q2, q3
      q0, a -> q1
      q0, b -> q0
      q1, ε -> q2 (or q1, eps -> q2)
      q1, a -> q2, q3
    """
    states: set[str] = set()
    transitions: dict[str, dict[str, set[str]]] = {}
    start: str | None = None
    accept_states: set[str] = set()
    inferred_alpha: set[str] = set()

    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            if ":" in line:
                k, v = line.lstrip("#").split(":", 1)
                k = k.strip().lower()
                vals = [x.strip() for x in v.split(",") if x.strip()]
                if k == "start" and vals:
                    start = vals[0]
                elif k in ("accept", "accepting", "finals", "final"):
                    accept_states.update(vals)
            continue

        if "->" in line:
            left, right = line.split("->", 1)
            parts = [p.strip() for p in left.split(",") if p.strip()]
            if len(parts) == 2:
                src, sym = parts
            elif len(parts) == 1:
                src = parts[0]
                sym = ""
            else:
                continue

            dests = [d.strip() for d in right.split(",") if d.strip()]
            clean_dests: list[str] = []
            for d in dests:
                if d.endswith("*") or "(accept)" in d.lower():
                    clean_d = d.rstrip("*").replace("(accept)", "").strip()
                    accept_states.add(clean_d)
                    clean_dests.append(clean_d)
                else:
                    clean_dests.append(d)

            if src.endswith("*"):
                src = src.rstrip("*")
                accept_states.add(src)

            sym = "" if sym.lower() in ("ε", "eps", "epsilon", "") else sym
            if sym != "":
                inferred_alpha.add(sym)

            states.add(src)
            states.update(clean_dests)
            if start is None:
                start = src

            transitions.setdefault(src, {}).setdefault(sym, set()).update(clean_dests)

    if not states:
        raise ValueError("No valid states or transitions found in input.")

    final_alpha = alphabet if alphabet is not None else tuple(sorted(inferred_alpha))
    if not final_alpha:
        final_alpha = ("a", "b")

    start_state = start or sorted(states)[0]
    return NFA(
        states=states,
        alphabet=final_alpha,
        transitions=transitions,
        start=start_state,
        accept_states=accept_states,
    )


def architect_automata(
    pattern: str | None = None,
    custom_text: str | None = None,
    alphabet: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Compile a pattern or custom transitions into 4 inter-changeable representations."""
    from data.regex import infer_regex_alphabet, regex_to_nfa

    if pattern is not None and pattern.strip():
        pat = pattern.strip()
        alpha = tuple(alphabet) if alphabet is not None else infer_regex_alphabet(pat)
        eps_nfa = regex_to_nfa(pat, alphabet=alpha)
    elif custom_text is not None and custom_text.strip():
        eps_nfa = parse_custom_transitions(custom_text, alphabet=alphabet)
    else:
        raise ValueError("Must provide either a regex pattern or custom transition text.")

    has_epsilon = any("" in eps_nfa.transitions.get(s, {}) for s in eps_nfa.states)
    if has_epsilon:
        nfa_no_eps = nfa_remove_epsilon(eps_nfa)
    else:
        nfa_no_eps = eps_nfa

    dfa_raw = eps_nfa.to_dfa()
    dfa_min = dfa_raw.minimize()

    telemetry = {
        "pattern": pattern,
        "alphabet": list(eps_nfa.alphabet),
        "eps_nfa_states": len(eps_nfa.states),
        "eps_nfa_transitions": sum(
            len(tg) for src in eps_nfa.transitions.values() for tg in src.values()
        ),
        "eps_nfa_epsilon_count": sum(
            len(src.get("", set())) for src in eps_nfa.transitions.values()
        ),
        "nfa_states": len(nfa_no_eps.states),
        "nfa_transitions": sum(
            len(tg) for src in nfa_no_eps.transitions.values() for tg in src.values()
        ),
        "dfa_states": len(dfa_raw.states),
        "dfa_transitions": sum(len(src) for src in dfa_raw.transitions.values()),
        "min_dfa_states": len(dfa_min.states),
        "min_dfa_transitions": sum(len(src) for src in dfa_min.transitions.values()),
        "has_epsilon": has_epsilon,
    }

    return {
        "eps_nfa": eps_nfa,
        "nfa": nfa_no_eps,
        "dfa": dfa_raw,
        "min_dfa": dfa_min,
        "telemetry": telemetry,
    }


def simulate_automaton(machine: NFA | DFA, test_string: str) -> dict[str, object]:
    """Simulate a string on an NFA or DFA, recording the step-by-step trace."""
    if isinstance(machine, DFA):
        for ch in test_string:
            if ch not in machine.alphabet:
                raise ValueError(f"Symbol {ch!r} is outside alphabet {machine.alphabet}.")
        accepted, state_path = machine.accepts(test_string)
        steps = []
        for i, st in enumerate(state_path):
            sym = test_string[i - 1] if i > 0 else None
            steps.append({
                "step": i,
                "symbol": sym,
                "current_state": st,
                "active_states": [st],
                "is_accept": st in machine.accept_states,
            })
        return {
            "accepted": accepted,
            "string": test_string,
            "is_nfa": False,
            "path": state_path,
            "steps": steps,
        }
    elif isinstance(machine, NFA):
        for ch in test_string:
            if ch not in machine.alphabet:
                raise ValueError(f"Symbol {ch!r} is outside alphabet {machine.alphabet}.")
        accepted, set_path = machine.accepts(test_string)
        steps = []
        for i, s_set in enumerate(set_path):
            sym = test_string[i - 1] if i > 0 else None
            sorted_set = sorted(s_set)
            steps.append({
                "step": i,
                "symbol": sym,
                "active_states": sorted_set,
                "has_accept": bool(s_set & machine.accept_states),
            })
        return {
            "accepted": accepted,
            "string": test_string,
            "is_nfa": True,
            "path": [sorted(s) for s in set_path],
            "steps": steps,
        }
    else:
        raise TypeError(f"Unknown machine type: {type(machine)}")

