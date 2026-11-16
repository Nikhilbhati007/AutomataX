"""RPNI (Regular Positive and Negative Inference) grammatical inference."""

from __future__ import annotations

from typing import Iterable, Sequence

from data.generator import LabeledExample
from learn.base import LearningResult, LearningStep
from learn.pta import build_pta


def learn_rpni(
    examples: Sequence[LabeledExample | tuple[str, bool]],
    alphabet: Iterable[str] | None = None,
    *,
    strict: bool = False,
    record_rejects: bool = True,
) -> LearningResult:
    """Infer a DFA from labeled examples using canonical-order RPNI.

    States are explored in canonical shortlex order. Each blue fringe state is
    merged with the earliest compatible red state; if all red states reject the
    merge, the blue state is promoted to red.
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

        b = blue[0]  # Canonical shortlex order: smallest state ID in the blue fringe.
        merged_into: int | None = None

        for r in sorted(red):
            attempt = automaton.try_merge(r, b, red_states=red)
            if attempt is not None:
                automaton, red = attempt
                merged_into = r
                merges_accepted += 1
                _log(
                    "merge",
                    f"Merged blue q{b} into red q{r} ({len(automaton.active)} states remain).",
                    extra={"red": f"q{r}", "blue": f"q{b}"},
                )
                break
            merges_rejected += 1
            if record_rejects:
                _log(
                    "reject",
                    f"Rejected merge (q{r}, q{b}): accepts negative example.",
                    include_dfa=False,
                    extra={"red": f"q{r}", "blue": f"q{b}"},
                )

        if merged_into is None:
            red.add(b)
            promotions += 1
            _log(
                "promote",
                f"Promoted blue q{b} to red ({len(red)} red states).",
                extra={"promoted": f"q{b}"},
            )

    final_dfa = automaton.to_dfa()
    return LearningResult(
        dfa=final_dfa,
        steps=steps,
        algorithm="rpni",
        metadata={
            "initial_pta_states": initial_states,
            "final_states": len(final_dfa.states),
            "merges_accepted": merges_accepted,
            "merges_rejected": merges_rejected,
            "promotions": promotions,
            "num_examples": len(examples),
        },
    )

