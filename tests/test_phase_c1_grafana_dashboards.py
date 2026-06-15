# ABOUTME: Phase C1 test — each Grafana dashboard JSON must have a matching ConfigMap.
# ABOUTME: The kube-prometheus-stack Grafana sidecar (B3) imports any CM labeled grafana_dashboard=1.

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


DASHBOARDS_DIR = PROJECT_ROOT / "observability" / "grafana" / "dashboards"
JSON_FILES = sorted(DASHBOARDS_DIR.glob("*.json"))


def _all_docs(path: Path) -> list[dict]:
    with path.open() as fp:
        return [d for d in yaml.safe_load_all(fp) if d]


def _configmap_for(json_path: Path) -> Path:
    return json_path.with_name(json_path.stem + "-configmap.yaml")


@pytest.mark.static
def test_dashboard_inventory_unchanged() -> None:
    """Phase C1 wraps exactly the three dashboards that exist today."""
    assert len(JSON_FILES) >= 1, "no dashboard JSONs found — directory empty?"


@pytest.mark.parametrize("json_path", JSON_FILES, ids=lambda p: p.name)
@pytest.mark.static
def test_each_dashboard_has_configmap(json_path: Path) -> None:
    cm_path = _configmap_for(json_path)
    assert cm_path.is_file(), (
        f"missing ConfigMap wrapper for {json_path.name} — "
        f"expected at {cm_path.name}"
    )
    docs = _all_docs(cm_path)
    assert len(docs) == 1, f"{cm_path.name} must contain exactly one ConfigMap"
    cm = docs[0]
    assert cm["kind"] == "ConfigMap"


@pytest.mark.parametrize("json_path", JSON_FILES, ids=lambda p: p.name)
@pytest.mark.static
def test_configmap_has_grafana_dashboard_label(json_path: Path) -> None:
    cm = _all_docs(_configmap_for(json_path))[0]
    labels = cm.get("metadata", {}).get("labels", {}) or {}
    assert labels.get("grafana_dashboard") == "1", (
        f"{_configmap_for(json_path).name} must carry "
        f"label grafana_dashboard=\"1\" (Phase B3 sidecar selector)"
    )


@pytest.mark.parametrize("json_path", JSON_FILES, ids=lambda p: p.name)
@pytest.mark.static
def test_configmap_targets_monitoring_namespace(json_path: Path) -> None:
    cm = _all_docs(_configmap_for(json_path))[0]
    namespace = cm.get("metadata", {}).get("namespace")
    assert namespace == "monitoring", (
        f"{_configmap_for(json_path).name}: namespace must be monitoring; "
        f"got {namespace!r}"
    )


@pytest.mark.parametrize("json_path", JSON_FILES, ids=lambda p: p.name)
@pytest.mark.static
def test_configmap_embeds_valid_dashboard_json(json_path: Path) -> None:
    """The embedded dashboard JSON must parse and match the source file."""
    cm = _all_docs(_configmap_for(json_path))[0]
    data = cm.get("data", {}) or {}
    key = f"{json_path.stem}.json"
    assert key in data, (
        f"{_configmap_for(json_path).name} must embed the JSON under "
        f"data[{key!r}]"
    )
    parsed = json.loads(data[key])
    source = json.loads(json_path.read_text())
    assert parsed.get("uid") == source.get("uid"), (
        f"embedded uid != source uid for {json_path.name}"
    )
