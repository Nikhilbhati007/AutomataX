"""Phase 5 unit and integration tests for FastAPI backend endpoints."""

import pytest

from core import get_reference_dfa
from web.api import (
    CompareRequest,
    GenerateRequest,
    LearnRequest,
    LearningCurveRequest,
    NoiseStudyRequest,
    SimulateRequest,
    api_learning_curve,
    api_noise_study,
    compare_with_reference,
    dfa_to_cytoscape,
    generate_data,
    get_reference_machine,
    list_languages,
    list_presets,
    run_learning,
    simulate_string,
)


def test_dfa_to_cytoscape_format():
    dfa = get_reference_dfa("ends_with_ab")
    elements = dfa_to_cytoscape(dfa.to_dict())

    nodes = [e for e in elements if "target" not in e["data"]]
    edges = [e for e in elements if "target" in e["data"]]

    assert len(nodes) == len(dfa.states) == 3
    start_nodes = [n for n in nodes if n["data"]["is_start"]]
    assert len(start_nodes) == 1
    assert start_nodes[0]["data"]["id"] == dfa.start

    accept_nodes = [n for n in nodes if n["data"]["is_accept"]]
    assert len(accept_nodes) == len(dfa.accept_states) == 1
    assert edges


def test_list_languages_endpoint():
    data = list_languages()
    assert "languages" in data
    ids = {l["id"] for l in data["languages"]}
    assert "ends_with_ab" in ids
    assert "even_ones" in ids
    assert "third_from_end_a" in ids


def test_list_presets_endpoint():
    data = list_presets()
    assert "presets" in data
    assert len(data["presets"]) >= 4


def test_get_reference_dfa_endpoint():
    data = get_reference_machine("ends_with_ab")
    assert data["language_id"] == "ends_with_ab"
    assert "dfa" in data
    assert "cytoscape" in data
    assert len(data["dfa"]["states"]) == 3


def test_generate_data_endpoint():
    req = GenerateRequest(
        target_type="language",
        target="ends_with_ab",
        size=25,
        sampling_mode="length_stratified",
        seed=42,
    )
    data = generate_data(req)
    assert data["count"] == 25
    assert len(data["examples"]) == 25
    assert all("string" in ex and "label" in ex for ex in data["examples"])


def test_learn_endpoint_edsm_and_rpni():
    examples = [
        {"string": "ab", "label": True},
        {"string": "aab", "label": True},
        {"string": "bab", "label": True},
        {"string": "a", "label": False},
        {"string": "b", "label": False},
        {"string": "ba", "label": False},
    ]

    # Test EDSM
    req_edsm = LearnRequest(
        algorithm="edsm",
        examples=[{"string": e["string"], "label": e["label"]} for e in examples],  # type: ignore[arg-type]
        alphabet=["a", "b"],
    )
    data_edsm = run_learning(req_edsm)
    assert data_edsm["algorithm"] == "edsm"
    assert "dfa" in data_edsm
    assert "cytoscape" in data_edsm
    assert "steps" in data_edsm
    assert len(data_edsm["steps"]) > 0

    # Test RPNI
    req_rpni = LearnRequest(
        algorithm="rpni",
        examples=[{"string": e["string"], "label": e["label"]} for e in examples],  # type: ignore[arg-type]
        alphabet=["a", "b"],
    )
    data_rpni = run_learning(req_rpni)
    assert data_rpni["algorithm"] == "rpni"


def test_learn_endpoint_lstar():
    req_lstar = LearnRequest(algorithm="lstar", target_language="even_ones")
    data_lstar = run_learning(req_lstar)
    assert data_lstar["algorithm"] == "lstar"
    assert len(data_lstar["dfa"]["states"]) == 2


def test_simulate_endpoint():
    ref = get_reference_dfa("ends_with_ab").to_dict()
    req = SimulateRequest(dfa=ref, string="aab")
    data = simulate_string(req)
    assert data["accepted"] is True
    assert len(data["path"]) == 4
    assert len(data["transitions_taken"]) == 3


def test_compare_endpoint():
    ref = get_reference_dfa("ends_with_ab").to_dict()
    req = CompareRequest(dfa=ref, reference_language_id="ends_with_ab", test_size=40)
    data = compare_with_reference(req)
    assert data["metrics"]["is_equivalent"] is True
    assert data["metrics"]["accuracy"] == 1.0
    assert len(data["disagreements"]) == 0


def test_experiment_endpoints():
    req_lc = LearningCurveRequest(
        language_id="ends_with_ab",
        train_sizes=[10, 30],
        learners=["edsm"],
        seeds=[0],
    )
    data_lc = api_learning_curve(req_lc)
    assert len(data_lc["points"]) == 2

    req_ns = NoiseStudyRequest(
        language_id="even_ones",
        noise_rates=[0.0, 0.10],
        learners=["edsm"],
        train_size=30,
        seeds=[0],
    )
    data_ns = api_noise_study(req_ns)
    assert len(data_ns["points"]) == 2
