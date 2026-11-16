"""Prefix Tree Acceptor (PTA) and state-merging automaton utilities."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Sequence

from core.dfa import DFA
from data.generator import LabeledExample


@dataclass
class MergeAutomaton:
    """Mutable deterministic state-merging automaton initialized as a PTA.

    State IDs are integers `0..N-1` assigned in canonical shortlex order when
    constructed from a PTA, with `0` always serving as the start state (`""`).
    """

    alphabet: tuple[str, ...]
    start: int
    active: set[int]
    transitions: dict[int, dict[str, int]]
    pos_count: dict[int, int]
    neg_count: dict[int, int]
    prefixes: dict[int, str]

    def copy(self) -> MergeAutomaton:
        """Return a deep copy suitable for tentative merge evaluation."""
        return MergeAutomaton(
            alphabet=self.alphabet,
            start=self.start,
            active=set(self.active),
            transitions={s: dict(edges) for s, edges in self.transitions.items()},
            pos_count=dict(self.pos_count),
            neg_count=dict(self.neg_count),
            prefixes=dict(self.prefixes),
        )

    def blue_fringe(self, red_states: set[int]) -> list[int]:
        """Return sorted active non-red states reachable in one step from `red_states`."""
        fringe: set[int] = set()
        for r in sorted(red_states):
            if r not in self.active:
                continue
            for sym in self.alphabet:
                nxt = self.transitions[r].get(sym)
                if nxt is not None and nxt in self.active and nxt not in red_states:
                    fringe.add(nxt)
        return sorted(fringe)

    def evidence_score(self) -> int:
        """Compute total label-overlap evidence across all active states."""
        score = 0
        for s in self.active:
            p = self.pos_count.get(s, 0)
            n = self.neg_count.get(s, 0)
            if p > 1:
                score += p - 1
            if n > 1:
                score += n - 1
        return score

    def try_merge(
        self,
        state_a: int,
        state_b: int,
        red_states: set[int] | None = None,
    ) -> tuple[MergeAutomaton, set[int]] | None:
        """Tentatively merge `state_b` into `state_a` with deterministic folding.

        Returns `(merged_automaton, updated_red_states)` if consistent (no state
        gains both positive and negative examples), or `None` if inconsistent.
        """
        if state_a not in self.active or state_b not in self.active:
            return None

        red = set(red_states) if red_states is not None else set()
        candidate = self.copy()
        parent: dict[int, int] = {s: s for s in candidate.active}

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def pick_survivor(u: int, v: int) -> tuple[int, int]:
            # Prefer keeping the start state or an existing red state as representative.
            if u == candidate.start:
                return u, v
            if v == candidate.start:
                return v, u
            u_red = u in red
            v_red = v in red
            if u_red and not v_red:
                return u, v
            if v_red and not u_red:
                return v, u
            return (u, v) if u < v else (v, u)

        queue: deque[tuple[int, int]] = deque([(state_a, state_b)])
        while queue:
            u, v = queue.popleft()
            ru, rv = find(u), find(v)
            if ru == rv:
                continue

            keep, drop = pick_survivor(ru, rv)
            parent[drop] = keep
            candidate.active.discard(drop)

            candidate.pos_count[keep] = candidate.pos_count.get(keep, 0) + candidate.pos_count.pop(
                drop, 0
            )
            candidate.neg_count[keep] = candidate.neg_count.get(keep, 0) + candidate.neg_count.pop(
                drop, 0
            )

            # Fast consistency check: a state cannot both accept (+) and reject (-).
            if candidate.pos_count[keep] > 0 and candidate.neg_count[keep] > 0:
                return None

            drop_edges = candidate.transitions.pop(drop, {})
            keep_edges = candidate.transitions[keep]
            for sym, dst_drop in drop_edges.items():
                resolved_drop = find(dst_drop)
                if sym in keep_edges:
                    resolved_keep = find(keep_edges[sym])
                    if resolved_keep != resolved_drop:
                        queue.append((resolved_keep, resolved_drop))
                else:
                    keep_edges[sym] = resolved_drop

        # Normalize all transition targets to their active union-find representatives.
        for s in candidate.active:
            edges = candidate.transitions[s]
            for sym in list(edges.keys()):
                edges[sym] = find(edges[sym])

        candidate.start = find(candidate.start)
        updated_red = {find(r) for r in red} & candidate.active
        return candidate, updated_red

    def to_dfa(self) -> DFA:
        """Convert the current merged automaton into a `DFA` with `q{id}` state names."""
        ordered_states = sorted(self.active)
        name_of = {s: f"q{s}" for s in ordered_states}
        transitions = {
            name_of[s]: {
                sym: name_of[dst]
                for sym, dst in self.transitions[s].items()
                if dst in self.active
            }
            for s in ordered_states
        }
        accept_states = {
            name_of[s] for s in ordered_states if self.pos_count.get(s, 0) > 0
        }
        return DFA(
            states=name_of.values(),
            alphabet=self.alphabet,
            transitions=transitions,
            start=name_of[self.start],
            accept_states=accept_states,
        )


def _normalize_examples(
    examples: Sequence[LabeledExample | tuple[str, bool]],
    alphabet: Iterable[str] | None,
) -> tuple[tuple[str, ...], list[tuple[str, bool]]]:
    pairs: list[tuple[str, bool]] = []
    seen_symbols: set[str] = set()
    for item in examples:
        if isinstance(item, LabeledExample):
            s, lbl = item.string, bool(item.label)
        else:
            s, lbl = item[0], bool(item[1])
        pairs.append((s, lbl))
        seen_symbols.update(s)

    if alphabet is not None:
        alpha = tuple(alphabet)
    elif seen_symbols:
        alpha = tuple(sorted(seen_symbols))
    else:
        raise ValueError("Cannot infer empty alphabet; pass `alphabet` explicitly.")

    allowed = set(alpha)
    for s, _ in pairs:
        invalid = [ch for ch in s if ch not in allowed]
        if invalid:
            raise ValueError(
                f"Training string {s!r} contains symbols {sorted(set(invalid))} "
                f"outside alphabet {alpha}."
            )
    return alpha, pairs


def build_pta(
    examples: Sequence[LabeledExample | tuple[str, bool]],
    alphabet: Iterable[str] | None = None,
    *,
    strict: bool = True,
) -> MergeAutomaton:
    """Build a Prefix Tree Acceptor (PTA) in shortlex state order from labeled examples.

    Args:
        examples: Sequence of `LabeledExample` or `(string, label)` pairs.
        alphabet: Input alphabet; inferred from `examples` if omitted.
        strict: If True, raise `ValueError` when the same string has conflicting labels.
    """
    alpha, pairs = _normalize_examples(examples, alphabet)
    ordered_alpha = tuple(sorted(alpha))

    # Collect all prefixes and count positive/negative endpoints.
    pos_map: dict[str, int] = {}
    neg_map: dict[str, int] = {}
    prefixes: set[str] = {""}
    for s, lbl in pairs:
        for i in range(len(s) + 1):
            prefixes.add(s[:i])
        if lbl:
            pos_map[s] = pos_map.get(s, 0) + 1
        else:
            neg_map[s] = neg_map.get(s, 0) + 1

    if strict:
        conflicts = sorted(set(pos_map.keys()) & set(neg_map.keys()))
        if conflicts:
            raise ValueError(
                f"Conflicting labels in training data for strings: {conflicts[:5]}"
            )

    # Sort prefixes in canonical shortlex order so BFS state IDs are deterministic.
    alpha_rank = {sym: idx for idx, sym in enumerate(ordered_alpha)}
    sorted_prefixes = sorted(
        prefixes,
        key=lambda p: (len(p), [alpha_rank[ch] for ch in p]),
    )
    prefix_to_id = {p: idx for idx, p in enumerate(sorted_prefixes)}

    active = set(range(len(sorted_prefixes)))
    transitions: dict[int, dict[str, int]] = {i: {} for i in active}
    pos_count: dict[int, int] = {}
    neg_count: dict[int, int] = {}
    id_to_prefix: dict[int, str] = {}

    for p, pid in prefix_to_id.items():
        id_to_prefix[pid] = p
        pos_count[pid] = pos_map.get(p, 0)
        neg_count[pid] = neg_map.get(p, 0)
        if p:
            parent_id = prefix_to_id[p[:-1]]
            transitions[parent_id][p[-1]] = pid

    return MergeAutomaton(
        alphabet=alpha,
        start=0,
        active=active,
        transitions=transitions,
        pos_count=pos_count,
        neg_count=neg_count,
        prefixes=id_to_prefix,
    )

