import copy
import hashlib
import json
from pathlib import Path

from tools.registry.generate_registry_v2_conformance_report import build_report
from tools.registry.registry_v2_conformance import evaluate_python

CORPUS = Path(__file__).parent / "fixtures" / "registry_v2_conformance.json"


def test_python_conformance_adapter_emits_every_corpus_case():
    corpus = json.loads(CORPUS.read_text())
    result = evaluate_python(corpus)
    expected_count = sum(
        len(corpus[key])
        for key in (
            "record_cases",
            "identity_cases",
            "type_id_vectors",
            "creation_cases",
            "transition_cases",
            "script_cases",
            "discovery_cases",
        )
    )

    assert result["implementation"] == "python"
    assert len(result["results"]) == expected_count
    assert len({case["id"] for case in result["results"]}) == expected_count


def test_conformance_report_requires_exact_three_way_agreement():
    corpus_bytes = CORPUS.read_bytes()
    corpus = json.loads(corpus_bytes)
    python_result = evaluate_python(corpus)
    runtime_results = {}
    for implementation in ("rust", "python", "typescript"):
        result = copy.deepcopy(python_result)
        result["implementation"] = implementation
        runtime_results[implementation] = result

    passing = build_report(corpus, corpus_bytes, runtime_results)
    assert passing["corpus_sha256"] == hashlib.sha256(corpus_bytes).hexdigest()
    assert passing["summary"]["conformant"] is True
    assert passing["summary"]["assertion_count"] == passing["summary"]["case_count"] * 3

    runtime_results["typescript"]["results"][0]["outcome"]["accepted"] = False
    failing = build_report(corpus, corpus_bytes, runtime_results)
    assert failing["summary"]["conformant"] is False
    assert failing["summary"]["cross_language_equal"] is False
