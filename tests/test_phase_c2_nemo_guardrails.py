# ABOUTME: Phase C2 test — NeMo Guardrails Deployment + Service + 2 ConfigMaps under ai-gateway/.
# ABOUTME: Cross-checks ConfigMap names with the Deployment volumes block; enforces hardening defaults.

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


NEMO_DIR = PROJECT_ROOT / "ai-gateway" / "nemo-guardrails"
DEPLOYMENT = NEMO_DIR / "deployment.yaml"
CONFIGMAP_CONFIG = NEMO_DIR / "configmap-config.yaml"
CONFIGMAP_RAILS = NEMO_DIR / "configmap-rails.yaml"


def _all_docs(path: Path) -> list[dict]:
    with path.open() as fp:
        return [d for d in yaml.safe_load_all(fp) if d]


def _kinds(path: Path) -> set[str]:
    return {d.get("kind") for d in _all_docs(path)}


@pytest.mark.static
def test_deployment_and_service_exist() -> None:
    assert DEPLOYMENT.is_file(), f"missing {DEPLOYMENT}"
    kinds = _kinds(DEPLOYMENT)
    assert "Deployment" in kinds, "Deployment kind must be present"
    assert "Service" in kinds, "Service kind must be present"


@pytest.mark.static
def test_configmaps_exist() -> None:
    assert CONFIGMAP_CONFIG.is_file(), f"missing {CONFIGMAP_CONFIG}"
    assert CONFIGMAP_RAILS.is_file(), f"missing {CONFIGMAP_RAILS}"
    assert "ConfigMap" in _kinds(CONFIGMAP_CONFIG)
    assert "ConfigMap" in _kinds(CONFIGMAP_RAILS)


@pytest.mark.static
def test_targets_burritbot_net_namespace() -> None:
    for path in (DEPLOYMENT, CONFIGMAP_CONFIG, CONFIGMAP_RAILS):
        for doc in _all_docs(path):
            ns = doc.get("metadata", {}).get("namespace")
            assert ns == "burritbot-net", (
                f"{path.name}: {doc['kind']} namespace must be burritbot-net; "
                f"got {ns!r}"
            )


@pytest.mark.static
def test_deployment_mounts_match_configmap_names() -> None:
    """Cross-check: every volume.configMap.name must match an actual ConfigMap."""
    deployment = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Deployment")
    volumes = deployment["spec"]["template"]["spec"].get("volumes", [])
    cm_refs = {
        v["configMap"]["name"]
        for v in volumes
        if "configMap" in v
    }
    cm_names = {
        d["metadata"]["name"]
        for path in (CONFIGMAP_CONFIG, CONFIGMAP_RAILS)
        for d in _all_docs(path)
        if d["kind"] == "ConfigMap"
    }
    missing = cm_refs - cm_names
    assert not missing, (
        f"Deployment references ConfigMap names that do not exist: {missing}"
    )


@pytest.mark.static
def test_image_pinned_not_latest() -> None:
    deployment = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Deployment")
    containers = deployment["spec"]["template"]["spec"]["containers"]
    for c in containers:
        image = c["image"]
        assert ":" in image, f"container {c['name']!r}: image must include a tag"
        tag = image.rsplit(":", 1)[1]
        assert tag != "latest", (
            f"container {c['name']!r}: image tag 'latest' is forbidden — pin a version"
        )


@pytest.mark.static
def test_otel_endpoint_env_present() -> None:
    deployment = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Deployment")
    containers = deployment["spec"]["template"]["spec"]["containers"]
    found = False
    for c in containers:
        env = c.get("env", []) or []
        if any(e.get("name") == "OTEL_EXPORTER_OTLP_ENDPOINT" for e in env):
            found = True
            break
    assert found, "at least one container must export OTEL_EXPORTER_OTLP_ENDPOINT"


@pytest.mark.static
def test_pod_security_hardened() -> None:
    deployment = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Deployment")
    pod = deployment["spec"]["template"]["spec"]
    sc = pod.get("securityContext", {}) or {}
    assert sc.get("runAsNonRoot") is True, "pod must run as non-root"
    assert sc.get("runAsUser", 0) >= 1001, "pod uid must be >= 1001"
    for c in pod["containers"]:
        csc = c.get("securityContext", {}) or {}
        assert csc.get("allowPrivilegeEscalation") is False
        assert csc.get("readOnlyRootFilesystem") is True
        caps = csc.get("capabilities", {}) or {}
        assert caps.get("drop") == ["ALL"], (
            f"container {c['name']!r} must drop ALL capabilities"
        )


@pytest.mark.static
def test_service_exposes_named_port() -> None:
    service = next(d for d in _all_docs(DEPLOYMENT) if d["kind"] == "Service")
    ports = service["spec"]["ports"]
    assert ports, "Service must expose at least one port"
    # NeMo Guardrails microservice default REST port is 8000.
    expected_ports = {p["port"] for p in ports}
    assert 8000 in expected_ports, (
        f"Service must expose port 8000 (NeMo default); got {expected_ports}"
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
def test_rails_configmap_carries_all_four_rails() -> None:
    """The rails ConfigMap must include all .co files under rails/."""
    rails_dir = NEMO_DIR / "rails"
    expected = {p.name for p in rails_dir.glob("*.co")}
    cm = next(d for d in _all_docs(CONFIGMAP_RAILS) if d["kind"] == "ConfigMap")
    actual = set(cm.get("data", {}).keys())
    missing = expected - actual
    assert not missing, (
        f"rails ConfigMap is missing .co files: {missing}"
    )
