# ABOUTME: Phase D1 test — Terraform root module must declare a GCS remote backend.
# ABOUTME: Local state would be unversioned and catastrophic to lose; senior review C11.

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT


MAIN_TF = PROJECT_ROOT / "infrastructure" / "terraform" / "main.tf"
BACKEND_EXAMPLE = PROJECT_ROOT / "infrastructure" / "terraform" / "backend.tf.example"


@pytest.mark.static
def test_terraform_declares_gcs_backend() -> None:
    text = MAIN_TF.read_text()
    # backend "gcs" block must appear inside the terraform {} block.
    assert re.search(
        r'backend\s+"gcs"\s*{', text
    ), (
        "main.tf must declare a GCS remote backend "
        "(terraform { backend \"gcs\" { ... } }); local state is forbidden "
        "for any production-bound apply"
    )


@pytest.mark.static
def test_gcs_backend_bucket_is_placeholder_or_real() -> None:
    """Bucket name must be set (placeholder or real); rejects empty / local."""
    text = MAIN_TF.read_text()
    match = re.search(
        r'backend\s+"gcs"\s*{[^}]*?bucket\s*=\s*"([^"]+)"', text, re.DOTALL
    )
    assert match, "backend gcs block must set bucket = \"...\""
    bucket = match.group(1)
    assert bucket and bucket != "", "bucket value must be non-empty"
    # Either a REPLACE_WITH_ placeholder or a real-looking GCS bucket name.
    assert (
        bucket.startswith("REPLACE_WITH_")
        or re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]", bucket)
    ), f"bucket {bucket!r} is not a valid placeholder or GCS bucket name"


@pytest.mark.static
def test_gcs_backend_has_prefix() -> None:
    """Multiple Terraform configs may share a bucket; require a prefix to namespace state."""
    text = MAIN_TF.read_text()
    block = re.search(r'backend\s+"gcs"\s*{[^}]*}', text, re.DOTALL)
    assert block, "backend gcs block not found"
    assert re.search(r'\bprefix\s*=', block.group(0)), (
        "backend gcs block must declare a `prefix` so the bucket can host "
        "multiple Terraform configs without collision"
    )


@pytest.mark.static
def test_bootstrap_doc_exists() -> None:
    """Operators need an example of the bucket bootstrap commands."""
    assert BACKEND_EXAMPLE.is_file(), (
        f"missing {BACKEND_EXAMPLE.name} — operators need a documented "
        f"example of bucket creation (versioning on) before terraform init"
    )
