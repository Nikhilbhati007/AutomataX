"""Exploratory string clustering by DFA end-state and n-gram K-means."""

from __future__ import annotations

import math
import random
from typing import Sequence

from core.dfa import DFA


def cluster_strings_by_end_state(
    dfa: DFA, strings: Sequence[str]
) -> dict[str, dict[str, object]]:
    """Group strings by the final state reached when simulated on `dfa`."""
    clusters: dict[str, list[str]] = {}
    for s in strings:
        accepted, path = dfa.accepts(s)
        end_state = path[-1]
        # Distinguish hitting dead transition early vs completing in state.
        key = end_state if len(path) == len(s) + 1 else f"{end_state} (stopped)"
        clusters.setdefault(key, []).append(s)

    summary: dict[str, dict[str, object]] = {}
    for state_key in sorted(clusters.keys()):
        items = clusters[state_key]
        base_state = state_key.split(" ")[0]
        summary[state_key] = {
            "accepting": base_state in dfa.accept_states and "stopped" not in state_key,
            "count": len(items),
            "examples": items,
        }
    return summary


def _ngram_vector(s: str, n: int) -> dict[str, float]:
    vec: dict[str, float] = {"__len__": float(len(s))}
    if len(s) < n:
        vec[f"__short_{s}__"] = 1.0
        return vec
    for i in range(len(s) - n + 1):
        gram = s[i : i + n]
        vec[gram] = vec.get(gram, 0.0) + 1.0
    return vec


def _sq_distance(v1: dict[str, float], v2: dict[str, float]) -> float:
    keys = set(v1.keys()) | set(v2.keys())
    return sum((v1.get(k, 0.0) - v2.get(k, 0.0)) ** 2 for k in keys)


def cluster_strings_by_ngrams(
    strings: Sequence[str],
    *,
    n: int = 2,
    k: int = 3,
    max_iters: int = 25,
    seed: int = 42,
) -> dict[int, list[str]]:
    """Cluster strings via pure-Python K-means over n-gram feature vectors."""
    unique_strings = list(dict.fromkeys(strings))
    if not unique_strings:
        return {}

    effective_k = max(1, min(k, len(unique_strings)))
    vectors = [_ngram_vector(s, n) for s in unique_strings]
    rng = random.Random(seed)
    centroid_indices = rng.sample(range(len(unique_strings)), k=effective_k)
    centroids = [dict(vectors[i]) for i in centroid_indices]

    assignments = [0] * len(unique_strings)
    for _ in range(max_iters):
        changed = False
        for i, vec in enumerate(vectors):
            best_c = min(
                range(effective_k),
                key=lambda c: (_sq_distance(vec, centroids[c]), c),
            )
            if assignments[i] != best_c:
                assignments[i] = best_c
                changed = True

        if not changed:
            break

        # Recompute centroids
        for c in range(effective_k):
            members = [vectors[i] for i, a in enumerate(assignments) if a == c]
            if not members:
                continue
            new_cent: dict[str, float] = {}
            for m in members:
                for key, val in m.items():
                    new_cent[key] = new_cent.get(key, 0.0) + val
            scale = 1.0 / len(members)
            centroids[c] = {key: val * scale for key, val in new_cent.items() if not math.isclose(val, 0.0)}

    grouped: dict[int, list[str]] = {c: [] for c in range(effective_k)}
    for s, c in zip(unique_strings, assignments):
        grouped[c].append(s)
    return {c: items for c, items in grouped.items() if items}

