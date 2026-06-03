# ABOUTME: Phase B6 test — Loki + Tempo + Promtail Applications adapted from EKS to GKE.
# ABOUTME: Asserts no S3 backends, no gp2 storage class (AWS-specific), targets monitoring ns.

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


GITOPS_APPS = PROJECT_ROOT / "gitops" / "apps"
LOKI_APP = GITOPS_APPS / "loki.yaml"
TEMPO_APP = GITOPS_APPS / "tempo.yaml"
PROMTAIL_APP = GITOPS_APPS / "promtail.yaml"

AWS_PATTERNS = [
    re.compile(r"eks\.amazonaws\.com"),
    re.compile(r"\.dkr\.ecr\."),
    re.compile(r"arn:aws:"),
    re.compile(r"\baws_iam_role\b"),
    # AWS-only storage class — match only the config key form so the test
    # does not flag history-explaining comments about the swap.
    re.compile(r"storageClass(?:Name)?:\s*gp[23]\b"),
    # S3 storage backend would need IRSA — not in scope here.
    re.compile(r"backend:\s*s3\b", re.IGNORECASE),
    re.compile(r"object_store:\s*s3\b", re.IGNORECASE),
]


def _all_docs(path: Path) -> list[dict]:
    with path.open() as fp:
        return [d for d in yaml.safe_load_all(fp) if d]


def _assert_no_aws_strings(path: Path) -> None:
    text = path.read_text()
    for pat in AWS_PATTERNS:
        match = pat.search(text)
        assert not match, (
            f"{path.name}: AWS-specific token {pat.pattern!r} still present "
            f"(matched: {match.group(0)!r}) — replace with GKE equivalent "
            f"(standard storage class, filesystem/local backend, or gcs+WIF)"
        )


@pytest.mark.parametrize(
    "app_path,expected_name",
    [
        (LOKI_APP, "loki"),
        (TEMPO_APP, "tempo"),
        (PROMTAIL_APP, "promtail"),
    ],
    ids=lambda x: x.name if isinstance(x, Path) else x,
)
@pytest.mark.static
def test_application_exists_and_targets_monitoring(
    app_path: Path, expected_name: str
) -> None:
    assert app_path.is_file(), f"missing {app_path}"
    doc = _all_docs(app_path)[0]
    assert doc["kind"] == "Application"
    assert doc["metadata"]["name"] == expected_name
    assert doc["spec"]["destination"]["namespace"] == "monitoring"


@pytest.mark.parametrize(
    "app_path",
    [LOKI_APP, TEMPO_APP, PROMTAIL_APP],
    ids=lambda x: x.name,
)
@pytest.mark.static
def test_no_aws_strings(app_path: Path) -> None:
    _assert_no_aws_strings(app_path)


@pytest.mark.static
def test_loki_storage_backend_not_s3() -> None:
    """Loki on EKS often uses S3 chunks; for demo, filesystem is simplest."""
    doc = _all_docs(LOKI_APP)[0]
    values = doc["spec"]["source"].get("helm", {}).get("valuesObject", {})
    storage = values.get("loki", {}).get("storage", {})
    storage_type = storage.get("type", "")
    assert storage_type in ("filesystem", "gcs"), (
        f"Loki storage.type must be filesystem (demo) or gcs (persistent); "
        f"got {storage_type!r}"
    )


@pytest.mark.static
def test_tempo_storage_backend_not_s3() -> None:
    doc = _all_docs(TEMPO_APP)[0]
    values = doc["spec"]["source"].get("helm", {}).get("valuesObject", {})
    backend = (
        values.get("tempo", {})
        .get("storage", {})
        .get("trace", {})
        .get("backend", "")
    )
    assert backend in ("local", "gcs"), (
        f"Tempo storage backend must be local (demo) or gcs (persistent); "
        f"got {backend!r}"
    )


@pytest.mark.static
def test_promtail_points_at_loki_in_monitoring() -> None:
    doc = _all_docs(PROMTAIL_APP)[0]
    values = doc["spec"]["source"].get("helm", {}).get("valuesObject", {})
    clients = values.get("config", {}).get("clients", [])
    assert clients, "Promtail must have at least one push client configured"
    urls = [c.get("url", "") for c in clients]
    assert any("loki" in u for u in urls), (
        f"Promtail must push to a loki URL; got {urls}"
    )
