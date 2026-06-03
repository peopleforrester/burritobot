# ABOUTME: Phase B7 test — Kyverno install App carries the full EKS-reference values.
# ABOUTME: Asserts webhook namespace exclusions + per-controller resource limits are wired.

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


KYVERNO_APP = PROJECT_ROOT / "gitops" / "apps" / "05-kyverno.yaml"


def _all_docs(path: Path) -> list[dict]:
    with path.open() as fp:
        return [d for d in yaml.safe_load_all(fp) if d]


@pytest.mark.static
def test_kyverno_application_exists() -> None:
    assert KYVERNO_APP.is_file(), f"missing {KYVERNO_APP}"
    doc = _all_docs(KYVERNO_APP)[0]
    assert doc["kind"] == "Application"
    assert doc["metadata"]["name"] == "kyverno"


@pytest.mark.static
def test_kyverno_chart_pinned_and_targets_security() -> None:
    doc = _all_docs(KYVERNO_APP)[0]
    src = doc["spec"]["source"]
    assert src["chart"] == "kyverno"
    assert src.get("targetRevision"), "chart targetRevision must be pinned"
    assert doc["spec"]["destination"]["namespace"] == "security"


@pytest.mark.static
def test_kyverno_webhook_excludes_kube_system_namespaces() -> None:
    """Admission webhook exclusions must exclude system namespaces to avoid lockouts."""
    doc = _all_docs(KYVERNO_APP)[0]
    values = doc["spec"]["source"].get("helm", {}).get("valuesObject", {})
    exprs = (
        values.get("config", {})
        .get("webhooks", {})
        .get("namespaceSelector", {})
        .get("matchExpressions", [])
    )
    found = next(
        (
            e
            for e in exprs
            if e.get("key") == "kubernetes.io/metadata.name"
            and e.get("operator") == "NotIn"
        ),
        None,
    )
    assert found is not None, (
        "kyverno config.webhooks.namespaceSelector must have a NotIn "
        "matchExpression on kubernetes.io/metadata.name (system-namespace "
        "exclusion); otherwise webhook recursion can deadlock the cluster"
    )
    for ns in ("kube-system", "kube-public"):
        assert ns in found["values"], (
            f"system namespace {ns!r} must be in the webhook exclusion list"
        )


@pytest.mark.static
def test_kyverno_controllers_have_resource_limits() -> None:
    """Every Kyverno controller must declare requests + limits — chart defaults are absent."""
    doc = _all_docs(KYVERNO_APP)[0]
    values = doc["spec"]["source"].get("helm", {}).get("valuesObject", {})
    for controller in (
        "admissionController",
        "backgroundController",
        "cleanupController",
        "reportsController",
    ):
        c = values.get(controller, {})
        assert "resources" in c, (
            f"{controller}.resources missing — declare CPU/memory requests "
            f"and limits per Kubernetes best practice"
        )
        assert "requests" in c["resources"] and "limits" in c["resources"], (
            f"{controller}.resources must have both requests and limits"
        )
