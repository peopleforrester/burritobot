# ABOUTME: Phase C3 test — LLM Guard Deployment + Service + ConfigMap under ai-gateway/llm-guard/.
# ABOUTME: Cross-checks ConfigMap name; enforces non-latest tag, OTel env, non-root hardening.

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


LLM_GUARD_DIR = PROJECT_ROOT / "ai-gateway" / "llm-guard"
DEPLOYMENT = LLM_GUARD_DIR / "deployment.yaml"
CONFIGMAP = LLM_GUARD_DIR / "configmap.yaml"


def _all_docs(path: Path) -> list[dict]:
    with path.open() as fp:
        return [d for d in yaml.safe_load_all(fp) if d]


def _kinds(path: Path) -> set[str]:
    return {d.get("kind") for d in _all_docs(path)}


@pytest.mark.static
def test_deployment_and_service_exist() -> None:
    assert DEPLOYMENT.is_file(), f"missing {DEPLOYMENT}"
    kinds = _kinds(DEPLOYMENT)
    assert "Deployment" in kinds
    assert "Service" in kinds


@pytest.mark.static
def test_configmap_exists() -> None:
    assert CONFIGMAP.is_file(), f"missing {CONFIGMAP}"
    assert "ConfigMap" in _kinds(CONFIGMAP)


@pytest.mark.static
def test_targets_burritbot_net_namespace() -> None:
    for path in (DEPLOYMENT, CONFIGMAP):
        for doc in _all_docs(path):
            ns = doc.get("metadata", {}).get("namespace")
            assert ns == "burritbot-net", (
                f"{path.name}: {doc['kind']} namespace must be burritbot-net; "
                f"got {ns!r}"
            )


@pytest.mark.static
def test_deployment_mount_matches_configmap_name() -> None:
    deployment = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Deployment")
    volumes = deployment["spec"]["template"]["spec"].get("volumes", [])
    cm_refs = {
        v["configMap"]["name"]
        for v in volumes
        if "configMap" in v
    }
    cm = next(d for d in _all_docs(CONFIGMAP) if d["kind"] == "ConfigMap")
    cm_name = cm["metadata"]["name"]
    assert cm_name in cm_refs, (
        f"Deployment volumes do not reference ConfigMap {cm_name!r}; "
        f"got refs {cm_refs}"
    )


@pytest.mark.static
def test_image_pinned_not_latest() -> None:
    deployment = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Deployment")
    for c in deployment["spec"]["template"]["spec"]["containers"]:
        image = c["image"]
        assert ":" in image, f"container {c['name']!r}: image must include a tag"
        tag = image.rsplit(":", 1)[1]
        assert tag != "latest", (
            f"container {c['name']!r}: image tag 'latest' is forbidden"
        )


@pytest.mark.static
def test_otel_endpoint_env_present() -> None:
    deployment = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Deployment")
    containers = deployment["spec"]["template"]["spec"]["containers"]
    found = any(
        e.get("name") == "OTEL_EXPORTER_OTLP_ENDPOINT"
        for c in containers
        for e in (c.get("env") or [])
    )
    assert found, "at least one container must export OTEL_EXPORTER_OTLP_ENDPOINT"


@pytest.mark.static
def test_pod_security_hardened() -> None:
    deployment = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Deployment")
    pod = deployment["spec"]["template"]["spec"]
    sc = pod.get("securityContext", {}) or {}
    assert sc.get("runAsNonRoot") is True
    assert sc.get("runAsUser", 0) >= 1001
    for c in pod["containers"]:
        csc = c.get("securityContext", {}) or {}
        assert csc.get("allowPrivilegeEscalation") is False
        assert csc.get("readOnlyRootFilesystem") is True
        caps = csc.get("capabilities", {}) or {}
        assert caps.get("drop") == ["ALL"]


@pytest.mark.static
def test_service_exposes_port_8000() -> None:
    service = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Service")
    ports = {p["port"] for p in service["spec"]["ports"]}
    assert 8000 in ports, (
        f"Service must expose port 8000 (llm-guard-api default); got {ports}"
    )


@pytest.mark.static
def test_resources_and_probes_set() -> None:
    deployment = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Deployment")
    for c in deployment["spec"]["template"]["spec"]["containers"]:
        assert "resources" in c, f"{c['name']!r}: resources missing"
        assert "requests" in c["resources"] and "limits" in c["resources"]
        assert "readinessProbe" in c, f"{c['name']!r}: readinessProbe missing"
        assert "livenessProbe" in c, f"{c['name']!r}: livenessProbe missing"


@pytest.mark.static
def test_memory_request_at_least_4gi() -> None:
    """LLM Guard ships several transformer models; 16Gi total is the docs ceiling.

    The demo demands at least 4Gi to load even the smallest scanner set.
    """
    deployment = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Deployment")
    for c in deployment["spec"]["template"]["spec"]["containers"]:
        req_mem = c["resources"]["requests"].get("memory", "")
        # very rough — strings like "4Gi" or "4096Mi"
        assert ("Gi" in req_mem or "Mi" in req_mem), (
            f"{c['name']!r}: memory request {req_mem!r} unparseable"
        )
        if "Gi" in req_mem:
            val = float(req_mem.replace("Gi", ""))
        else:
            val = float(req_mem.replace("Mi", "")) / 1024
        assert val >= 4, (
            f"{c['name']!r}: memory request {req_mem} < 4Gi — scanner models "
            f"will OOM at load time"
        )
