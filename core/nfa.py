"""Nondeterministic Finite Automaton (NFA) with epsilon transitions."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Mapping

if TYPE_CHECKING:
    from core.dfa import DFA

EPSILON = ""


@dataclass(frozen=True)
class NFA:
    """Nondeterministic Finite Automaton supporting ε-transitions.

    Use ``EPSILON`` (``""``) as the transition symbol key for ε-transitions.
    """

    states: frozenset[str]
    alphabet: tuple[str, ...]
    transitions: dict[str, dict[str, frozenset[str]]]
    start: str
    accept_states: frozenset[str]

    def __init__(
        self,
        states: Iterable[str],
        alphabet: Iterable[str],
        transitions: Mapping[str, Mapping[str, Iterable[str]]],
        start: str,
        accept_states: Iterable[str],
    ) -> None:
        state_set = frozenset(states)
        if not state_set:
            raise ValueError("NFA must have at least one state.")

        alpha_tuple = tuple(alphabet)
        if not alpha_tuple:
            raise ValueError("NFA alphabet must not be empty.")
        if len(set(alpha_tuple)) != len(alpha_tuple):
            raise ValueError(f"NFA alphabet contains duplicate symbols: {alpha_tuple}")
        if EPSILON in alpha_tuple:
            raise ValueError("NFA alphabet must not contain EPSILON ('').")

        if start not in state_set:
            raise ValueError(f"Start state {start!r} is not in states.")

        accept_set = frozenset(accept_states)
        unknown_accept = accept_set - state_set
        if unknown_accept:
            raise ValueError(f"Accept states {sorted(unknown_accept)} are not in states.")

        allowed_keys = set(alpha_tuple) | {EPSILON}
        normalized_transitions: dict[str, dict[str, frozenset[str]]] = {s: {} for s in state_set}
        for src, edges in transitions.items():
            if src not in state_set:
                raise ValueError(f"Transition source state {src!r} is not in states.")
            for sym, targets in edges.items():
                if sym not in allowed_keys:
                    raise ValueError(
                        f"Transition symbol {sym!r} from {src!r} is not in alphabet {alpha_tuple} or EPSILON."
                    )
                target_set = frozenset(targets)
                unknown_targets = target_set - state_set
                if unknown_targets:
                    raise ValueError(
                        f"Transition target states {sorted(unknown_targets)} for ({src!r}, {sym!r}) "
                        f"are not in states."
                    )
                if target_set:
                    normalized_transitions[src][sym] = target_set

        object.__setattr__(self, "states", state_set)
        object.__setattr__(self, "alphabet", alpha_tuple)
        object.__setattr__(self, "transitions", normalized_transitions)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "accept_states", accept_set)

    def validate_string(self, s: str) -> None:
        """Raise ValueError if any character in `s` is outside `self.alphabet`."""
        allowed = set(self.alphabet)
        invalid = sorted({ch for ch in s if ch not in allowed})
        if invalid:
            raise ValueError(
                f"Input string {s!r} contains symbols {invalid} outside alphabet {self.alphabet}."
            )

    def epsilon_closure(self, state_set: Iterable[str]) -> frozenset[str]:
        """Return all states reachable from `state_set` via zero or more ε-transitions."""
        closure = set(state_set)
        queue: deque[str] = deque(closure)
        while queue:
            state = queue.popleft()
            for nxt in self.transitions.get(state, {}).get(EPSILON, frozenset()):
                if nxt not in closure:
                    closure.add(nxt)
                    queue.append(nxt)
        return frozenset(closure)

    def move(self, state_set: Iterable[str], symbol: str) -> frozenset[str]:
        """Return direct target states on `symbol` (before ε-closure)."""
        next_states: set[str] = set()
        for state in state_set:
            next_states.update(self.transitions.get(state, {}).get(symbol, frozenset()))
        return frozenset(next_states)

    def step(self, state_set: Iterable[str], symbol: str) -> frozenset[str]:
        """Advance `state_set` on `symbol`, applying ε-closure before and after."""
        return self.epsilon_closure(self.move(self.epsilon_closure(state_set), symbol))

    def accepts(self, s: str) -> tuple[bool, list[frozenset[str]]]:
        """Simulate the NFA via subset tracking and return `(accepted, state_set_path)`."""
        self.validate_string(s)
        current = self.epsilon_closure({self.start})
        path = [current]
        for ch in s:
            current = self.epsilon_closure(self.move(current, ch))
            path.append(current)
        return bool(current & self.accept_states), path

    def matches(self, s: str) -> bool:
        """Return True iff `s` is accepted by this NFA."""
        accepted, _ = self.accepts(s)
        return accepted

    def to_dfa(self) -> DFA:
        """Convert this NFA to an equivalent DFA via subset construction."""
        from core.algorithms import nfa_to_dfa

        return nfa_to_dfa(self)

    def to_dict(self) -> dict[str, object]:
        """Serialize the NFA to a JSON-compatible dictionary."""
        return {
            "states": sorted(self.states),
            "alphabet": list(self.alphabet),
            "start": self.start,
            "accept_states": sorted(self.accept_states),
            "transitions": {
                state: {
                    sym: sorted(targets)
                    for sym, targets in sorted(self.transitions[state].items())
                }
                for state in sorted(self.states)
            },
        }

