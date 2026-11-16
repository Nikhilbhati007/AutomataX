"""Deterministic Finite Automaton (DFA) representation and simulation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class DFA:
    """Deterministic Finite Automaton supporting total and partial transition tables.

    Attributes:
        states: Set of state identifiers.
        alphabet: Ordered tuple of input symbols (each a non-empty string).
        transitions: Mapping ``state -> {symbol -> next_state}``.
        start: Start state identifier (must be in ``states``).
        accept_states: Set of accepting/final state identifiers.
    """

    states: frozenset[str]
    alphabet: tuple[str, ...]
    transitions: dict[str, dict[str, str]]
    start: str
    accept_states: frozenset[str]

    def __init__(
        self,
        states: Iterable[str],
        alphabet: Iterable[str],
        transitions: Mapping[str, Mapping[str, str]],
        start: str,
        accept_states: Iterable[str],
    ) -> None:
        state_set = frozenset(states)
        if not state_set:
            raise ValueError("DFA must have at least one state.")

        alpha_tuple = tuple(alphabet)
        if not alpha_tuple:
            raise ValueError("DFA alphabet must not be empty.")
        if len(set(alpha_tuple)) != len(alpha_tuple):
            raise ValueError(f"DFA alphabet contains duplicate symbols: {alpha_tuple}")
        if "" in alpha_tuple:
            raise ValueError("DFA alphabet must not contain the empty string.")

        if start not in state_set:
            raise ValueError(f"Start state {start!r} is not in states.")

        accept_set = frozenset(accept_states)
        unknown_accept = accept_set - state_set
        if unknown_accept:
            raise ValueError(f"Accept states {sorted(unknown_accept)} are not in states.")

        allowed_symbols = set(alpha_tuple)
        normalized_transitions: dict[str, dict[str, str]] = {s: {} for s in state_set}
        for src, edges in transitions.items():
            if src not in state_set:
                raise ValueError(f"Transition source state {src!r} is not in states.")
            for sym, dst in edges.items():
                if sym not in allowed_symbols:
                    raise ValueError(
                        f"Transition symbol {sym!r} from {src!r} is not in alphabet {alpha_tuple}."
                    )
                if dst not in state_set:
                    raise ValueError(
                        f"Transition target state {dst!r} for ({src!r}, {sym!r}) is not in states."
                    )
                normalized_transitions[src][sym] = dst

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

    def step(self, state: str, symbol: str) -> str | None:
        """Return the next state for `(state, symbol)`, or None if undefined."""
        return self.transitions.get(state, {}).get(symbol)

    def accepts(self, s: str) -> tuple[bool, list[str]]:
        """Simulate the DFA on `s` and return `(accepted, execution_path)`.

        For a complete DFA, `execution_path` has length `len(s) + 1`, beginning
        with `self.start`. For a partial DFA that encounters a missing transition,
        simulation stops early and returns `(False, path_so_far)`.
        """
        self.validate_string(s)
        current = self.start
        path = [current]
        for ch in s:
            nxt = self.step(current, ch)
            if nxt is None:
                return False, path
            current = nxt
            path.append(current)
        return current in self.accept_states, path

    def matches(self, s: str) -> bool:
        """Return True iff `s` is accepted by this DFA."""
        accepted, _ = self.accepts(s)
        return accepted

    def is_complete(self) -> bool:
        """Return True iff every `(state, symbol)` pair has a defined transition."""
        return all(
            sym in self.transitions[state]
            for state in self.states
            for sym in self.alphabet
        )

    def complete(self, sink_name: str | None = None) -> DFA:
        """Return an equivalent total DFA, adding a dead sink state only if needed."""
        if self.is_complete():
            return self

        if sink_name is None:
            candidate = "__sink__"
            idx = 0
            while candidate in self.states:
                idx += 1
                candidate = f"__sink_{idx}__"
            sink = candidate
        else:
            if sink_name in self.states:
                raise ValueError(f"Sink state name {sink_name!r} already exists in states.")
            sink = sink_name

        new_states = self.states | {sink}
        new_transitions: dict[str, dict[str, str]] = {}
        for state in self.states:
            row = dict(self.transitions[state])
            for sym in self.alphabet:
                if sym not in row:
                    row[sym] = sink
            new_transitions[state] = row
        new_transitions[sink] = {sym: sink for sym in self.alphabet}

        return DFA(
            states=new_states,
            alphabet=self.alphabet,
            transitions=new_transitions,
            start=self.start,
            accept_states=self.accept_states,
        )

    def reachable_states(self) -> frozenset[str]:
        """Return all states reachable from `self.start`."""
        visited: set[str] = {self.start}
        queue: deque[str] = deque([self.start])
        while queue:
            state = queue.popleft()
            for sym in self.alphabet:
                nxt = self.step(state, sym)
                if nxt is not None and nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        return frozenset(visited)

    def minimize(self) -> DFA:
        """Return the canonical minimal equivalent DFA."""
        from core.algorithms import minimize_dfa

        return minimize_dfa(self)

    def is_equivalent_to(self, other: DFA) -> tuple[bool, str | None]:
        """Check equivalence with `other`, returning `(True, None)` or `(False, counterexample)`."""
        from core.algorithms import are_equivalent

        return are_equivalent(self, other)

    def to_dict(self) -> dict[str, object]:
        """Serialize the DFA to a JSON-compatible dictionary."""
        return {
            "states": sorted(self.states),
            "alphabet": list(self.alphabet),
            "start": self.start,
            "accept_states": sorted(self.accept_states),
            "transitions": {
                state: {sym: self.transitions[state][sym] for sym in sorted(self.transitions[state])}
                for state in sorted(self.states)
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> DFA:
        """Deserialize a DFA from a dictionary created by `to_dict()`."""
        return cls(
            states=data["states"],  # type: ignore[arg-type]
            alphabet=data["alphabet"],  # type: ignore[arg-type]
            transitions=data["transitions"],  # type: ignore[arg-type]
            start=data["start"],  # type: ignore[arg-type]
            accept_states=data["accept_states"],  # type: ignore[arg-type]
        )

