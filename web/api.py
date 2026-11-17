"""FastAPI backend API for Automata Detective."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core import (
    DEFAULT_ALPHABETS,
    DFA,
    REFERENCE_LANGUAGES,
    are_equivalent,
    get_reference_dfa,
    get_reference_language,
)
from data import (
    generate_characteristic_sample,
    generate_dataset,
    generate_train_test_split,
    regex_to_dfa,
)
from experiments import (
    cluster_strings_by_end_state,
    evaluate_dfa,
    run_active_vs_random_study,
    run_diversity_study,
    run_learning_curve,
    run_noise_study,
)
from learn import learn_edsm, learn_lstar_from_dfa, learn_rpni

app = FastAPI(
    title="Automata Detective API",
    description="Interactive backend for learning, simulating, and evaluating DFA models from data.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Cytoscape Graph Adapter
# ---------------------------------------------------------------------------

def dfa_to_cytoscape(dfa_dict: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert a serialized DFA dictionary to Cytoscape.js node/edge elements."""
    elements: list[dict[str, Any]] = []
    states: list[str] = dfa_dict.get("states", [])
    start_state: str = dfa_dict.get("start", "")
    accept_states: set[str] = set(dfa_dict.get("accept_states", []))
    transitions: dict[str, dict[str, str]] = dfa_dict.get("transitions", {})

    for s in states:
        elements.append(
            {
                "data": {
                    "id": s,
                    "label": s,
                    "is_start": s == start_state,
                    "is_accept": s in accept_states,
                },
                "classes": " ".join(
                    filter(
                        None,
                        [
                            "start" if s == start_state else "",
                            "accept" if s in accept_states else "",
                        ],
                    )
                ),
            }
        )

    # Group parallel edges between same (source, target) into comma-separated label
    edge_map: dict[tuple[str, str], list[str]] = {}
    for src, edges in transitions.items():
        for sym, dst in edges.items():
            edge_map.setdefault((src, dst), []).append(sym)

    for (src, dst), syms in edge_map.items():
        label = ", ".join(sorted(syms))
        edge_id = f"e_{src}_{dst}"
        elements.append(
            {
                "data": {
                    "id": edge_id,
                    "source": src,
                    "target": dst,
                    "label": label,
                    "is_self": src == dst,
                }
            }
        )

    return elements


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    target_type: Literal["language", "regex"] = "language"
    target: str = "ends_with_ab"
    alphabet: list[str] | None = None
    size: int = Field(default=35, ge=1, le=500)
    min_length: int = Field(default=0, ge=0)
    max_length: int = Field(default=7, ge=0)
    positive_ratio: float = Field(default=0.5, ge=0.0, le=1.0)
    noise_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    sampling_mode: Literal["uniform", "length_stratified", "random_walk", "characteristic"] = "length_stratified"
    seed: int | None = 42


class ExampleItem(BaseModel):
    string: str
    label: bool


class LearnRequest(BaseModel):
    algorithm: Literal["edsm", "rpni", "lstar"] = "edsm"
    examples: list[ExampleItem] | None = None
    alphabet: list[str] | None = None
    target_language: str | None = None  # Required if algorithm == "lstar"
    strict: bool = False


class SimulateRequest(BaseModel):
    dfa: dict[str, Any] | None = None
    language_id: str | None = None
    string: str


class CompareRequest(BaseModel):
    dfa: dict[str, Any]
    reference_language_id: str
    test_size: int = Field(default=60, ge=10, le=300)


class LearningCurveRequest(BaseModel):
    language_id: str = "ends_with_ab"
    train_sizes: list[int] = Field(default=[10, 25, 50, 80])
    learners: list[str] = Field(default=["edsm", "rpni"])
    seeds: list[int] = Field(default=[0, 1, 2])


class NoiseStudyRequest(BaseModel):
    language_id: str = "even_ones"
    noise_rates: list[float] = Field(default=[0.0, 0.05, 0.10, 0.20])
    learners: list[str] = Field(default=["rpni", "edsm"])
    train_size: int = Field(default=60, ge=10, le=200)
    seeds: list[int] = Field(default=[0, 1])


class ActiveStudyRequest(BaseModel):
    language_id: str = "ends_with_ab"
    initial_size: int = 6
    batch_size: int = 6
    rounds: int = 4
    seed: int = 42


class ClusterRequest(BaseModel):
    dfa: dict[str, Any]
    strings: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/languages")
def list_languages() -> dict[str, Any]:
    """Return catalog of Phase 0 benchmark languages."""
    catalog = []
    for lang_id, spec in sorted(REFERENCE_LANGUAGES.items()):
        catalog.append(
            {
                "id": lang_id,
                "name": spec.name,
                "alphabet": list(spec.alphabet),
                "description": spec.description,
                "expected_min_dfa_states": spec.expected_min_dfa_states,
                "expected_nfa_states": spec.expected_nfa_states,
                "positive_examples": list(spec.positive_examples),
                "negative_examples": list(spec.negative_examples),
            }
        )
    return {"languages": catalog, "default_alphabets": DEFAULT_ALPHABETS}


@app.get("/api/presets")
def list_presets() -> dict[str, Any]:
    """Demo presets for 30-second live presentation stories & case files."""
    presets = [
        {
            "id": "too_few_examples",
            "case_code": "CASE-001",
            "clearance": "RESTRICTED",
            "status": "COLD CASE",
            "difficulty": "Novice",
            "title": "Case 01: The Sparse Suffix Ambiguity",
            "subtitle": "4 sparse strings produce an incomplete/premature hypothesis",
            "language": "ends_with_ab",
            "algorithm": "edsm",
            "suspect": "Pattern ending with 'ab' over Σ = {a, b}",
            "examples": [
                {"string": "ab", "label": True},
                {"string": "aab", "label": True},
                {"string": "a", "label": False},
                {"string": "b", "label": False},
            ],
            "description": "With just 4 strings, the learner folds prematurely into an overgeneralized hypothesis that fails on longer strings.",
        },
        {
            "id": "diverse_correction",
            "case_code": "CASE-002",
            "clearance": "CONFIDENTIAL",
            "status": "SOLVABLE",
            "difficulty": "Specialist",
            "title": "Case 02: The Characteristic Blueprint",
            "subtitle": "Characteristic sample converges to exact minimal DFA",
            "language": "ends_with_ab",
            "algorithm": "edsm",
            "suspect": "Exact state boundary mapping of 'ends_with_ab'",
            "sampling_mode": "characteristic",
            "description": "Feed a compact set of shortlex prefixes and distinguishing suffixes; watch 100% equivalence emerge.",
        },
        {
            "id": "noisy_mode",
            "case_code": "CASE-003",
            "clearance": "SECRET",
            "status": "COMPROMISED",
            "difficulty": "Hard",
            "title": "Case 03: The Corrupted Wiretap Showdown",
            "subtitle": "RPNI collapses while EDSM degrades gracefully under 15% noise",
            "language": "even_ones",
            "algorithm": "edsm",
            "suspect": "Even parity language with flipped labels in transit",
            "noise_rate": 0.15,
            "description": "Observe how label flips affect the PTA collapse. RPNI overfits invalid merges whereas EDSM's endorsement scoring resists distortion.",
        },
        {
            "id": "active_learning",
            "case_code": "CASE-004",
            "clearance": "TOP SECRET",
            "status": "BLACK OPS",
            "difficulty": "Classified",
            "title": "Case 04: The Oracle Interrogation (Angluin L*)",
            "subtitle": "Uncertainty queries reach target accuracy in half the examples",
            "language": "third_from_end_a",
            "algorithm": "lstar",
            "suspect": "High-complexity delayed trigger: 3rd symbol from end is 'a' (8 states)",
            "description": "Active query oracle interrogates transition boundaries directly, discovering missing states via counterexample-guided refinement.",
        },
        {
            "id": "parity_anomaly",
            "case_code": "CASE-005",
            "clearance": "RESTRICTED",
            "status": "ACTIVE CASE",
            "difficulty": "Medium",
            "title": "Case 05: The Parity Lockout",
            "subtitle": "Binary modulo-2 alternating clock cycles",
            "language": "even_ones",
            "algorithm": "edsm",
            "suspect": "Infinite binary streams accepting even number of 1s",
            "sampling_mode": "length_stratified",
            "description": "Examine if evidence-driven merging discovers the 2-state periodic cycle without hardcoded modular arithmetic.",
        },
    ]
    return {"presets": presets}


@app.get("/api/reference-dfa/{language_id}")
def get_reference_machine(language_id: str) -> dict[str, Any]:
    """Fetch the ground-truth minimal DFA and Cytoscape representation for a language."""
    if language_id not in REFERENCE_LANGUAGES:
        raise HTTPException(status_code=404, detail=f"Language {language_id!r} not found.")
    dfa = get_reference_dfa(language_id)
    dfa_dict = dfa.to_dict()
    return {
        "language_id": language_id,
        "dfa": dfa_dict,
        "cytoscape": dfa_to_cytoscape(dfa_dict),
    }


@app.post("/api/generate")
def generate_data(req: GenerateRequest) -> dict[str, Any]:
    """Generate labeled strings using uniform, stratified, random-walk, or characteristic sampling."""
    try:
        if req.target_type == "language":
            ref = get_reference_dfa(req.target)
        else:
            ref = regex_to_dfa(req.target, alphabet=tuple(req.alphabet) if req.alphabet else None)

        if req.sampling_mode == "characteristic":
            examples = generate_characteristic_sample(ref)
        else:
            examples = generate_dataset(
                ref,
                min_length=req.min_length,
                max_length=req.max_length,
                size=req.size,
                positive_ratio=req.positive_ratio,
                noise_rate=req.noise_rate,
                sampling_mode=req.sampling_mode,
                seed=req.seed,
            )

        return {
            "target": req.target,
            "alphabet": list(ref.alphabet),
            "count": len(examples),
            "examples": [ex.to_dict() for ex in examples],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/learn")
def run_learning(req: LearnRequest) -> dict[str, Any]:
    """Run RPNI, EDSM, or L* and return the learned DFA + full step replay history."""
    try:
        if req.algorithm == "lstar":
            if not req.target_language:
                raise ValueError("algorithm='lstar' requires 'target_language' to serve as oracle.")
            target_dfa = get_reference_dfa(req.target_language)
            result = learn_lstar_from_dfa(target_dfa)
        else:
            if not req.examples:
                raise ValueError("Learning requires non-empty 'examples'.")
            pairs = [(item.string, item.label) for item in req.examples]
            if req.algorithm == "edsm":
                result = learn_edsm(pairs, alphabet=req.alphabet, strict=req.strict)
            elif req.algorithm == "rpni":
                result = learn_rpni(pairs, alphabet=req.alphabet, strict=req.strict)
            else:
                raise ValueError(f"Unknown algorithm {req.algorithm!r}")

        dfa_dict = result.dfa.to_dict()
        steps_payload = []
        for step in result.steps:
            st_dict = step.to_dict()
            # If step contains a dfa snapshot, attach Cytoscape elements to enable instant replay
            if "dfa" in step.data and isinstance(step.data["dfa"], dict):
                st_dict["cytoscape"] = dfa_to_cytoscape(step.data["dfa"])
            steps_payload.append(st_dict)

        return {
            "algorithm": result.algorithm,
            "dfa": dfa_dict,
            "cytoscape": dfa_to_cytoscape(dfa_dict),
            "steps": steps_payload,
            "metadata": result.metadata,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/simulate")
def simulate_string(req: SimulateRequest) -> dict[str, Any]:
    """Simulate a string on a DFA, returning acceptance and state-by-state token path."""
    try:
        if req.dfa is not None:
            dfa = DFA.from_dict(req.dfa)
        elif req.language_id is not None:
            dfa = get_reference_dfa(req.language_id)
        else:
            raise ValueError("Provide either 'dfa' or 'language_id'.")

        accepted, path = dfa.accepts(req.string)
        # Build path transitions for token edge animation
        transitions_taken: list[dict[str, str]] = []
        for idx in range(len(path) - 1):
            transitions_taken.append(
                {
                    "from_state": path[idx],
                    "symbol": req.string[idx],
                    "to_state": path[idx + 1],
                    "edge_id": f"e_{path[idx]}_{path[idx + 1]}",
                }
            )

        return {
            "string": req.string,
            "accepted": accepted,
            "path": path,
            "transitions_taken": transitions_taken,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/compare")
def compare_with_reference(req: CompareRequest) -> dict[str, Any]:
    """Diff a candidate DFA against reference DFA, computing accuracy and counterexample."""
    try:
        candidate = DFA.from_dict(req.dfa)
        ref_dfa = get_reference_dfa(req.reference_language_id)

        split = generate_train_test_split(
            ref_dfa,
            train_size=10,
            test_size=req.test_size,
            seed=101,
        )
        metrics = evaluate_dfa(candidate, split.test, reference_dfa=ref_dfa)

        # Identify specific disagreeing strings for display
        disagreements = []
        for ex in split.test:
            cand_pred = candidate.matches(ex.string)
            if cand_pred != ex.true_label:
                disagreements.append(
                    {
                        "string": ex.string,
                        "candidate_predicted": cand_pred,
                        "true_label": ex.true_label,
                    }
                )
                if len(disagreements) >= 12:
                    break

        return {
            "metrics": metrics.to_dict(),
            "reference_states": len(ref_dfa.states),
            "candidate_states": len(candidate.states),
            "disagreements": disagreements,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/experiments/learning-curve")
def api_learning_curve(req: LearningCurveRequest) -> dict[str, Any]:
    """Run learning curve benchmark across sizes and seeds."""
    try:
        report = run_learning_curve(
            req.language_id,
            train_sizes=req.train_sizes,
            learners=req.learners,  # type: ignore[arg-type]
            seeds=req.seeds,
        )
        return report.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/experiments/noise-study")
def api_noise_study(req: NoiseStudyRequest) -> dict[str, Any]:
    """Run noise degradation benchmark."""
    try:
        report = run_noise_study(
            req.language_id,
            noise_rates=req.noise_rates,
            learners=req.learners,  # type: ignore[arg-type]
            train_size=req.train_size,
            seeds=req.seeds,
        )
        return report.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/experiments/active-study")
def api_active_study(req: ActiveStudyRequest) -> dict[str, Any]:
    """Run active learning vs. random sampling benchmark."""
    try:
        comp = run_active_vs_random_study(
            req.language_id,
            initial_size=req.initial_size,
            batch_size=req.batch_size,
            rounds=req.rounds,
            seed=req.seed,
        )
        return comp.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/experiments/clustering")
def api_clustering(req: ClusterRequest) -> dict[str, Any]:
    """Cluster strings according to the DFA state they end in."""
    try:
        dfa = DFA.from_dict(req.dfa)
        clusters = cluster_strings_by_end_state(dfa, req.strings)
        return {"clusters": clusters}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Mount Static Frontend
# ---------------------------------------------------------------------------

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

