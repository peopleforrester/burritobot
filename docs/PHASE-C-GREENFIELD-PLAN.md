# Phase C — Greenfield Manifests (NeMo, LLM Guard, Grafana dashboards)
# These have no EKS reference. Strict TDD, phase by phase, no timelines.
# Plan source: out-of-scope section of docs/PHASE-B-EKS-ADAPT-PLAN.md.

## Verification Method
For each component:
- The config file already exists in this repo (Phase 3/5 work).
- The Kubernetes Deployment, Service, ConfigMap, etc. wrapping it does
  not. Phase C authors that wrapping from scratch, with a static test
  that asserts (a) the wrapping yaml exists, (b) the ConfigMap names
  match what the Deployment mounts, (c) the container image and tag
  are pinned, (d) the Service port matches what the gateway HTTPRoute
  expects, (e) the OTel endpoint env vars are wired through.

Live verification (container actually loads the config, NeMo
Guardrails actually parses the Colang rails) is a separate Phase D
concern and requires a real cluster.

## Phase order (smallest swap → largest)

### Phase C1 — Grafana dashboard ConfigMaps
**Swap surface:** trivial. Three JSON dashboards already exist at
`observability/grafana/dashboards/`. The kube-prometheus-stack chart
(B3) already enables the Grafana sidecar that watches for ConfigMaps
labeled `grafana_dashboard: "1"`. Phase C1 wraps each JSON file in a
ConfigMap with that label.

**Files:**
- `observability/grafana/dashboards/the-eyes-overview-configmap.yaml`
  (wraps `the-eyes-overview.json`)
- `observability/grafana/dashboards/prompt-response-traces-configmap.yaml`
- `observability/grafana/dashboards/cast-net-comparison-configmap.yaml`

**Test:** `tests/test_phase_c1_grafana_dashboards.py`
For each dashboard JSON: a sibling ConfigMap yaml exists, labeled
`grafana_dashboard: "1"`, with the JSON content embedded under
`data:<dashboard-name>.json:`. Asserts the JSON parses and the
ConfigMap's namespace is `monitoring`.

### Phase C2 — NeMo Guardrails Deployment + ConfigMaps
**Swap surface:** medium. No upstream Helm chart for NeMo
Guardrails. Container image is `nvcr.io/nvidia/nemo-guardrails:<tag>`
(or `nemollm/nemo-guardrails` for the community build; research
current GA before pinning). Config + four `.co` rails already exist
at `ai-gateway/nemo-guardrails/`. Wrap them in ConfigMaps the
Deployment mounts at `/config/`.

**Files:**
- `ai-gateway/nemo-guardrails/deployment.yaml` — Deployment +
  Service. Container env carries `OTEL_*` vars + `NEMO_CONFIG_PATH=/config/`
  + `GOOGLE_CLOUD_PROJECT` (Vertex passthrough). Mounts two ConfigMaps:
  one for `config.yaml`, one for the rails directory.
- `ai-gateway/nemo-guardrails/configmap-config.yaml` — wraps `config.yaml`.
- `ai-gateway/nemo-guardrails/configmap-rails.yaml` — wraps the four
  `.co` files.

**Test:** `tests/test_phase_c2_nemo_guardrails.py`
- Deployment + Service + 2 ConfigMaps exist.
- ConfigMap names referenced by `volumes:` match the ConfigMap
  `metadata.name`s (cross-reference check).
- Container image is pinned to a digest or specific tag (no `:latest`).
- OTEL_EXPORTER_OTLP_ENDPOINT env var present.
- Service port 8000 (NeMo default) exposed by the Service.
- Pod runs as non-root uid (>=1001), drops ALL capabilities, has
  readOnlyRootFilesystem.
- Sidecar container is named `burritbot-*` per the Kyverno
  `require-burritbot-sidecar-naming` policy (Phase 4).

### Phase C3 — LLM Guard Deployment + ConfigMap
**Swap surface:** medium. ProtectAI LLM Guard has an API mode (
`llm-guard-api`) that runs the scanners as a FastAPI service. The
input + output scanner config already exists at
`ai-gateway/llm-guard/config.yaml`. Wrap it in a ConfigMap, author
a Deployment.

**Files:**
- `ai-gateway/llm-guard/deployment.yaml` — Deployment + Service.
  Container env carries `OTEL_*` + `LLM_GUARD_CONFIG=/config/config.yaml`.
- `ai-gateway/llm-guard/configmap.yaml` — wraps `config.yaml`.

**Test:** `tests/test_phase_c3_llm_guard.py`
- Deployment + Service + ConfigMap exist.
- ConfigMap name referenced by Deployment matches metadata.name.
- Container image pinned (not `:latest`).
- OTEL_EXPORTER_OTLP_ENDPOINT env var present.
- Service port matches what Envoy AI Gateway's ExtProc filter
  expects (default 8000).
- Pod-security context matches Phase C2's expectations.
- Sidecar container name `burritbot-*`.

### Phase C4 — Wire new resources into deploy/ai-gateway/
**Swap surface:** tiny. Add the new manifests to
`deploy/ai-gateway/kustomization.yaml` so the wrapper Application
syncs them. Remove the Phase C TODO comment.

**Files:**
- `deploy/ai-gateway/kustomization.yaml` — add references to:
  - `../../ai-gateway/nemo-guardrails/deployment.yaml`
  - `../../ai-gateway/nemo-guardrails/configmap-config.yaml`
  - `../../ai-gateway/nemo-guardrails/configmap-rails.yaml`
  - `../../ai-gateway/llm-guard/deployment.yaml`
  - `../../ai-gateway/llm-guard/configmap.yaml`

**Test:** `tests/test_phase_c4_ai_gateway_wiring.py`
- `deploy/ai-gateway/kustomization.yaml` references all five new
  manifest paths.
- No `TODO(critical-fixes-plan)` or `TODO(phase-c)` remain in that
  kustomization (the Phase C work is no longer deferred).

### Phase C5 — Colang 1.0 syntax verification (best-effort static)
**Swap surface:** tiny. The senior review's C3 finding (colang_version
mismatch) was patched in Phase A4 by setting `colang_version: "1.0"`
to match the rails. Phase A4's note explicitly deferred live
verification against a NeMo Guardrails 0.11 container.

Phase C5 does what is verifiable without a container:
- If `nemoguardrails` Python package is install-able under uv, import
  it and call its Colang 1.0 parser on each `.co` file. Assert each
  parses without error.
- If the package can't be installed (size, deps, etc.), the test
  marks itself as `skip` with a clear reason, and the live-cluster
  verification stays a Phase D obligation.

**Files:**
- `tests/test_phase_c5_colang_syntax.py` — the parse-if-package-available
  test.
- Possibly `pyproject.toml` dev-group dep on `nemoguardrails` if it
  installs cleanly.

## Cross-cutting requirements (every phase)

Every Deployment in C2 and C3 must:
- Run as non-root (`runAsNonRoot: true`, `runAsUser: 1001`).
- Drop ALL capabilities.
- Set `readOnlyRootFilesystem: true` (with `emptyDir` mounts for any
  paths the container writes).
- Carry the `burritbot.io/layer: the-net` label and
  `burritbot.io/guarded: "true"` to match the namespace policies.
- Mount no service-account token (`automountServiceAccountToken: false`)
  unless the workload genuinely calls the Kubernetes API.
- Set CPU + memory requests and limits.
- Define readiness + liveness probes.
- Emit OTel spans via `OTEL_EXPORTER_OTLP_ENDPOINT` pointing at the
  collector in `monitoring`.

Every sidecar container in a `burritbot-guarded` pod must be named
`burritbot-*` (Kyverno `require-burritbot-sidecar-naming.yaml` will
reject otherwise).

## Out of scope
- **Colang 1.0 live verification** — Phase D (needs a running NeMo
  container or cluster).
- **Envoy AI Gateway ExtProc wiring to NeMo / LLM Guard upstreams** —
  the gateway.yaml already exists; updating its filter chain to call
  the new Services is a follow-up if the Service DNS names need to
  change.
- **Vertex AI authentication for NeMo's main-model engine** — the
  ConfigMap declares `engine: vertexai` and references
  `GOOGLE_CLOUD_PROJECT`; live auth via WIF is a Phase D concern.
- **Performance tuning of LLM Guard model loads** — the demo accepts
  whatever the default scanner models do; production tuning is a
  separate exercise.

## Commit Strategy
- One commit per phase (C1 through C5) on `staging`.
- Failing test first; minimum implementation; full static suite
  green before commit.
- Commit message names the component and what was authored: e.g.
  `feat(C2): add NeMo Guardrails Deployment + ConfigMap wrappers`.

## Exit Conditions
- All five Phase C tests pass.
- `deploy/ai-gateway/kustomization.yaml` no longer carries a Phase C
  TODO.
- PROJECT_STATE.md refreshed with the new manifest inventory and the
  "NeMo / LLM Guard / Grafana dashboards" entry in Known Gaps is
  removed (moved to a "Phase D — live cluster" gap that lists Colang
  live verify, Terraform apply, ArgoCD sync, live test markers).
