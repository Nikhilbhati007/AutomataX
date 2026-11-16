"""Phase 2 dataset generator, train/test splitter, and characteristic sampler."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import random
from typing import Iterable, Literal

from core.dfa import DFA
from core.languages import ReferenceLanguage
from core.reference_machines import get_reference_dfa
from data.regex import regex_to_dfa

SamplingMode = Literal["uniform", "length_stratified", "random_walk"]
TargetSpec = DFA | ReferenceLanguage | str


@dataclass(frozen=True)
class LabeledExample:
    """A single labeled training or test string."""

    string: str
    label: bool
    true_label: bool

    @property
    def is_noisy(self) -> bool:
        """Return True if label noise flipped the true membership label."""
        return self.label != self.true_label

    def to_dict(self) -> dict[str, object]:
        return {
            "string": self.string,
            "label": self.label,
            "true_label": self.true_label,
            "is_noisy": self.is_noisy,
        }


@dataclass(frozen=True)
class DatasetSplit:
    """Train and test splits plus generation metadata."""

    train: list[LabeledExample]
    test: list[LabeledExample]
    alphabet: tuple[str, ...]
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "alphabet": list(self.alphabet),
            "train": [ex.to_dict() for ex in self.train],
            "test": [ex.to_dict() for ex in self.test],
            "metadata": dict(self.metadata),
        }


def resolve_target_dfa(
    target: TargetSpec,
    alphabet: Iterable[str] | None = None,
) -> DFA:
    """Convert a DFA, ReferenceLanguage, or regex string into a minimal complete DFA."""
    if isinstance(target, DFA):
        if alphabet is not None and tuple(alphabet) != target.alphabet:
            raise ValueError(
                f"Provided alphabet {tuple(alphabet)} does not match DFA alphabet {target.alphabet}."
            )
        return target.complete()

    if isinstance(target, ReferenceLanguage):
        dfa = get_reference_dfa(target.id)
        if alphabet is not None and tuple(alphabet) != dfa.alphabet:
            raise ValueError(
                f"Provided alphabet {tuple(alphabet)} does not match language alphabet {dfa.alphabet}."
            )
        return dfa.complete()

    if isinstance(target, str):
        alpha = tuple(alphabet) if alphabet is not None else None
        return regex_to_dfa(target, alphabet=alpha)

    raise TypeError(f"Unsupported target type: {type(target).__name__}")


def _random_string_of_length(
    rng: random.Random, alphabet: tuple[str, ...], length: int
) -> str:
    if length == 0:
        return ""
    return "".join(rng.choices(alphabet, k=length))


def _sample_length_weighted(
    rng: random.Random, alphabet_size: int, min_length: int, max_length: int
) -> int:
    """Pick length in [min_length, max_length] weighted by |Sigma|^length (uniform over strings)."""
    lengths = list(range(min_length, max_length + 1))
    # Cap exponent growth difference via log/relative weights, exact for reasonable lengths.
    if max_length - min_length <= 30:
        weights = [alphabet_size**ell for ell in lengths]
        return rng.choices(lengths, weights=weights, k=1)[0]
    # For very large ranges, bias smoothly without overflowing huge powers unnecessarily.
    weights = [alphabet_size ** (ell - min_length) for ell in lengths]
    return rng.choices(lengths, weights=weights, k=1)[0]


def _random_walk_string(
    rng: random.Random,
    dfa: DFA,
    min_length: int,
    max_length: int,
    stop_prob: float = 0.25,
) -> str:
    """Perform a random walk through `dfa` from `dfa.start`, returning the traversed string."""
    if max_length == 0:
        return ""
    target_stop_len = max_length
    if min_length < max_length:
        # Geometric-like stop probability after reaching min_length.
        for length in range(min_length, max_length):
            if rng.random() < stop_prob:
                target_stop_len = length
                break

    state = dfa.start
    chars: list[str] = []
    for _ in range(target_stop_len):
        sym = rng.choice(dfa.alphabet)
        nxt = dfa.step(state, sym)
        if nxt is None:
            break
        chars.append(sym)
        state = nxt
    return "".join(chars)


def _inject_noise(
    examples: list[LabeledExample],
    noise_rate: float,
    rng: random.Random,
) -> list[LabeledExample]:
    """Flip labels on `round(len(examples) * noise_rate)` randomly selected examples."""
    if noise_rate <= 0.0 or not examples:
        return list(examples)

    n_flip = round(len(examples) * noise_rate)
    n_flip = max(0, min(len(examples), n_flip))
    flip_indices = set(rng.sample(range(len(examples)), k=n_flip))
    result: list[LabeledExample] = []
    for idx, ex in enumerate(examples):
        if idx in flip_indices:
            result.append(
                LabeledExample(string=ex.string, label=not ex.true_label, true_label=ex.true_label)
            )
        else:
            result.append(ex)
    return result


def generate_dataset(
    target: TargetSpec,
    *,
    alphabet: Iterable[str] | None = None,
    min_length: int = 0,
    max_length: int = 8,
    size: int = 50,
    positive_ratio: float = 0.5,
    noise_rate: float = 0.0,
    sampling_mode: SamplingMode = "uniform",
    unique: bool = True,
    exclude: Iterable[str] = (),
    seed: int | None = None,
) -> list[LabeledExample]:
    """Generate labeled strings from a reference DFA, ReferenceLanguage, or regex.

    Args:
        target: A `DFA`, `ReferenceLanguage`, or regex pattern string.
        alphabet: Optional symbol tuple (validated against DFA/language or used for regex).
        min_length: Minimum generated string length (>= 0).
        max_length: Maximum generated string length (>= min_length).
        size: Target number of examples to return.
        positive_ratio: Desired fraction of positive examples in [0.0, 1.0].
        noise_rate: Fraction of examples whose labels are flipped, in [0.0, 1.0].
        sampling_mode: One of ``"uniform"``, ``"length_stratified"``, or ``"random_walk"``.
        unique: If True, disallow duplicate strings (bounded if language space is smaller).
        exclude: Optional strings that must not appear in the generated dataset.
        seed: Optional random seed for reproducibility.
    """
    if min_length < 0:
        raise ValueError("min_length must be >= 0.")
    if max_length < min_length:
        raise ValueError("max_length must be >= min_length.")
    if size < 0:
        raise ValueError("size must be >= 0.")
    if not 0.0 <= positive_ratio <= 1.0:
        raise ValueError("positive_ratio must be between 0.0 and 1.0.")
    if not 0.0 <= noise_rate <= 1.0:
        raise ValueError("noise_rate must be between 0.0 and 1.0.")
    if sampling_mode not in ("uniform", "length_stratified", "random_walk"):
        raise ValueError(
            f"Invalid sampling_mode {sampling_mode!r}. "
            "Choose 'uniform', 'length_stratified', or 'random_walk'."
        )

    if size == 0:
        return []

    dfa = resolve_target_dfa(target, alphabet=alphabet)
    rng = random.Random(seed)
    excluded = set(exclude)

    target_pos = round(size * positive_ratio)
    target_neg = size - target_pos

    pos_examples: list[LabeledExample] = []
    neg_examples: list[LabeledExample] = []
    seen: set[str] = set(excluded)

    lengths = list(range(min_length, max_length + 1))
    strat_idx = 0

    def _draw_candidate() -> str:
        nonlocal strat_idx
        if sampling_mode == "uniform":
            ell = _sample_length_weighted(rng, len(dfa.alphabet), min_length, max_length)
            return _random_string_of_length(rng, dfa.alphabet, ell)
        if sampling_mode == "length_stratified":
            ell = lengths[strat_idx % len(lengths)]
            strat_idx += 1
            return _random_string_of_length(rng, dfa.alphabet, ell)
        return _random_walk_string(rng, dfa, min_length, max_length)

    max_attempts = max(2000, size * 100)
    attempts = 0
    while (len(pos_examples) < target_pos or len(neg_examples) < target_neg) and attempts < max_attempts:
        attempts += 1
        candidate = _draw_candidate()
        if unique and candidate in seen:
            continue

        is_pos = dfa.matches(candidate)
        if is_pos and len(pos_examples) < target_pos:
            if unique:
                seen.add(candidate)
            pos_examples.append(LabeledExample(string=candidate, label=True, true_label=True))
        elif not is_pos and len(neg_examples) < target_neg:
            if unique:
                seen.add(candidate)
            neg_examples.append(LabeledExample(string=candidate, label=False, true_label=False))

    # If one class is sparse or exhausted, top up remaining slots from the other class.
    combined = pos_examples + neg_examples
    topup_attempts = 0
    while len(combined) < size and topup_attempts < max_attempts:
        topup_attempts += 1
        candidate = _draw_candidate()
        if unique and candidate in seen:
            continue
        if unique:
            seen.add(candidate)
        is_pos = dfa.matches(candidate)
        combined.append(LabeledExample(string=candidate, label=is_pos, true_label=is_pos))

    rng.shuffle(combined)
    return _inject_noise(combined, noise_rate=noise_rate, rng=rng)


def generate_train_test_split(
    target: TargetSpec,
    *,
    alphabet: Iterable[str] | None = None,
    train_min_length: int = 0,
    train_max_length: int = 6,
    train_size: int = 50,
    test_min_length: int | None = None,
    test_max_length: int | None = None,
    test_size: int = 100,
    positive_ratio: float = 0.5,
    noise_rate: float = 0.0,
    sampling_mode: SamplingMode = "length_stratified",
    test_sampling_mode: SamplingMode = "uniform",
    seed: int | None = None,
) -> DatasetSplit:
    """Generate a disjoint train/test split where test strings extend to longer lengths."""
    dfa = resolve_target_dfa(target, alphabet=alphabet)

    if test_min_length is None:
        test_min_length = train_max_length + 1
    if test_max_length is None:
        test_max_length = max(test_min_length + 3, train_max_length + 4)

    train_seed = seed
    test_seed = None if seed is None else seed + 1

    train = generate_dataset(
        dfa,
        min_length=train_min_length,
        max_length=train_max_length,
        size=train_size,
        positive_ratio=positive_ratio,
        noise_rate=noise_rate,
        sampling_mode=sampling_mode,
        unique=True,
        seed=train_seed,
    )
    train_strings = {ex.string for ex in train}

    test = generate_dataset(
        dfa,
        min_length=test_min_length,
        max_length=test_max_length,
        size=test_size,
        positive_ratio=positive_ratio,
        noise_rate=0.0,
        sampling_mode=test_sampling_mode,
        unique=True,
        exclude=train_strings,
        seed=test_seed,
    )

    metadata: dict[str, object] = {
        "train_size": len(train),
        "test_size": len(test),
        "train_length_range": [train_min_length, train_max_length],
        "test_length_range": [test_min_length, test_max_length],
        "sampling_mode": sampling_mode,
        "test_sampling_mode": test_sampling_mode,
        "positive_ratio_target": positive_ratio,
        "noise_rate": noise_rate,
        "noisy_train_count": sum(1 for ex in train if ex.is_noisy),
    }
    return DatasetSplit(train=train, test=test, alphabet=dfa.alphabet, metadata=metadata)


def _find_distinguishing_suffix(dfa: DFA, s1: str, s2: str) -> str:
    """Return a shortest distinguishing suffix between `s1` and `s2` in a minimal complete DFA."""
    ordered = tuple(sorted(dfa.alphabet))
    visited: set[tuple[str, str]] = {(s1, s2)}
    queue: deque[tuple[str, str, str]] = deque([(s1, s2, "")])

    while queue:
        a, b, suffix = queue.popleft()
        if (a in dfa.accept_states) != (b in dfa.accept_states):
            return suffix
        for sym in ordered:
            na = dfa.transitions[a][sym]
            nb = dfa.transitions[b][sym]
            pair = (na, nb)
            if pair not in visited:
                visited.add(pair)
                queue.append((na, nb, suffix + sym))

    raise ValueError(f"States {s1!r} and {s2!r} are equivalent and cannot be distinguished.")


def _find_accepting_suffix(dfa: DFA, state: str) -> str | None:
    """Return a shortest suffix reaching an accepting state from `state`, or None if dead."""
    ordered = tuple(sorted(dfa.alphabet))
    visited: set[str] = {state}
    queue: deque[tuple[str, str]] = deque([(state, "")])

    while queue:
        cur, suffix = queue.popleft()
        if cur in dfa.accept_states:
            return suffix
        for sym in ordered:
            nxt = dfa.transitions[cur][sym]
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, suffix + sym))
    return None


def generate_characteristic_sample(
    target: TargetSpec,
    *,
    alphabet: Iterable[str] | None = None,
) -> list[LabeledExample]:
    """Generate a minimal DFA characteristic sample (short prefixes + distinguishing suffixes).

    Computes:
      1. Shortlex state-access strings `Sp` reaching every state of the minimal DFA.
      2. One-symbol transitions `K = Sp U (Sp * alphabet)`.
      3. Distinguishing suffixes separating every pair of non-equivalent prefixes
         `(u in K, v in Sp)`, plus shortest accepting suffixes per non-dead state.
    """
    dfa = resolve_target_dfa(target, alphabet=alphabet).minimize()
    ordered_alpha = tuple(sorted(dfa.alphabet))

    # 1. Shortest (shortlex) string reaching each state.
    access_str: dict[str, str] = {dfa.start: ""}
    queue: deque[str] = deque([dfa.start])
    while queue:
        state = queue.popleft()
        prefix = access_str[state]
        for sym in ordered_alpha:
            nxt = dfa.transitions[state][sym]
            if nxt not in access_str:
                access_str[nxt] = prefix + sym
                queue.append(nxt)

    def _run_state(s: str) -> str:
        cur = dfa.start
        for ch in s:
            cur = dfa.transitions[cur][ch]
        return cur

    # 2. Transition-covering kernel K = Sp U {u + a | u in Sp, a in Sigma}.
    short_prefixes = sorted(access_str.values(), key=lambda x: (len(x), x))
    kernel_set: set[str] = set(short_prefixes)
    for u in short_prefixes:
        for sym in ordered_alpha:
            kernel_set.add(u + sym)
    kernel = sorted(kernel_set, key=lambda x: (len(x), x))

    # 3. Include every u in K, shortest accepting suffix from state(u), and distinguishing suffixes.
    sample_strings: set[str] = set(kernel)

    # Cache accepting and pairwise distinguishing suffixes.
    acc_suffix_cache: dict[str, str | None] = {
        st: _find_accepting_suffix(dfa, st) for st in dfa.states
    }
    dist_cache: dict[tuple[str, str], str] = {}
    states_list = sorted(dfa.states)
    for i, s1 in enumerate(states_list):
        for s2 in states_list[i + 1 :]:
            w = _find_distinguishing_suffix(dfa, s1, s2)
            dist_cache[(s1, s2)] = w
            dist_cache[(s2, s1)] = w

    for u in kernel:
        su = _run_state(u)
        acc_w = acc_suffix_cache[su]
        if acc_w is not None:
            sample_strings.add(u + acc_w)

        for v in short_prefixes:
            sv = _run_state(v)
            if su != sv:
                w = dist_cache[(su, sv)]
                sample_strings.add(u + w)
                sample_strings.add(v + w)

    ordered_samples = sorted(sample_strings, key=lambda x: (len(x), x))
    return [
        LabeledExample(
            string=s,
            label=(acc := dfa.matches(s)),
            true_label=acc,
        )
        for s in ordered_samples
    ]

