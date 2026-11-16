"""Phase 4 unit tests for evaluation metrics, benchmarks, ML baselines, and clustering."""

from core import get_reference_dfa, get_reference_language
from data import generate_train_test_split
from experiments import (
    DecisionTreeBaseline,
    cluster_strings_by_end_state,
    cluster_strings_by_ngrams,
    evaluate_dfa,
    run_active_vs_random_study,
    run_diversity_study,
    run_learning_curve,
    run_noise_study,
)
from learn import learn_edsm


def test_evaluate_dfa_metrics_and_equivalence():
    target = get_reference_dfa("ends_with_ab")
    split = generate_train_test_split(target, train_size=30, test_size=40, seed=11)

    metrics_exact = evaluate_dfa(target, split.test, reference_dfa=target)
    assert metrics_exact.accuracy == 1.0
    assert metrics_exact.f1_score == 1.0
    assert metrics_exact.is_equivalent is True
    assert metrics_exact.counterexample is None
    assert metrics_exact.learned_states == 3
    assert metrics_exact.minimal_states == 3

    # Compare against a trivial wrong machine (only start state accepting "").
    wrong = get_reference_dfa("even_ones")  # different alphabet -> is_equivalent False
    metrics_diff = evaluate_dfa(target, split.test, reference_dfa=wrong)
    assert metrics_diff.is_equivalent is False


def test_learning_curve_improves_with_more_data():
    report = run_learning_curve(
        get_reference_language("ends_with_ab"),
        train_sizes=(12, 60),
        learners=("edsm", "rpni"),
        seeds=(0, 1, 2),
        test_size=80,
    )
    assert report.minimal_true_states == 3
    edsm_pts = [p for p in report.points if p.learner == "edsm"]
    assert len(edsm_pts) == 2
    assert edsm_pts[1].mean_accuracy >= edsm_pts[0].mean_accuracy
    serialized = report.to_dict()
    assert len(serialized["points"]) == 4


def test_noise_study_produces_expected_rates():
    report = run_noise_study(
        get_reference_language("even_ones"),
        noise_rates=(0.0, 0.05, 0.10, 0.20),
        learners=("rpni", "edsm"),
        seeds=(0, 1),
        train_size=50,
        test_size=60,
    )
    assert report.minimal_true_states == 2
    assert len(report.points) == 8
    edsm_0 = next(p for p in report.points if p.learner == "edsm" and p.noise_rate == 0.0)
    assert edsm_0.mean_accuracy > 0.8


def test_diversity_study_characteristic_vs_random():
    report = run_diversity_study(
        get_reference_language("no_aa"),
        learner="edsm",
        random_multipliers=(1, 2),
        seeds=(0, 1),
        test_size=60,
    )
    assert report.minimal_true_states == 3
    assert report.characteristic_accuracy == 1.0
    assert report.characteristic_equivalent is True
    assert report.characteristic_states == 3
    assert len(report.random_samples) == 2


def test_decision_tree_baseline_learns_pattern_and_compares_with_edsm():
    target = get_reference_dfa("ends_with_ab")
    split = generate_train_test_split(
        target,
        train_min_length=0,
        train_max_length=6,
        train_size=60,
        test_min_length=7,
        test_max_length=10,
        test_size=60,
        seed=5,
    )

    dt = DecisionTreeBaseline(alphabet=target.alphabet, max_depth=5).fit(split.train)
    dt_eval = dt.evaluate(split.test)
    assert 0.0 <= dt_eval["accuracy"] <= 1.0
    # Because DT uses positional end_m1_b / end_m2_a features, it generalizes decently on ends_with_ab.
    assert dt_eval["accuracy"] >= 0.8

    edsm_res = learn_edsm(split.train, alphabet=target.alphabet)
    edsm_eval = evaluate_dfa(edsm_res.dfa, split.test, reference_dfa=target)
    assert edsm_eval.accuracy >= dt_eval["accuracy"] - 0.1


def test_active_vs_random_learning_study():
    comp = run_active_vs_random_study(
        get_reference_language("ends_with_ab"),
        initial_size=6,
        batch_size=6,
        rounds=4,
        pool_size=80,
        test_size=60,
        seed=42,
    )
    assert len(comp.query_budgets) == 5
    assert comp.query_budgets == [6, 12, 18, 24, 30]
    assert len(comp.active_accuracies) == 5
    assert len(comp.random_accuracies) == 5
    assert comp.active_accuracies[-1] >= comp.active_accuracies[0]


def test_clustering_by_end_state_and_ngrams():
    target = get_reference_dfa("ends_with_ab")
    strings = ["", "a", "b", "aa", "ab", "ba", "bb", "aab", "bab"]

    by_state = cluster_strings_by_end_state(target, strings)
    assert set(by_state.keys()) == {"q0", "q_a", "q_ab"}
    assert set(by_state["q_ab"]["examples"]) == {"ab", "aab", "bab"}  # type: ignore[arg-type]
    assert by_state["q_ab"]["accepting"] is True

    by_ngrams = cluster_strings_by_ngrams(strings, n=2, k=3, seed=7)
    clustered_all = [s for group in by_ngrams.values() for s in group]
    assert set(clustered_all) == set(strings)

