"""Phase 0 reference language specifications for Automata Detective.

Defines the initial benchmark languages over {0, 1} and {a, b} used across
Phase 1 (automata engine tests), Phase 2 (dataset generation), Phase 3
(inference learners), and Phase 4 (experiments).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


DEFAULT_ALPHABETS: dict[str, tuple[str, ...]] = {
    "binary": ("0", "1"),
    "ab": ("a", "b"),
}


@dataclass(frozen=True)
class ReferenceLanguage:
    """Formal specification of a benchmark regular language."""

    id: str
    name: str
    alphabet: tuple[str, ...]
    description: str
    expected_min_dfa_states: int
    expected_nfa_states: int | None
    accepts: Callable[[str], bool]
    positive_examples: tuple[str, ...]
    negative_examples: tuple[str, ...]

    def validate_string(self, s: str) -> None:
        """Raise ValueError if `s` contains symbols outside `self.alphabet`."""
        allowed = set(self.alphabet)
        invalid = [ch for ch in s if ch not in allowed]
        if invalid:
            raise ValueError(
                f"String {s!r} contains symbols {sorted(set(invalid))} "
                f"outside alphabet {self.alphabet}"
            )


def _has_even_ones(s: str) -> bool:
    return s.count("1") % 2 == 0


def _ends_with_ab(s: str) -> bool:
    return s.endswith("ab")


def _no_aa_substring(s: str) -> bool:
    return "aa" not in s


def _length_divisible_by_3(s: str) -> bool:
    return len(s) % 3 == 0


def _exactly_two_as(s: str) -> bool:
    return s.count("a") == 2


def _third_from_end_is_a(s: str) -> bool:
    return len(s) >= 3 and s[-3] == "a"


REFERENCE_LANGUAGES: dict[str, ReferenceLanguage] = {
    "even_ones": ReferenceLanguage(
        id="even_ones",
        name="Even number of 1s",
        alphabet=DEFAULT_ALPHABETS["binary"],
        description="Strings over {0, 1} containing an even number of '1's (including epsilon).",
        expected_min_dfa_states=2,
        expected_nfa_states=2,
        accepts=_has_even_ones,
        positive_examples=("", "0", "00", "11", "0101", "1111"),
        negative_examples=("1", "01", "10", "111", "01011"),
    ),
    "ends_with_ab": ReferenceLanguage(
        id="ends_with_ab",
        name="Ends with ab",
        alphabet=DEFAULT_ALPHABETS["ab"],
        description="Strings over {a, b} whose last two symbols are 'ab'.",
        expected_min_dfa_states=3,
        expected_nfa_states=3,
        accepts=_ends_with_ab,
        positive_examples=("ab", "aab", "bab", "abab", "bbab"),
        negative_examples=("", "a", "b", "ba", "aba", "abb"),
    ),
    "no_aa": ReferenceLanguage(
        id="no_aa",
        name="No 'aa' substring",
        alphabet=DEFAULT_ALPHABETS["ab"],
        description="Strings over {a, b} that never contain two consecutive 'a's.",
        expected_min_dfa_states=3,
        expected_nfa_states=3,
        accepts=_no_aa_substring,
        positive_examples=("", "a", "b", "ab", "ba", "aba", "babab"),
        negative_examples=("aa", "baa", "aab", "abaa", "aaa"),
    ),
    "length_div_3": ReferenceLanguage(
        id="length_div_3",
        name="Length divisible by 3",
        alphabet=DEFAULT_ALPHABETS["ab"],
        description="Strings over {a, b} whose length is a multiple of 3 (including epsilon).",
        expected_min_dfa_states=3,
        expected_nfa_states=3,
        accepts=_length_divisible_by_3,
        positive_examples=("", "aaa", "aba", "bbb", "ababab"),
        negative_examples=("a", "b", "ab", "ba", "aaaa", "ababa"),
    ),
    "exactly_two_as": ReferenceLanguage(
        id="exactly_two_as",
        name="Exactly two 'a's",
        alphabet=DEFAULT_ALPHABETS["ab"],
        description="Strings over {a, b} containing exactly two occurrences of 'a'.",
        expected_min_dfa_states=4,
        expected_nfa_states=4,
        accepts=_exactly_two_as,
        positive_examples=("aa", "aab", "aba", "baa", "bbababb"),
        negative_examples=("", "a", "b", "bbb", "aaa", "ababa"),
    ),
    "third_from_end_a": ReferenceLanguage(
        id="third_from_end_a",
        name="3rd symbol from end is 'a'",
        alphabet=DEFAULT_ALPHABETS["ab"],
        description=(
            "Strings over {a, b} of length >= 3 where the 3rd symbol from the end is 'a'. "
            "Exhibits exponential NFA-to-DFA blowup (4 NFA states vs. 8 minimal DFA states)."
        ),
        expected_min_dfa_states=8,
        expected_nfa_states=4,
        accepts=_third_from_end_is_a,
        positive_examples=("aaa", "aab", "aba", "abb", "baaa", "bbabb"),
        negative_examples=("", "a", "ab", "baa", "bab", "bbb", "abaa"),
    ),
}


def get_reference_language(language_id: str) -> ReferenceLanguage:
    """Return a registered ReferenceLanguage by ID or raise KeyError."""
    if language_id not in REFERENCE_LANGUAGES:
        available = ", ".join(sorted(REFERENCE_LANGUAGES))
        raise KeyError(f"Unknown language {language_id!r}. Available: {available}")
    return REFERENCE_LANGUAGES[language_id]

