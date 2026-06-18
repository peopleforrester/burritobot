# ABOUTME: Terraform input variables for burritbot GCP foundation.
# ABOUTME: All defaults are Phase 1 placeholders — override in terraform.tfvars.

variable "project_id" {
  description = "GCP project ID hosting the burritbot demo cluster."
  type        = string
}

variable "region" {
  description = "GCP region for the GKE cluster and regional resources."
  type        = string
  default     = "us-west1"
}

variable "cluster_name" {
  description = "Name of the GKE Standard cluster."
  type        = string
  default     = "burritbot"
}

variable "network_name" {
  description = "Name of the VPC network."
  type        = string
  default     = "burritbot-vpc"
}

variable "subnet_name" {
  description = "Name of the regional subnetwork."
  type        = string
  default     = "burritbot-subnet"
}

variable "subnet_cidr" {
  description = "Primary CIDR range for the GKE subnet."
  type        = string
  default     = "10.20.0.0/20"
}

variable "pods_cidr" {
  description = "Secondary range for pod IPs."
  type        = string
  default     = "10.24.0.0/14"
}

variable "services_cidr" {
  description = "Secondary range for Kubernetes service IPs."
  type        = string
  default     = "10.28.0.0/20"
}

variable "node_service_account_id" {
  description = "Account ID of the GKE node service account (no JSON keys)."
  type        = string
  default     = "burritbot-gke-nodes"
}

variable "workload_service_account_id" {
  description = "Account ID of the WIF-bound workload service account."
  type        = string
  default     = "burritbot-workload"
}

variable "eso_controller_service_account_id" {
  description = "Account ID of the WIF-bound External Secrets Operator controller GSA."
  type        = string
  default     = "eso-controller"
}

variable "vertex_secret_id" {
  description = "Secret Manager secret ID holding any Vertex AI quota metadata."
  type        = string
  default     = "burritbot-vertex-ai"
}

variable "master_ipv4_cidr_block" {
  description = "Private /28 used for the GKE control plane peering range."
  type        = string
  default     = "172.16.0.0/28"
}

variable "master_authorized_cidrs" {
  description = "CIDR blocks allowed to reach the GKE control plane API."
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = []
}
