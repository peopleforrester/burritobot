# ABOUTME: GKE Standard cluster with Node Auto-Provisioning and Workload Identity.
# ABOUTME: Autopilot is explicitly off — Falco DaemonSet requires privileged containers.

resource "google_container_cluster" "burritbot" {
  name     = var.cluster_name
  location = var.region

  # GKE Standard: do NOT enable Autopilot. Falco DaemonSet needs privileged
  # containers, which Autopilot forbids. This is the non-negotiable decision
  # from the burritbot spec.
  enable_autopilot = false

  network    = google_compute_network.burritbot.id
  subnetwork = google_compute_subnetwork.burritbot.id

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Workload Identity Federation — no JSON service-account keys anywhere.
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Node Auto-Provisioning with resource limits (required, otherwise NAP is
  # inert). These limits are conservative demo-day budgets.
  cluster_autoscaling {
    enabled = true

    auto_provisioning_defaults {
      service_account = google_service_account.nodes.email
      oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]

      management {
        auto_repair  = true
        auto_upgrade = true
      }

      shielded_instance_config {
        enable_secure_boot          = true
        enable_integrity_monitoring = true
      }
    }

    resource_limits {
      resource_type = "cpu"
      minimum       = 4
      maximum       = 32
    }

    resource_limits {
      resource_type = "memory"
      minimum       = 16
      maximum       = 128
    }
  }

  release_channel {
    channel = "REGULAR"
  }

  # Private nodes: workers get no public IPs (egress via Cloud NAT in vpc.tf).
  # enable_private_endpoint = false leaves the control-plane API reachable
  # from the operator's allow-listed CIDRs via master_authorized_networks
  # below. Flipping to true would lock the control plane to the VPC only.
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_ipv4_cidr_block
  }

  # Restrict who can hit the control plane API. Default keeps it closed
  # to literally nothing; operator overrides via terraform.tfvars before
  # the first apply.
  master_authorized_networks_config {
    dynamic "cidr_blocks" {
      for_each = var.master_authorized_cidrs
      content {
        cidr_block   = cidr_blocks.value.cidr_block
        display_name = cidr_blocks.value.display_name
      }
    }
  }

  # Initial node pool is removed — NAP provisions the real pools. GKE
  # requires a default pool exist at creation, so we create a minimal one
  # and then remove it in a follow-up.
  initial_node_count       = 1
  remove_default_node_pool = true

  # Minimal dataplane and addons tuned for the demo.
  datapath_provider = "ADVANCED_DATAPATH"

  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
  }

  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]
    managed_prometheus {
      enabled = true
    }
  }

  deletion_protection = false
}
