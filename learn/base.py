"""Common data structures and oracle interfaces for grammatical inference algorithms."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

from core.dfa import DFA


@dataclass(frozen=True)
class LearningStep:
    """A single logged step in an inference algorithm's execution history."""

    step_index: int
    step_type: str  # e.g. "pta_init", "merge", "reject", "promote", "lstar_query", etc.
    description: str
    data: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "step_index": self.step_index,
            "step_type": self.step_type,
            "description": self.description,
            "data": dict(self.data),
        }


@dataclass(frozen=True)
class LearningResult:
    """The outcome of a grammatical inference algorithm run."""

    dfa: DFA
    steps: list[LearningStep]
    algorithm: str
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "algorithm": self.algorithm,
            "dfa": self.dfa.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
            "metadata": dict(self.metadata),
        }


class MembershipOracle(Protocol):
    """Answers membership queries for arbitrary strings."""

    def __call__(self, s: str) -> bool:
        ...


class EquivalenceOracle(Protocol):
    """Answers equivalence queries for a candidate DFA, returning (equivalent, counterexample)."""

    def __call__(self, hypothesis: DFA) -> tuple[bool, str | None]:
        ...


def make_dfa_membership_oracle(target_dfa: DFA) -> MembershipOracle:
    """Create a MembershipOracle backed by a ground-truth DFA."""
    return target_dfa.matches


def make_dfa_equivalence_oracle(target_dfa: DFA) -> EquivalenceOracle:
    """Create an EquivalenceOracle backed by Phase 1's `are_equivalent`."""

    def _oracle(hypothesis: DFA) -> tuple[bool, str | None]:
        return target_dfa.is_equivalent_to(hypothesis)

    return _oracle

