# ABOUTME: Phase C4 test — deploy/ai-gateway/kustomization.yaml references the C2 + C3 manifests.
# ABOUTME: Asserts no remaining Phase-C TODO comments after the greenfield resources land.

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


KUSTOMIZATION = PROJECT_ROOT / "deploy" / "ai-gateway" / "kustomization.yaml"

EXPECTED_REFS = [
    "../../ai-gateway/envoy/gateway.yaml",
    "../../ai-gateway/nemo-guardrails/deployment.yaml",
    "../../ai-gateway/nemo-guardrails/configmap-config.yaml",
    "../../ai-gateway/nemo-guardrails/configmap-rails.yaml",
    "../../ai-gateway/llm-guard/deployment.yaml",
    "../../ai-gateway/llm-guard/configmap.yaml",
]


def _kustomization() -> dict:
    with KUSTOMIZATION.open() as fp:
        for doc in yaml.safe_load_all(fp):
            if doc and doc.get("kind") == "Kustomization":
                return doc
    raise AssertionError("no Kustomization in deploy/ai-gateway/")


@pytest.mark.static
@pytest.mark.parametrize("ref", EXPECTED_REFS, ids=lambda r: r.rsplit("/", 1)[-1])
def test_kustomization_references(ref: str) -> None:
    k = _kustomization()
    resources = k.get("resources", []) or []
    assert ref in resources, (
        f"deploy/ai-gateway/kustomization.yaml missing reference to {ref}"
    )


@pytest.mark.static
def test_phase_c_todo_resolved() -> None:
    """Phase C TODOs must be gone now that C2 + C3 landed."""
    text = KUSTOMIZATION.read_text()
    leftover = re.findall(r"TODO\((?:critical-fixes-plan|phase-c)\)", text)
    assert not leftover, (
        f"deploy/ai-gateway/kustomization.yaml still has Phase C TODO "
        f"comments: {leftover}"
    )
