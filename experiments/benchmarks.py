"""Experiment runners: learning curves, noise sensitivity, and diversity studies."""

from __future__ import annotations

from dataclasses import dataclass, field
import statistics
from typing import Iterable, Literal, Sequence

from core.dfa import DFA
from data.generator import (
    SamplingMode,
    TargetSpec,
    generate_characteristic_sample,
    generate_dataset,
    resolve_target_dfa,
)
from experiments.metrics import evaluate_dfa
from learn.edsm import learn_edsm
from learn.rpni import learn_rpni

LearnerName = Literal["edsm", "rpni"]


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return float(values[0]), 0.0
    return float(statistics.mean(values)), float(statistics.stdev(values))


def _run_learner(learner: LearnerName, examples, alphabet: tuple[str, ...]) -> DFA:
    if learner == "edsm":
        return learn_edsm(examples, alphabet=alphabet, record_rejects=False).dfa
    if learner == "rpni":
        return learn_rpni(examples, alphabet=alphabet, record_rejects=False).dfa
    raise ValueError(f"Unknown learner {learner!r}. Expected 'edsm' or 'rpni'.")


@dataclass(frozen=True)
class LearningCurvePoint:
    """Aggregated metrics for one training set size across seeds."""

    train_size: int
    learner: str
    mean_accuracy: float
    std_accuracy: float
    mean_f1: float
    mean_states: float
    std_states: float
    equivalence_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "train_size": self.train_size,
            "learner": self.learner,
            "mean_accuracy": round(self.mean_accuracy, 4),
            "std_accuracy": round(self.std_accuracy, 4),
            "mean_f1": round(self.mean_f1, 4),
            "mean_states": round(self.mean_states, 2),
            "std_states": round(self.std_states, 2),
            "equivalence_rate": round(self.equivalence_rate, 4),
        }


@dataclass(frozen=True)
class LearningCurveReport:
    """Complete learning curve experiment across sizes and learners."""

    minimal_true_states: int
    points: list[LearningCurvePoint] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "minimal_true_states": self.minimal_true_states,
            "points": [p.to_dict() for p in self.points],
        }


def run_learning_curve(
    target: TargetSpec,
    *,
    train_sizes: Sequence[int] = (10, 20, 40, 80, 120),
    learners: Sequence[LearnerName] = ("edsm", "rpni"),
    seeds: Sequence[int] = (0, 1, 2, 3, 4),
    train_min_length: int = 0,
    train_max_length: int = 7,
    test_min_length: int = 8,
    test_max_length: int = 11,
    test_size: int = 150,
    sampling_mode: SamplingMode = "length_stratified",
    alphabet: Iterable[str] | None = None,
) -> LearningCurveReport:
    """Evaluate test accuracy and learned state counts across increasing training sizes."""
    ref_dfa = resolve_target_dfa(target, alphabet=alphabet).minimize()
    min_states = len(ref_dfa.states)

    # Fixed shared clean test set on longer unseen strings.
    test_set = generate_dataset(
        ref_dfa,
        min_length=test_min_length,
        max_length=test_max_length,
        size=test_size,
        positive_ratio=0.5,
        sampling_mode="uniform",
        seed=9999,
    )
    test_strings = {ex.string for ex in test_set}

    points: list[LearningCurvePoint] = []
    for learner in learners:
        for size in train_sizes:
            accs: list[float] = []
            f1s: list[float] = []
            states: list[float] = []
            equivs: list[float] = []

            for seed in seeds:
                train_set = generate_dataset(
                    ref_dfa,
                    min_length=train_min_length,
                    max_length=train_max_length,
                    size=size,
                    positive_ratio=0.5,
                    sampling_mode=sampling_mode,
                    exclude=test_strings,
                    seed=seed,
                )
                learned = _run_learner(learner, train_set, ref_dfa.alphabet)
                metrics = evaluate_dfa(learned, test_set, reference_dfa=ref_dfa)
                accs.append(metrics.accuracy)
                f1s.append(metrics.f1_score)
                states.append(float(metrics.learned_states))
                equivs.append(1.0 if metrics.is_equivalent else 0.0)

            mean_acc, std_acc = _mean_std(accs)
            mean_f1, _ = _mean_std(f1s)
            mean_st, std_st = _mean_std(states)
            mean_eq, _ = _mean_std(equivs)

            points.append(
                LearningCurvePoint(
                    train_size=size,
                    learner=learner,
                    mean_accuracy=mean_acc,
                    std_accuracy=std_acc,
                    mean_f1=mean_f1,
                    mean_states=mean_st,
                    std_states=std_st,
                    equivalence_rate=mean_eq,
                )
            )

    return LearningCurveReport(minimal_true_states=min_states, points=points)


@dataclass(frozen=True)
class NoiseStudyPoint:
    """Aggregated metrics for one noise level and learner."""

    noise_rate: float
    learner: str
    mean_accuracy: float
    std_accuracy: float
    mean_f1: float
    mean_states: float
    std_states: float

    def to_dict(self) -> dict[str, object]:
        return {
            "noise_rate": self.noise_rate,
            "learner": self.learner,
            "mean_accuracy": round(self.mean_accuracy, 4),
            "std_accuracy": round(self.std_accuracy, 4),
            "mean_f1": round(self.mean_f1, 4),
            "mean_states": round(self.mean_states, 2),
            "std_states": round(self.std_states, 2),
        }


@dataclass(frozen=True)
class NoiseStudyReport:
    """Results comparing RPNI vs EDSM under increasing label flip rates."""

    minimal_true_states: int
    train_size: int
    points: list[NoiseStudyPoint] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "minimal_true_states": self.minimal_true_states,
            "train_size": self.train_size,
            "points": [p.to_dict() for p in self.points],
        }


def run_noise_study(
    target: TargetSpec,
    *,
    noise_rates: Sequence[float] = (0.0, 0.05, 0.10, 0.20),
    learners: Sequence[LearnerName] = ("rpni", "edsm"),
    seeds: Sequence[int] = (0, 1, 2, 3, 4),
    train_size: int = 80,
    train_min_length: int = 0,
    train_max_length: int = 7,
    test_min_length: int = 8,
    test_max_length: int = 11,
    test_size: int = 150,
    alphabet: Iterable[str] | None = None,
) -> NoiseStudyReport:
    """Compare RPNI and EDSM degradation across label-noise percentages."""
    ref_dfa = resolve_target_dfa(target, alphabet=alphabet).minimize()
    test_set = generate_dataset(
        ref_dfa,
        min_length=test_min_length,
        max_length=test_max_length,
        size=test_size,
        positive_ratio=0.5,
        sampling_mode="uniform",
        seed=8888,
    )
    test_strings = {ex.string for ex in test_set}

    points: list[NoiseStudyPoint] = []
    for learner in learners:
        for noise in noise_rates:
            accs: list[float] = []
            f1s: list[float] = []
            states: list[float] = []

            for seed in seeds:
                train_set = generate_dataset(
                    ref_dfa,
                    min_length=train_min_length,
                    max_length=train_max_length,
                    size=train_size,
                    positive_ratio=0.5,
                    noise_rate=noise,
                    sampling_mode="length_stratified",
                    exclude=test_strings,
                    seed=seed,
                )
                learned = _run_learner(learner, train_set, ref_dfa.alphabet)
                metrics = evaluate_dfa(learned, test_set, reference_dfa=ref_dfa)
                accs.append(metrics.accuracy)
                f1s.append(metrics.f1_score)
                states.append(float(metrics.learned_states))

            mean_acc, std_acc = _mean_std(accs)
            mean_f1, _ = _mean_std(f1s)
            mean_st, std_st = _mean_std(states)
            points.append(
                NoiseStudyPoint(
                    noise_rate=noise,
                    learner=learner,
                    mean_accuracy=mean_acc,
                    std_accuracy=std_acc,
                    mean_f1=mean_f1,
                    mean_states=mean_st,
                    std_states=std_st,
                )
            )

    return NoiseStudyReport(
        minimal_true_states=len(ref_dfa.states),
        train_size=train_size,
        points=points,
    )


@dataclass(frozen=True)
class DiversityComparisonReport:
    """Comparison of a compact characteristic sample vs. larger random samples."""

    minimal_true_states: int
    characteristic_size: int
    characteristic_accuracy: float
    characteristic_states: int
    characteristic_equivalent: bool
    random_samples: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return {
            "minimal_true_states": self.minimal_true_states,
            "characteristic": {
                "size": self.characteristic_size,
                "accuracy": round(self.characteristic_accuracy, 4),
                "states": self.characteristic_states,
                "is_equivalent": self.characteristic_equivalent,
            },
            "random_samples": list(self.random_samples),
        }


def run_diversity_study(
    target: TargetSpec,
    *,
    learner: LearnerName = "edsm",
    random_multipliers: Sequence[int] = (1, 2, 4),
    seeds: Sequence[int] = (0, 1, 2),
    test_min_length: int = 8,
    test_max_length: int = 11,
    test_size: int = 150,
    alphabet: Iterable[str] | None = None,
) -> DiversityComparisonReport:
    """Compare a small characteristic set against larger random uniform samples."""
    ref_dfa = resolve_target_dfa(target, alphabet=alphabet).minimize()
    char_sample = generate_characteristic_sample(ref_dfa)
    char_strs = {ex.string for ex in char_sample}

    test_set = generate_dataset(
        ref_dfa,
        min_length=test_min_length,
        max_length=test_max_length,
        size=test_size,
        positive_ratio=0.5,
        sampling_mode="uniform",
        exclude=char_strs,
        seed=7777,
    )
    test_strs = {ex.string for ex in test_set}

    char_dfa = _run_learner(learner, char_sample, ref_dfa.alphabet)
    char_metrics = evaluate_dfa(char_dfa, test_set, reference_dfa=ref_dfa)

    random_rows: list[dict[str, object]] = []
    for mult in random_multipliers:
        size = len(char_sample) * mult
        accs: list[float] = []
        states: list[float] = []
        equivs: list[float] = []
        for seed in seeds:
            rand_sample = generate_dataset(
                ref_dfa,
                min_length=0,
                max_length=7,
                size=size,
                positive_ratio=0.5,
                sampling_mode="uniform",
                exclude=test_strs,
                seed=seed,
            )
            rand_dfa = _run_learner(learner, rand_sample, ref_dfa.alphabet)
            m = evaluate_dfa(rand_dfa, test_set, reference_dfa=ref_dfa)
            accs.append(m.accuracy)
            states.append(float(m.learned_states))
            equivs.append(1.0 if m.is_equivalent else 0.0)

        mean_acc, _ = _mean_std(accs)
        mean_st, _ = _mean_std(states)
        mean_eq, _ = _mean_std(equivs)
        random_rows.append(
            {
                "multiplier": mult,
                "size": size,
                "mean_accuracy": round(mean_acc, 4),
                "mean_states": round(mean_st, 2),
                "equivalence_rate": round(mean_eq, 4),
            }
        )

    return DiversityComparisonReport(
        minimal_true_states=len(ref_dfa.states),
        characteristic_size=len(char_sample),
        characteristic_accuracy=char_metrics.accuracy,
        characteristic_states=char_metrics.learned_states,
        characteristic_equivalent=bool(char_metrics.is_equivalent),
        random_samples=random_rows,
    )

