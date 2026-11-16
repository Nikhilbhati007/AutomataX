"""ML baselines (Decision Tree) and active-learning vs. random sampling studies."""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Iterable, Sequence

from core.dfa import DFA
from data.generator import LabeledExample, TargetSpec, generate_dataset, resolve_target_dfa
from experiments.metrics import evaluate_dfa
from learn.edsm import learn_edsm


def extract_string_features(
    s: str,
    alphabet: tuple[str, ...],
    *,
    max_ngram: int = 2,
) -> dict[str, float]:
    """Extract interpretable numeric features (length, counts, n-grams, prefix/suffix)."""
    feats: dict[str, float] = {
        "length": float(len(s)),
        "len_mod_2": float(len(s) % 2),
        "len_mod_3": float(len(s) % 3),
    }

    for sym in alphabet:
        feats[f"count_{sym}"] = float(s.count(sym))
        feats[f"count_{sym}_mod_2"] = float(s.count(sym) % 2)
        feats[f"starts_{sym}"] = 1.0 if s.startswith(sym) else 0.0
        feats[f"ends_{sym}"] = 1.0 if s.endswith(sym) else 0.0

    # Positional end features (useful for suffix languages)
    for k in (1, 2, 3):
        if len(s) >= k:
            for sym in alphabet:
                feats[f"end_m{k}_{sym}"] = 1.0 if s[-k] == sym else 0.0
        else:
            for sym in alphabet:
                feats[f"end_m{k}_{sym}"] = 0.0

    # N-gram counts
    for n in range(1, max_ngram + 1):
        if len(s) >= n:
            for i in range(len(s) - n + 1):
                gram = s[i : i + n]
                key = f"ngram_{gram}"
                feats[key] = feats.get(key, 0.0) + 1.0

    return feats


@dataclass
class _TreeNode:
    prob_pos: float
    feature: str | None = None
    threshold: float | None = None
    left: _TreeNode | None = None
    right: _TreeNode | None = None


class DecisionTreeBaseline:
    """Pure-Python CART binary decision tree classifier over string features."""

    def __init__(
        self,
        alphabet: tuple[str, ...],
        *,
        max_depth: int = 6,
        min_samples_split: int = 2,
        max_ngram: int = 2,
    ) -> None:
        self.alphabet = alphabet
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_ngram = max_ngram
        self.feature_names: list[str] = []
        self.root: _TreeNode | None = None

    @staticmethod
    def _gini(labels: Sequence[bool]) -> float:
        n = len(labels)
        if n == 0:
            return 0.0
        p = sum(1 for y in labels if y) / n
        return 1.0 - (p * p + (1.0 - p) * (1.0 - p))

    def _build(
        self,
        rows: list[dict[str, float]],
        labels: list[bool],
        depth: int,
    ) -> _TreeNode:
        n = len(labels)
        prob_pos = sum(1 for y in labels if y) / n if n > 0 else 0.5
        if (
            depth >= self.max_depth
            or n < self.min_samples_split
            or len(set(labels)) <= 1
        ):
            return _TreeNode(prob_pos=prob_pos)

        parent_gini = self._gini(labels)
        best_gain = 0.0
        best_feat: str | None = None
        best_thresh: float | None = None
        best_split: tuple[list[int], list[int]] | None = None

        for feat in self.feature_names:
            vals = sorted({r.get(feat, 0.0) for r in rows})
            if len(vals) <= 1:
                continue
            thresholds = [(vals[i] + vals[i + 1]) / 2.0 for i in range(len(vals) - 1)]
            for thresh in thresholds:
                left_idx = [i for i, r in enumerate(rows) if r.get(feat, 0.0) <= thresh]
                right_idx = [i for i, r in enumerate(rows) if r.get(feat, 0.0) > thresh]
                if not left_idx or not right_idx:
                    continue

                gini_l = self._gini([labels[i] for i in left_idx])
                gini_r = self._gini([labels[i] for i in right_idx])
                weighted = (len(left_idx) / n) * gini_l + (len(right_idx) / n) * gini_r
                gain = parent_gini - weighted
                if gain > best_gain:
                    best_gain = gain
                    best_feat = feat
                    best_thresh = thresh
                    best_split = (left_idx, right_idx)

        if best_split is None or best_feat is None or best_thresh is None:
            return _TreeNode(prob_pos=prob_pos)

        left_idx, right_idx = best_split
        left_node = self._build(
            [rows[i] for i in left_idx], [labels[i] for i in left_idx], depth + 1
        )
        right_node = self._build(
            [rows[i] for i in right_idx], [labels[i] for i in right_idx], depth + 1
        )
        return _TreeNode(
            prob_pos=prob_pos,
            feature=best_feat,
            threshold=best_thresh,
            left=left_node,
            right=right_node,
        )

    def fit(self, examples: Sequence[LabeledExample | tuple[str, bool]]) -> DecisionTreeBaseline:
        """Fit the decision tree on labeled strings."""
        rows: list[dict[str, float]] = []
        labels: list[bool] = []
        feat_keys: set[str] = set()

        for item in examples:
            s = item.string if isinstance(item, LabeledExample) else item[0]
            lbl = bool(item.label if isinstance(item, LabeledExample) else item[1])
            f = extract_string_features(s, self.alphabet, max_ngram=self.max_ngram)
            rows.append(f)
            labels.append(lbl)
            feat_keys.update(f.keys())

        self.feature_names = sorted(feat_keys)
        self.root = self._build(rows, labels, 0)
        return self

    def predict_proba(self, s: str) -> float:
        """Return estimated P(label=True | s)."""
        if self.root is None:
            raise RuntimeError("DecisionTreeBaseline must be fitted before calling predict.")
        feats = extract_string_features(s, self.alphabet, max_ngram=self.max_ngram)
        node = self.root
        while node.feature is not None and node.threshold is not None:
            val = feats.get(node.feature, 0.0)
            node = node.left if val <= node.threshold else node.right  # type: ignore[assignment]
            assert node is not None
        return node.prob_pos

    def predict(self, s: str) -> bool:
        """Predict binary label for string `s`."""
        return self.predict_proba(s) >= 0.5

    def evaluate(
        self, test_set: Sequence[LabeledExample | tuple[str, bool]]
    ) -> dict[str, float]:
        """Compute accuracy and F1 score on `test_set`."""
        tp = tn = fp = fn = 0
        for item in test_set:
            s = item.string if isinstance(item, LabeledExample) else item[0]
            true_lbl = item.true_label if isinstance(item, LabeledExample) else bool(item[1])
            pred = self.predict(s)
            if pred and true_lbl:
                tp += 1
            elif not pred and not true_lbl:
                tn += 1
            elif pred and not true_lbl:
                fp += 1
            else:
                fn += 1

        total = tp + tn + fp + fn
        acc = (tp + tn) / total if total > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        return {
            "accuracy": round(acc, 4),
            "f1_score": round(f1, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
        }


@dataclass(frozen=True)
class ActiveLearningComparison:
    """Results comparing uncertainty-driven active querying vs. random pool sampling."""

    query_budgets: list[int]
    active_accuracies: list[float]
    random_accuracies: list[float]
    active_states: list[int]
    random_states: list[int]

    def to_dict(self) -> dict[str, object]:
        return {
            "query_budgets": list(self.query_budgets),
            "active_accuracies": [round(a, 4) for a in self.active_accuracies],
            "random_accuracies": [round(a, 4) for a in self.random_accuracies],
            "active_states": list(self.active_states),
            "random_states": list(self.random_states),
        }


def _dfa_uncertainty_score(dfa: DFA, s: str) -> float:
    """Measure how uncertain a learned partial/complete DFA is on string `s`.

    Higher score = more informative to query:
      - 2.0: String hits a missing transition (unexplored region of the hypothesis!)
      - 1.0 + tie-breaker: Hits a state near decision boundaries or shorter unvisited suffix.
    """
    current = dfa.start
    for ch in s:
        nxt = dfa.step(current, ch)
        if nxt is None:
            # Unexplored path in partial DFA -> maximum epistemic uncertainty!
            return 2.0 + 1.0 / (1.0 + len(s))
        current = nxt
    # Known path: prefer shorter strings that probe under-tested transitions or states.
    return 0.5 / (1.0 + len(s))


def run_active_vs_random_study(
    target: TargetSpec,
    *,
    initial_size: int = 6,
    batch_size: int = 6,
    rounds: int = 6,
    pool_size: int = 150,
    test_size: int = 120,
    seed: int = 42,
    alphabet: Iterable[str] | None = None,
) -> ActiveLearningComparison:
    """Compare uncertainty-first pool querying vs. random querying with EDSM."""
    ref_dfa = resolve_target_dfa(target, alphabet=alphabet).minimize()
    rng = random.Random(seed)

    pool_examples = generate_dataset(
        ref_dfa,
        min_length=0,
        max_length=7,
        size=pool_size,
        positive_ratio=0.5,
        sampling_mode="length_stratified",
        seed=seed,
    )
    pool_strs = {ex.string for ex in pool_examples}
    test_set = generate_dataset(
        ref_dfa,
        min_length=6,
        max_length=10,
        size=test_size,
        positive_ratio=0.5,
        sampling_mode="uniform",
        exclude=pool_strs,
        seed=seed + 100,
    )

    # Identical initial seed examples for both strategies (ensure >=1 pos and >=1 neg if available).
    pos_pool = [ex for ex in pool_examples if ex.true_label]
    neg_pool = [ex for ex in pool_examples if not ex.true_label]
    initial: list[LabeledExample] = []
    if pos_pool:
        initial.extend(pos_pool[: max(1, initial_size // 2)])
    if neg_pool:
        initial.extend(neg_pool[: max(1, initial_size - len(initial))])
    initial_strs = {ex.string for ex in initial}
    remaining = [ex for ex in pool_examples if ex.string not in initial_strs]

    active_labeled = list(initial)
    active_remaining = list(remaining)

    random_labeled = list(initial)
    random_remaining = list(remaining)
    rng.shuffle(random_remaining)

    budgets: list[int] = []
    active_accs: list[float] = []
    random_accs: list[float] = []
    active_st: list[int] = []
    random_st: list[int] = []

    for r_idx in range(rounds + 1):
        act_dfa = learn_edsm(active_labeled, alphabet=ref_dfa.alphabet, record_rejects=False).dfa
        rnd_dfa = learn_edsm(random_labeled, alphabet=ref_dfa.alphabet, record_rejects=False).dfa

        act_m = evaluate_dfa(act_dfa, test_set, reference_dfa=ref_dfa)
        rnd_m = evaluate_dfa(rnd_dfa, test_set, reference_dfa=ref_dfa)

        budgets.append(len(active_labeled))
        active_accs.append(act_m.accuracy)
        random_accs.append(rnd_m.accuracy)
        active_st.append(act_m.learned_states)
        random_st.append(rnd_m.learned_states)

        if r_idx == rounds or not active_remaining:
            break

        # Active: pick top `batch_size` most uncertain strings for current hypothesis.
        scored = sorted(
            active_remaining,
            key=lambda ex: _dfa_uncertainty_score(act_dfa, ex.string),
            reverse=True,
        )
        chosen_active = scored[:batch_size]
        chosen_set = {ex.string for ex in chosen_active}
        active_labeled.extend(chosen_active)
        active_remaining = [ex for ex in active_remaining if ex.string not in chosen_set]

        # Random: pick next `batch_size` random examples.
        chosen_rand = random_remaining[:batch_size]
        random_labeled.extend(chosen_rand)
        random_remaining = random_remaining[batch_size:]

    return ActiveLearningComparison(
        query_budgets=budgets,
        active_accuracies=active_accs,
        random_accuracies=random_accs,
        active_states=active_st,
        random_states=random_st,
    )

