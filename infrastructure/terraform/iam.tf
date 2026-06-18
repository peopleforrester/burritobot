# ABOUTME: IAM for burritbot — WIF-bound workload SA and node SA with minimum scopes.
# ABOUTME: No JSON credential resources; Workload Identity Federation is the only path.

# Node service account: attached to the GKE node pools created by NAP.
# Gets only the minimum cloud-platform scope needed for logging and metrics.
resource "google_service_account" "nodes" {
  account_id   = var.node_service_account_id
  display_name = "burritbot GKE node service account"
  description  = "Attached to GKE nodes via NAP. No direct workload use."
}

resource "google_project_iam_member" "nodes_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.nodes.email}"
}

resource "google_project_iam_member" "nodes_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.nodes.email}"
}

resource "google_project_iam_member" "nodes_monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.nodes.email}"
}

# Workload service account: bound via Workload Identity Federation to the
# Kubernetes service account that BurritBot uses. No JSON key is generated.
resource "google_service_account" "workload" {
  account_id   = var.workload_service_account_id
  display_name = "burritbot workload service account (WIF)"
  description  = "Federated to the burritbot KSA. Never has a JSON key."
}

resource "google_project_iam_member" "workload_vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.workload.email}"
}

resource "google_project_iam_member" "workload_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.workload.email}"
}

# WIF binding: allow the burritbot Kubernetes service account to impersonate
# the workload GSA. The KSA lives in the burritbot-guarded namespace.
resource "google_service_account_iam_member" "workload_wif_binding" {
  service_account_id = google_service_account.workload.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[burritbot-guarded/burritbot]"
}

# External Secrets Operator controller service account: WIF-bound to the
# external-secrets KSA in the external-secrets namespace so the controller
# can read GCP Secret Manager values through the ClusterSecretStore.
resource "google_service_account" "eso_controller" {
  account_id   = var.eso_controller_service_account_id
  display_name = "External Secrets Operator controller (WIF)"
  description  = "Federated to the external-secrets/external-secrets KSA. No JSON key."
}

resource "google_project_iam_member" "eso_controller_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.eso_controller.email}"
}

resource "google_service_account_iam_member" "eso_controller_wif_binding" {
  service_account_id = google_service_account.eso_controller.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[external-secrets/external-secrets]"
}
