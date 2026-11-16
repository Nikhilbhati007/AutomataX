"""Simple regular expression to NFA/DFA compiler using Thompson's construction."""

from __future__ import annotations

from dataclasses import dataclass

from core.dfa import DFA
from core.nfa import EPSILON, NFA


@dataclass
class _Fragment:
    start: str
    end: str
    transitions: dict[str, dict[str, set[str]]]


class _RegexParser:
    """Recursive-descent parser compiling regexes into Thompson NFAs."""

    def __init__(self, pattern: str, alphabet: tuple[str, ...]) -> None:
        self.pattern = pattern
        self.alphabet = alphabet
        self.allowed_symbols = set(alphabet)
        self.pos = 0
        self.counter = 0

    def _new_state(self) -> str:
        name = f"r{self.counter}"
        self.counter += 1
        return name

    def _add_edge(
        self,
        transitions: dict[str, dict[str, set[str]]],
        src: str,
        sym: str,
        dst: str,
    ) -> None:
        transitions.setdefault(src, {}).setdefault(sym, set()).add(dst)

    def _merge_transitions(
        self, *tables: dict[str, dict[str, set[str]]]
    ) -> dict[str, dict[str, set[str]]]:
        merged: dict[str, dict[str, set[str]]] = {}
        for table in tables:
            for src, edges in table.items():
                for sym, targets in edges.items():
                    merged.setdefault(src, {}).setdefault(sym, set()).update(targets)
        return merged

    def _peek(self) -> str | None:
        if self.pos >= len(self.pattern):
            return None
        return self.pattern[self.pos]

    def _consume(self) -> str:
        ch = self.pattern[self.pos]
        self.pos += 1
        return ch

    def parse(self) -> NFA:
        frag = self._parse_expr()
        if self.pos != len(self.pattern):
            raise ValueError(
                f"Unexpected character {self.pattern[self.pos]!r} at position {self.pos} "
                f"in regex {self.pattern!r}."
            )
        all_states = set(frag.transitions.keys()) | {frag.start, frag.end}
        for edges in frag.transitions.values():
            for targets in edges.values():
                all_states.update(targets)

        return NFA(
            states=all_states,
            alphabet=self.alphabet,
            transitions=frag.transitions,
            start=frag.start,
            accept_states={frag.end},
        )

    def _epsilon_fragment(self) -> _Fragment:
        s = self._new_state()
        e = self._new_state()
        transitions: dict[str, dict[str, set[str]]] = {}
        self._add_edge(transitions, s, EPSILON, e)
        return _Fragment(s, e, transitions)

    def _literal_fragment(self, ch: str) -> _Fragment:
        if ch not in self.allowed_symbols:
            raise ValueError(
                f"Regex literal {ch!r} is outside alphabet {self.alphabet}."
            )
        s = self._new_state()
        e = self._new_state()
        transitions: dict[str, dict[str, set[str]]] = {}
        self._add_edge(transitions, s, ch, e)
        return _Fragment(s, e, transitions)

    def _parse_expr(self) -> _Fragment:
        branches = [self._parse_branch()]
        while self._peek() == "|":
            self._consume()
            branches.append(self._parse_branch())

        if len(branches) == 1:
            return branches[0]

        s = self._new_state()
        e = self._new_state()
        transitions = self._merge_transitions(*(b.transitions for b in branches))
        for b in branches:
            self._add_edge(transitions, s, EPSILON, b.start)
            self._add_edge(transitions, b.end, EPSILON, e)
        return _Fragment(s, e, transitions)

    def _parse_branch(self) -> _Fragment:
        pieces: list[_Fragment] = []
        while (ch := self._peek()) is not None and ch not in ("|", ")"):
            pieces.append(self._parse_piece())

        if not pieces:
            return self._epsilon_fragment()

        current = pieces[0]
        for nxt in pieces[1:]:
            transitions = self._merge_transitions(current.transitions, nxt.transitions)
            self._add_edge(transitions, current.end, EPSILON, nxt.start)
            current = _Fragment(current.start, nxt.end, transitions)
        return current

    def _parse_piece(self) -> _Fragment:
        atom = self._parse_atom()
        while (op := self._peek()) in ("*", "+", "?"):
            self._consume()
            if op == "*":
                s = self._new_state()
                e = self._new_state()
                transitions = self._merge_transitions(atom.transitions)
                self._add_edge(transitions, s, EPSILON, atom.start)
                self._add_edge(transitions, s, EPSILON, e)
                self._add_edge(transitions, atom.end, EPSILON, atom.start)
                self._add_edge(transitions, atom.end, EPSILON, e)
                atom = _Fragment(s, e, transitions)
            elif op == "+":
                s = self._new_state()
                e = self._new_state()
                transitions = self._merge_transitions(atom.transitions)
                self._add_edge(transitions, s, EPSILON, atom.start)
                self._add_edge(transitions, atom.end, EPSILON, atom.start)
                self._add_edge(transitions, atom.end, EPSILON, e)
                atom = _Fragment(s, e, transitions)
            elif op == "?":
                s = self._new_state()
                e = self._new_state()
                transitions = self._merge_transitions(atom.transitions)
                self._add_edge(transitions, s, EPSILON, atom.start)
                self._add_edge(transitions, s, EPSILON, e)
                self._add_edge(transitions, atom.end, EPSILON, e)
                atom = _Fragment(s, e, transitions)
        return atom

    def _parse_atom(self) -> _Fragment:
        ch = self._peek()
        if ch is None:
            raise ValueError(f"Unexpected end of regex {self.pattern!r}.")
        if ch in ("*", "+", "?"):
            raise ValueError(
                f"Quantifier {ch!r} missing operand at position {self.pos} in {self.pattern!r}."
            )
        if ch == "(":
            self._consume()
            inner = self._parse_expr()
            if self._peek() != ")":
                raise ValueError(f"Unclosed '(' in regex {self.pattern!r}.")
            self._consume()
            return inner
        if ch == "\\":
            self._consume()
            escaped = self._peek()
            if escaped is None:
                raise ValueError(f"Trailing backslash in regex {self.pattern!r}.")
            return self._literal_fragment(self._consume())
        return self._literal_fragment(self._consume())


def infer_regex_alphabet(pattern: str) -> tuple[str, ...]:
    """Extract sorted unique literal symbols from a regex pattern."""
    meta = {"|", "*", "+", "?", "(", ")"}
    symbols: set[str] = set()
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\":
            if i + 1 >= len(pattern):
                raise ValueError(f"Trailing backslash in regex {pattern!r}.")
            symbols.add(pattern[i + 1])
            i += 2
            continue
        if ch not in meta:
            symbols.add(ch)
        i += 1
    if not symbols:
        raise ValueError(
            f"Cannot infer non-empty alphabet from regex {pattern!r}; pass `alphabet` explicitly."
        )
    return tuple(sorted(symbols))


def regex_to_nfa(pattern: str, alphabet: tuple[str, ...] | None = None) -> NFA:
    """Compile a regular expression (literals, |, *, +, ?, ()) into an NFA."""
    alpha = tuple(alphabet) if alphabet is not None else infer_regex_alphabet(pattern)
    return _RegexParser(pattern, alpha).parse()


def regex_to_dfa(pattern: str, alphabet: tuple[str, ...] | None = None) -> DFA:
    """Compile a regular expression into a minimal DFA."""
    return regex_to_nfa(pattern, alphabet=alphabet).to_dfa().minimize()

