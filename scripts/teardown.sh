#!/usr/bin/env bash
# ABOUTME: Post-talk teardown — destroys the Terraform-managed burritbot platform.
# ABOUTME: Prompts for confirmation, scales ArgoCD down first, then runs terraform destroy.
set -euo pipefail

SCRIPT_NAME="teardown"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TF_DIR="${REPO_ROOT}/infrastructure/terraform"

readonly SCRIPT_NAME SCRIPT_DIR REPO_ROOT TF_DIR

usage() {
    cat <<EOF
Usage: ${SCRIPT_NAME} [--yes]

  Destroys every cluster-level artifact provisioned by Terraform under
  infrastructure/terraform/. This is not reversible.

  Pre-requisites:
    - terraform on PATH (>= 1.8.0)
    - kubectl on PATH with a loaded kubeconfig for the burritbot cluster
    - GOOGLE_APPLICATION_CREDENTIALS or gcloud ADC ready

Options:
  --yes    Skip the interactive confirmation prompt (for CI scripts).
           Requires CAST_NET_ALLOW_DESTROY=true as a second signal —
           --yes alone still prompts. The two-key guard prevents a
           stray CI invocation from destroying the cluster.

Environment:
  CAST_NET_ALLOW_DESTROY=true   Second key for --yes (see above).

After completion, spot-check the GCP console for any lingering load
balancers, disks, or forwarding rules that Terraform did not clean up.
EOF
}

require_command() {
    local cmd="$1"
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        printf '%s: required command not found: %s\n' "${SCRIPT_NAME}" "${cmd}" >&2
        exit 2
    fi
}

confirm() {
    local prompt="$1"
    local reply
    printf '%s [type DESTROY to continue]: ' "${prompt}" >&2
    read -r reply
    if [[ "${reply}" != "DESTROY" ]]; then
        printf '%s: aborted — no resources were modified\n' "${SCRIPT_NAME}" >&2
        exit 1
    fi
}

scale_argocd_down() {
    if ! kubectl -n argocd get ns argocd >/dev/null 2>&1; then
        printf '%s: argocd namespace absent; skipping scale-down\n' "${SCRIPT_NAME}" >&2
        return 0
    fi
    printf '%s: scaling ArgoCD controllers to zero so they do not race Terraform\n' "${SCRIPT_NAME}" >&2
    kubectl -n argocd scale deploy argocd-application-controller --replicas=0 || true
    kubectl -n argocd scale deploy argocd-applicationset-controller --replicas=0 || true
}

run_terraform_destroy() {
    if [[ ! -d "${TF_DIR}" ]]; then
        printf '%s: terraform dir missing: %s\n' "${SCRIPT_NAME}" "${TF_DIR}" >&2
        exit 2
    fi
    printf '%s: running terraform destroy in %s\n' "${SCRIPT_NAME}" "${TF_DIR}" >&2
    (
        cd "${TF_DIR}"
        terraform init -upgrade
        terraform destroy -auto-approve
    )
}

post_destroy_audit() {
    printf '%s: listing remaining GCP resources for visual sanity check\n' "${SCRIPT_NAME}" >&2
    if command -v gcloud >/dev/null 2>&1; then
        gcloud container clusters list || true
        gcloud compute networks list || true
        gcloud secrets list || true
    else
        printf '%s: gcloud not installed; skipping audit\n' "${SCRIPT_NAME}" >&2
    fi
}

main() {
    local yes_flag="false"
    while (( $# > 0 )); do
        case "$1" in
            --yes) yes_flag="true"; shift ;;
            -h|--help) usage; exit 0 ;;
            *) usage; exit 1 ;;
        esac
    done

    require_command terraform
    require_command kubectl

    # --yes alone is not enough — require CAST_NET_ALLOW_DESTROY=true as
    # a second independent signal so a stray CI invocation cannot wipe
    # the cluster. Without both keys, fall back to the interactive prompt.
    if [[ "${yes_flag}" != "true" || "${CAST_NET_ALLOW_DESTROY:-}" != "true" ]]; then
        confirm "About to DESTROY the burritbot cluster and all GCP resources"
    fi

    scale_argocd_down
    run_terraform_destroy
    post_destroy_audit

    printf '%s: teardown complete\n' "${SCRIPT_NAME}" >&2
}

main "$@"
