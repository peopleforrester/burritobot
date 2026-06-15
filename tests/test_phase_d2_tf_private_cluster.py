# ABOUTME: Phase D2 test — gke.tf must declare private nodes + authorized networks (C12).
# ABOUTME: Without these, GKE worker nodes get public IPs and the control plane is wide-open.

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT


GKE_TF = PROJECT_ROOT / "infrastructure" / "terraform" / "gke.tf"
VARIABLES_TF = PROJECT_ROOT / "infrastructure" / "terraform" / "variables.tf"


@pytest.mark.static
def test_private_cluster_config_block_present() -> None:
    text = GKE_TF.read_text()
    assert re.search(r"private_cluster_config\s*{", text), (
        "gke.tf must declare a private_cluster_config block — without it, "
        "GKE worker nodes get public IPs and the NAT gateway in vpc.tf is "
        "pointless"
    )


@pytest.mark.static
def test_private_nodes_enabled() -> None:
    text = GKE_TF.read_text()
    block = re.search(r"private_cluster_config\s*{[^}]*}", text, re.DOTALL)
    assert block, "private_cluster_config block missing"
    assert re.search(r"enable_private_nodes\s*=\s*true", block.group(0)), (
        "enable_private_nodes must be true (closes C12)"
    )


@pytest.mark.static
def test_master_ipv4_cidr_block_set() -> None:
    text = GKE_TF.read_text()
    block = re.search(r"private_cluster_config\s*{[^}]*}", text, re.DOTALL)
    assert block, "private_cluster_config block missing"
    assert re.search(r"master_ipv4_cidr_block\s*=", block.group(0)), (
        "master_ipv4_cidr_block must be set inside private_cluster_config"
    )


@pytest.mark.static
def test_master_authorized_networks_present() -> None:
    text = GKE_TF.read_text()
    assert re.search(
        r"master_authorized_networks_config\s*{", text
    ), (
        "gke.tf must declare master_authorized_networks_config so the "
        "control plane is reachable only from known CIDRs (no 0.0.0.0/0 "
        "blanket allow)"
    )


@pytest.mark.static
def test_variables_declare_master_cidrs() -> None:
    text = VARIABLES_TF.read_text()
    assert re.search(r'variable\s+"master_ipv4_cidr_block"', text), (
        "variables.tf must declare master_ipv4_cidr_block variable"
    )
    assert re.search(r'variable\s+"master_authorized_cidrs"', text), (
        "variables.tf must declare master_authorized_cidrs variable"
    )
