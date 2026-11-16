"""EDSM (Evidence-Driven State Merging / Blue-Fringe) grammatical inference."""

from __future__ import annotations

from typing import Iterable, Sequence

from data.generator import LabeledExample
from learn.base import LearningResult, LearningStep
from learn.pta import MergeAutomaton, build_pta


def learn_edsm(
    examples: Sequence[LabeledExample | tuple[str, bool]],
    alphabet: Iterable[str] | None = None,
    *,
    strict: bool = False,
    record_rejects: bool = False,
) -> LearningResult:
    """Infer a DFA using Blue-Fringe Evidence-Driven State Merging (EDSM).

    At each iteration:
      1. If any blue state cannot merge consistently with *any* red state,
         promote the first such blue state immediately.
      2. Otherwise, score all consistent `(red, blue)` candidate pairs by the
         increase in label-overlap evidence and execute the highest-scoring merge.
    """
    automaton = build_pta(examples, alphabet=alphabet, strict=strict)
    initial_states = len(automaton.active)
    red: set[int] = {automaton.start}
    steps: list[LearningStep] = []

    def _log(
        step_type: str,
        description: str,
        *,
        include_dfa: bool = True,
        extra: dict[str, object] | None = None,
    ) -> None:
        payload: dict[str, object] = dict(extra) if extra else {}
        payload["red_states"] = [f"q{r}" for r in sorted(red)]
        payload["blue_states"] = [f"q{b}" for b in automaton.blue_fringe(red)]
        payload["state_count"] = len(automaton.active)
        if include_dfa:
            payload["dfa"] = automaton.to_dfa().to_dict()
        steps.append(
            LearningStep(
                step_index=len(steps),
                step_type=step_type,
                description=description,
                data=payload,
            )
        )

    _log(
        "pta_init",
        f"Initialized PTA with {initial_states} states from {len(examples)} examples.",
    )

    merges_accepted = 0
    merges_rejected = 0
    promotions = 0

    while True:
        blue = automaton.blue_fringe(red)
        if not blue:
            break

        base_score = automaton.evidence_score()
        unmergeable_blue: int | None = None
        best_score = -1
        best_pair: tuple[int, int] | None = None
        best_result: tuple[MergeAutomaton, set[int]] | None = None
        candidate_summaries: list[dict[str, object]] = []

        ordered_red = sorted(red)
        for b in blue:
            valid_for_b = 0
            for r in ordered_red:
                attempt = automaton.try_merge(r, b, red_states=red)
                if attempt is None:
                    merges_rejected += 1
                    if record_rejects:
                        _log(
                            "reject",
                            f"Candidate (q{r}, q{b}) rejected due to label conflict.",
                            include_dfa=False,
                            extra={"red": f"q{r}", "blue": f"q{b}"},
                        )
                    continue

                valid_for_b += 1
                cand_auto, _ = attempt
                delta = cand_auto.evidence_score() - base_score
                candidate_summaries.append({"red": f"q{r}", "blue": f"q{b}", "score": delta})
                if delta > best_score:
                    best_score = delta
                    best_pair = (r, b)
                    best_result = attempt

            if valid_for_b == 0 and unmergeable_blue is None:
                unmergeable_blue = b

        if unmergeable_blue is not None:
            red.add(unmergeable_blue)
            promotions += 1
            _log(
                "promote",
                f"Promoted unmergeable blue q{unmergeable_blue} to red ({len(red)} red states).",
                extra={"promoted": f"q{unmergeable_blue}"},
            )
            continue

        assert best_pair is not None and best_result is not None
        r_best, b_best = best_pair
        automaton, red = best_result
        merges_accepted += 1
        _log(
            "merge",
            (
                f"Merged blue q{b_best} into red q{r_best} "
                f"(evidence score +{best_score}, {len(automaton.active)} states remain)."
            ),
            extra={
                "red": f"q{r_best}",
                "blue": f"q{b_best}",
                "score": best_score,
                "candidates_evaluated": len(candidate_summaries),
            },
        )

    final_dfa = automaton.to_dfa()
    return LearningResult(
        dfa=final_dfa,
        steps=steps,
        algorithm="edsm",
        metadata={
            "initial_pta_states": initial_states,
            "final_states": len(final_dfa.states),
            "merges_accepted": merges_accepted,
            "merges_rejected": merges_rejected,
            "promotions": promotions,
            "num_examples": len(examples),
        },
    )

