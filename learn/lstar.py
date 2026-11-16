"""Angluin's L* active DFA inference algorithm using membership and equivalence oracles."""

from __future__ import annotations

from typing import Iterable

from core.dfa import DFA
from learn.base import (
    EquivalenceOracle,
    LearningResult,
    LearningStep,
    MembershipOracle,
    make_dfa_equivalence_oracle,
    make_dfa_membership_oracle,
)


def learn_lstar(
    alphabet: Iterable[str],
    membership_oracle: MembershipOracle,
    equivalence_oracle: EquivalenceOracle,
    *,
    max_rounds: int = 500,
) -> LearningResult:
    """Learn the exact minimal DFA via Angluin's L* observation table algorithm."""
    ordered_alpha = tuple(alphabet)
    if not ordered_alpha:
        raise ValueError("Alphabet must not be empty.")

    prefixes: list[str] = [""]  # S
    prefix_set: set[str] = {""}
    suffixes: list[str] = [""]  # E
    suffix_set: set[str] = {""}
    cache: dict[str, bool] = {}
    steps: list[LearningStep] = []

    membership_queries = 0
    equivalence_queries = 0

    def query(s: str) -> bool:
        nonlocal membership_queries
        if s not in cache:
            cache[s] = bool(membership_oracle(s))
            membership_queries += 1
        return cache[s]

    def row(prefix: str) -> tuple[bool, ...]:
        return tuple(query(prefix + suffix) for suffix in suffixes)

    def _log(step_type: str, description: str, data: dict[str, object] | None = None) -> None:
        payload = dict(data) if data else {}
        payload["num_prefixes"] = len(prefixes)
        payload["num_suffixes"] = len(suffixes)
        payload["membership_queries"] = membership_queries
        payload["equivalence_queries"] = equivalence_queries
        steps.append(
            LearningStep(
                step_index=len(steps),
                step_type=step_type,
                description=description,
                data=payload,
            )
        )

    def _build_hypothesis() -> DFA:
        row_to_rep: dict[tuple[bool, ...], str] = {}
        row_to_name: dict[tuple[bool, ...], str] = {}
        for p in prefixes:
            r = row(p)
            if r not in row_to_rep:
                row_to_rep[r] = p
                row_to_name[r] = f"q{len(row_to_name)}"

        start_name = row_to_name[row("")]
        accept_states = {
            name for r, name in row_to_name.items() if r[0]  # "" is always suffixes[0]
        }
        transitions: dict[str, dict[str, str]] = {}
        for r, rep in row_to_rep.items():
            src_name = row_to_name[r]
            transitions[src_name] = {
                sym: row_to_name[row(rep + sym)] for sym in ordered_alpha
            }

        return DFA(
            states=row_to_name.values(),
            alphabet=ordered_alpha,
            transitions=transitions,
            start=start_name,
            accept_states=accept_states,
        )

    _log("lstar_init", "Initialized L* observation table with S={''}, E={''}.")

    hypothesis: DFA | None = None
    for _ in range(max_rounds):
        # Close and make consistent.
        while True:
            closed_changed = False
            s_rows = {row(s) for s in prefixes}
            for s in list(prefixes):
                for sym in ordered_alpha:
                    ext = s + sym
                    if row(ext) not in s_rows:
                        if ext not in prefix_set:
                            prefixes.append(ext)
                            prefix_set.add(ext)
                        s_rows.add(row(ext))
                        closed_changed = True
                        _log(
                            "lstar_close",
                            f"Closed table by promoting prefix {ext!r} to S.",
                            {"added_prefix": ext},
                        )
                        break
                if closed_changed:
                    break
            if closed_changed:
                continue

            # Consistency check.
            consistent_changed = False
            for i in range(len(prefixes)):
                for j in range(i + 1, len(prefixes)):
                    s1, s2 = prefixes[i], prefixes[j]
                    if row(s1) != row(s2):
                        continue
                    for sym in ordered_alpha:
                        for suf in suffixes:
                            if query(s1 + sym + suf) != query(s2 + sym + suf):
                                new_suf = sym + suf
                                if new_suf not in suffix_set:
                                    suffixes.append(new_suf)
                                    suffix_set.add(new_suf)
                                consistent_changed = True
                                _log(
                                    "lstar_consistent",
                                    (
                                        f"Resolved inconsistency between {s1!r} and {s2!r} "
                                        f"by adding suffix {new_suf!r} to E."
                                    ),
                                    {"added_suffix": new_suf, "s1": s1, "s2": s2},
                                )
                                break
                        if consistent_changed:
                            break
                    if consistent_changed:
                        break
                if consistent_changed:
                    break

            if not consistent_changed:
                break

        hypothesis = _build_hypothesis()
        equivalence_queries += 1
        equivalent, counterexample = equivalence_oracle(hypothesis)
        _log(
            "lstar_hypothesize",
            f"Proposed {len(hypothesis.states)}-state hypothesis (equivalent={equivalent}).",
            {
                "equivalent": equivalent,
                "counterexample": counterexample,
                "dfa": hypothesis.to_dict(),
            },
        )

        if equivalent:
            return LearningResult(
                dfa=hypothesis,
                steps=steps,
                algorithm="lstar",
                metadata={
                    "final_states": len(hypothesis.states),
                    "membership_queries": membership_queries,
                    "equivalence_queries": equivalence_queries,
                    "num_prefixes": len(prefixes),
                    "num_suffixes": len(suffixes),
                },
            )

        assert counterexample is not None
        added: list[str] = []
        for idx in range(len(counterexample) + 1):
            pref = counterexample[:idx]
            if pref not in prefix_set:
                prefixes.append(pref)
                prefix_set.add(pref)
                added.append(pref)
        _log(
            "lstar_counterexample",
            f"Received counterexample {counterexample!r}; added {len(added)} prefix(es) to S.",
            {"counterexample": counterexample, "added_prefixes": added},
        )

    raise RuntimeError(f"L* did not converge within {max_rounds} rounds.")


def learn_lstar_from_dfa(target_dfa: DFA, *, max_rounds: int = 500) -> LearningResult:
    """Convenience wrapper running Angluin's L* directly against a ground-truth DFA."""
    return learn_lstar(
        alphabet=target_dfa.alphabet,
        membership_oracle=make_dfa_membership_oracle(target_dfa),
        equivalence_oracle=make_dfa_equivalence_oracle(target_dfa),
        max_rounds=max_rounds,
    )

