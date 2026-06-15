# Phase D — GCP Live Cluster Prereqs + Bring-up
# Strict TDD, phase by phase, no timelines. GKE Standard + NAP is the target;
# k3s / Autopilot / non-GCP variants are out-of-scope collateral phases.

## Verification Method
D1–D3 are static-testable Terraform changes — they can land before any
`terraform apply`. The tests assert backend blocks, private-cluster
flags, and shell-script env gating. D4+ require GCP auth and are
deferred to a session with `gcloud` credentials + the Terraform binary
installed (per `PROJECT_STATE.md` "Local Tooling" — terraform is not
yet installed locally).

## Phase order

### Phase D1 — Terraform GCS backend (closes senior-review C11)
**Why now:** state must live in GCS *before* the first `terraform apply`.
Local state is unversioned; losing it means re-creating the cluster on
recovery.

**Files:**
- `infrastructure/terraform/main.tf` — add a `terraform { backend "gcs" {...} }`
  block. Bucket is `REPLACE_WITH_TFSTATE_BUCKET` placeholder; prefix
  `burritbot/terraform/state`. Operator creates the bucket once
  (object versioning on) before `terraform init`.
- `infrastructure/terraform/backend.tf.example` — a documented example
  of the bucket creation commands operators run before `init`.

**Test:** `tests/test_phase_d1_tf_gcs_backend.py`
- main.tf contains a `backend "gcs"` block.
- Bucket value is either a placeholder or a real GCS bucket name
  (rejects local/none backends).
- The example bootstrap doc exists.

### Phase D2 — Private cluster config (closes C12)
**Files:**
- `infrastructure/terraform/gke.tf` — add `private_cluster_config { ... }`
  with `enable_private_nodes = true`, `enable_private_endpoint = false`
  (lets the operator reach the control plane from a known IP),
  `master_ipv4_cidr_block = "172.16.0.0/28"`.
- `infrastructure/terraform/gke.tf` — add `master_authorized_networks_config`
  with a `REPLACE_WITH_OPERATOR_CIDR` placeholder.
- `infrastructure/terraform/variables.tf` — declare `master_ipv4_cidr_block`
  and `master_authorized_cidrs` variables with sensible defaults +
  descriptions.

**Test:** `tests/test_phase_d2_tf_private_cluster.py`
- `private_cluster_config` block present with `enable_private_nodes = true`.
- `master_authorized_networks_config` block present.
- variables.tf declares the two new variables with descriptions.

### Phase D3 — Deletion-protection guard (closes C13)
**Why:** `deletion_protection = false` plus `teardown.sh --yes` together
means a stray CI run could destroy the cluster. Layer a second signal.

**Files:**
- `scripts/teardown.sh` — gate the `--yes` path on a second env var
  (`CAST_NET_ALLOW_DESTROY=true`). Without it, `--yes` still requires
  interactive confirmation.

**Test:** `tests/test_phase_d3_teardown_guard.py`
- teardown.sh references `CAST_NET_ALLOW_DESTROY` somewhere.
- An end-to-end shell harness: setting only `--yes` (and not the env
  var) still prompts; setting both proceeds without prompting. Tested
  with `script -c` or by mocking the `terraform` binary on PATH.

## Deferred to a later (live-auth) session
- **D4 Cluster bring-up.** `terraform init` (with the GCS backend),
  `terraform validate`, `terraform plan -out=tfplan`, review,
  `terraform apply tfplan`. Requires `gcloud auth application-default
  login` and the `terraform` binary installed locally.
- **D5 ArgoCD bootstrap.** `kubectl apply -f gitops/bootstrap/app-of-apps.yaml`
  to seed the root app; ArgoCD's recursive directory sync picks up every
  Application under `gitops/apps/`.
- **D6 Live test markers.** `pytest -m live -m phase1` through `-m phase8`,
  promoting each YELLOW scorecard row to GREEN as the markers pass.
- **D7 Colang 1.0 live verification.** Spin up the NeMo Guardrails
  Deployment from Phase C2, port-forward, post a few prompts that the
  rails should refuse, and watch the response. Static parse (Phase C5)
  proved the rails are well-formed; D7 proves they actually fire.

## Out of scope (collateral / non-main-path)
Per Michael's direction (2026-06-15): k3s, Autopilot, and any non-GCP
runtime are saved as future collateral phases — they are not the path
to demo day. EKS-equivalent of this work will be a separate Phase E
*after* the GCP path is fully live.

## Commit Strategy
- One commit per phase (D1, D2, D3) on `staging`. Failing test first;
  minimum implementation; full static suite green before commit.
- D4+ commits happen in a live-auth session, not this one.

## Exit Conditions (for the offline portion)
- D1, D2, D3 tests pass.
- PROJECT_STATE.md refreshed with the new count and a clear "Phase D
  static prereqs complete; live bring-up pending GCP auth" entry.
- The Known Gaps list in PROJECT_STATE.md drops C11/C12/C13 and grows a
  "Phase D live cluster" sub-entry that names what is still pending.
