# ABOUTME: Terraform root module for burritbot — pins google provider and project.
# ABOUTME: All GCP resources live under this module; no AWS, no service-account JSON keys.

terraform {
  required_version = ">= 1.8.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.0"
    }
  }

  # Remote state in GCS — object versioning + state locking are mandatory
  # before any `terraform apply`. The bucket itself is created by the
  # operator out-of-band (see backend.tf.example) so it can carry its own
  # lifecycle protection and survive a Terraform-managed teardown of the
  # rest of the project.
  backend "gcs" {
    bucket = "REPLACE_WITH_TFSTATE_BUCKET"
    prefix = "burritbot/terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
