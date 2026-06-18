# ABOUTME: ESO controller must have a WIF-bound GSA with secretmanager.secretAccessor.
# ABOUTME: Without it, every ExternalSecret reconcile fails with permission denied.

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


IAM_TF = PROJECT_ROOT / "infrastructure" / "terraform" / "iam.tf"
VARIABLES_TF = PROJECT_ROOT / "infrastructure" / "terraform" / "variables.tf"
ESO_SA_MANIFEST_DIR = PROJECT_ROOT / "gitops" / "apps"
ESO_APP_YAML = ESO_SA_MANIFEST_DIR / "external-secrets.yaml"


@pytest.mark.static
def test_iam_tf_declares_eso_controller_service_account() -> None:
    text = IAM_TF.read_text()
    assert re.search(
        r'resource\s+"google_service_account"\s+"eso_controller"', text
    ), "iam.tf must declare a google_service_account.eso_controller resource"


@pytest.mark.static
def test_eso_controller_has_secret_accessor_binding() -> None:
    text = IAM_TF.read_text()
    # Look for an IAM member binding tying the eso_controller GSA to
    # roles/secretmanager.secretAccessor at the project level.
    assert re.search(
        r"roles/secretmanager\.secretAccessor", text
    ), "ESO controller must have roles/secretmanager.secretAccessor"
    assert re.search(
        r"google_service_account\.eso_controller\.email", text
    ), "the secret-accessor binding must reference eso_controller.email"


@pytest.mark.static
def test_eso_wif_binding_targets_external_secrets_ksa() -> None:
    """WIF binding must let the external-secrets/external-secrets KSA impersonate the GSA."""
    text = IAM_TF.read_text()
    # The member string follows the WIF pattern:
    # serviceAccount:<project>.svc.id.goog[<namespace>/<ksa-name>]
    assert re.search(
        r"svc\.id\.goog\[external-secrets/external-secrets\]", text
    ), (
        "iam.tf must declare a WIF binding for the external-secrets KSA "
        "in the external-secrets namespace (the ESO controller pod)"
    )


@pytest.mark.static
def test_eso_controller_account_id_variable_declared() -> None:
    text = VARIABLES_TF.read_text()
    assert re.search(
        r'variable\s+"eso_controller_service_account_id"', text
    ), "variables.tf must declare eso_controller_service_account_id"


@pytest.mark.static
def test_eso_app_ksa_annotation_no_longer_placeholder() -> None:
    """The external-secrets Application's WIF annotation must be substituted."""
    docs = list(yaml.safe_load_all(ESO_APP_YAML.read_text()))
    app = next(d for d in docs if d.get("kind") == "Application")
    annotations = (
        app["spec"]["source"]
        .get("helm", {})
        .get("valuesObject", {})
        .get("serviceAccount", {})
        .get("annotations", {})
        or {}
    )
    gsa_email = annotations.get("iam.gke.io/gcp-service-account", "")
    assert "REPLACE_WITH" not in gsa_email, (
        f"ESO controller serviceAccount annotation still a placeholder: "
        f"{gsa_email!r}"
    )
    assert "eso-controller" in gsa_email or "eso_controller" in gsa_email, (
        f"annotation should point at the eso-controller GSA; got {gsa_email!r}"
    )
