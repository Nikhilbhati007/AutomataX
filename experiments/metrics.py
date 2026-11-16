"""Evaluation metrics for grammatical inference and automata classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from core.dfa import DFA
from data.generator import LabeledExample


@dataclass(frozen=True)
class EvaluationMetrics:
    """Comprehensive performance and structural metrics for a learned DFA."""

    total_examples: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    learned_states: int
    minimal_states: int | None
    is_equivalent: bool | None
    counterexample: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "total_examples": self.total_examples,
            "confusion_matrix": {
                "tp": self.true_positives,
                "tn": self.true_negatives,
                "fp": self.false_positives,
                "fn": self.false_negatives,
            },
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "learned_states": self.learned_states,
            "minimal_states": self.minimal_states,
            "is_equivalent": self.is_equivalent,
            "counterexample": self.counterexample,
        }


def evaluate_dfa(
    hypothesis: DFA,
    test_set: Sequence[LabeledExample | tuple[str, bool]],
    reference_dfa: DFA | None = None,
) -> EvaluationMetrics:
    """Evaluate a candidate DFA on a test set, optionally checking exact equivalence."""
    tp = tn = fp = fn = 0

    for item in test_set:
        if isinstance(item, LabeledExample):
            s, true_label = item.string, item.true_label
        else:
            s, true_label = item[0], bool(item[1])

        pred = hypothesis.matches(s)
        if pred and true_label:
            tp += 1
        elif not pred and not true_label:
            tn += 1
        elif pred and not true_label:
            fp += 1
        else:
            fn += 1

    total = tp + tn + fp + fn
    acc = (tp + tn) / total if total > 0 else 0.0
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

    min_states: int | None = None
    is_equiv: bool | None = None
    cex: str | None = None

    if reference_dfa is not None:
        min_states = len(reference_dfa.minimize().states)
        try:
            is_equiv, cex = reference_dfa.is_equivalent_to(hypothesis)
        except ValueError:
            # Different alphabets
            is_equiv, cex = False, None

    return EvaluationMetrics(
        total_examples=total,
        true_positives=tp,
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn,
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1_score=f1,
        learned_states=len(hypothesis.states),
        minimal_states=min_states,
        is_equivalent=is_equiv,
        counterexample=cex,
    )

