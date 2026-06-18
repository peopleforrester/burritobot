# Project State — burritbot (Can Your Chatbot Run kubectl?)

## Verification Method
Tracker contents are reconciled against actual repo state (file reads,
`pytest --collect-only`, `git log`) at every transition — not from
prior session summaries. The "static tests passing" count below is
asserted by `tests/test_critical_fix_a6_project_state_truthful.py`,
which fails the suite if this number drifts from reality.

The senior-review pass on 2026-04-25 surfaced five demo-breaking
defects that all five Phase 1–8 scorecards had silently rated GREEN.
The lesson written into the state-persistence rule
(`~/.claude/rules/state-persistence.md`) — distinguish "written" from
"confirmed against reality" — is now enforced for the critical-fix
work tracked below.

## Current Status
**Phases 1–8 offline build complete; six critical defects (C1, C2,
C3, C4, C5, C9) found and repaired under TDD.** Commits land on
`staging` and ride the autonomous staging→main flow once each phase's
test passes. Live cluster validation (terraform apply, helm installs,
live Kyverno + Falco + Envoy + NeMo Guardrails smoke tests) remains
deferred to a session with GCP auth and cluster access.

**Recent rewrites (post-Phase-8):**
- Commit F (`0bd0f34`) — hard rename Deinopis → burritbot across 78 files.
- Commit G (`43b4db3`) — narrative shift to a lighthearted Act 1.
- Critical-fix series (this session) — see "Critical Fixes" below.

## Platform Context
- Platform name: **burritbot** (ogre-faced spider — The Eyes + The Net)
- Chatbot name: **BurritBot** (Chipotle viral chatbot incident as narrative hook)
- Format: Two-act live demo (unguarded then guarded BurritBot on GKE)
- Talk-specific delivery artifacts (CFP, runbook, scorecard, build plan)
  live under `presentations/<event>/`. See `README.md` for the current
  active deliveries.

## Critical Fixes (this session)
Plan: `docs/CRITICAL-FIXES-PLAN.md`. Each phase landed a failing test
first, then the minimum fix, then re-ran the full static suite before
commit.

| ID  | Fix                                                            | Test                                                  | Verified-Static | Verified-Live |
| --- | -------------------------------------------------------------- | ----------------------------------------------------- | --------------- | ------------- |
| C1  | ArgoCD Application paths now resolve (`deploy/<x>/` stubs)     | `test_critical_fix_a1_argocd_paths.py`                | Yes             | No            |
| C2  | ServiceAccount manifests added; WIF annotation on guarded SA   | `test_critical_fix_a2_service_accounts.py`            | Yes             | No            |
| C9  | audience-frontend Dockerfile + requirements.txt added          | `test_critical_fix_a3_audience_dockerfile.py`         | Yes             | No            |
| C3  | NeMo `colang_version` aligned with rail syntax (1.0)           | `test_critical_fix_a4_colang_alignment.py`            | Yes             | No            |
| C4  | OTel auto-instrumentation wired; unguarded Deployment exports OTEL_* | `test_critical_fix_a5_otel_app_wired.py`, `..._unguarded_env.py` | Yes             | No            |
| C5  | PROJECT_STATE.md test-count drift now asserted by a test       | `test_critical_fix_a6_project_state_truthful.py`      | Yes             | n/a           |

## What's Done

### Phase 0 — Bootstrap
- [x] Git repo initialized (`main` + `staging` branches pushed to origin)
- [x] GitHub repo: `peopleforrester/burritobot`
- [x] `kubeauto-ai-day/` subdir kept local-only (gitignored)
- [x] `CLAUDE.md`, `README.md`, `.gitignore`
- [x] `presentations/kubecon-na-2026/docs/BUILD-INSTRUCTIONS.md` (verbatim spec + preamble)
- [x] `presentations/kubecon-na-2026/docs/PLAN.md`, `docs/KUBEAUTO-REUSE-MAP.md`, `docs/CRITICAL-FIXES-PLAN.md`
- [x] `PROJECT_STATE.md` (this file)

### Offline Build (Tasks #7 – #18)
| # | Task | Status | Commit |
|---|------|--------|--------|
| 7 | Rebaseline docs to burritbot spec | completed | 5daad64 |
| 8 | Python env + test scaffolding | completed | 1608114 |
| 9 | Project skills and slash commands | completed | c978e63 |
| 10 | Phase specs + scorecard skeleton | completed | 500bef7 |
| 11 | Phase 1: Terraform (GKE Standard + NAP) | completed | c89a4b5 |
| 12 | Phase 2: ArgoCD GitOps bootstrap | completed | 25d7f5d |
| 13 | Phase 3: The Eyes (observability) | completed | af6629a |
| 14 | Phase 4: The Net — Security (Kyverno + Falco) | completed | 1d77e42 |
| 15 | Phase 5: The Net — AI Gateway | completed | e4602e2 |
| 16 | Phase 6: BurritBot application (gemini-3-pro) | completed | cdb1dda |
| 17 | Phase 7: Audience frontend + rate limiter | completed | 542c194 |
| 18 | Phase 8: Hardening, runbook, docs | completed | (Phase 8 commit) |
| 19 | Critical fixes C1–C5, C9 (senior-review pass) | completed | this session |

### Static Test Totals
- Phase 1: 8 passed
- Phase 2: 4 passed
- Phase 3: 6 passed
- Phase 4: 7 passed
- Phase 5: 6 passed
- Phase 6: 7 passed
- Phase 7: 7 passed
- Phase 8: 5 passed
- Critical-fix series: 21 passed
- Phase B (EKS-adapt) — B1 cert-manager (7) + B2 external-secrets (7) + B3 prometheus (6) + B4 otel-collector (6) + B5 falco (8) + B6 loki/tempo/promtail (9) + B7 kyverno (4) + B8 deploy wiring (4) — **complete**
- Phase G (Genericize) — G1 move talk artifacts + G2 scrub platform refs + G3 rewrite README/instructions/state + G4 GitHub description + G5 leak test (1) — **complete**
- Phase C (Greenfield) — C1 grafana dashboard ConfigMaps (13) + C2 nemo-guardrails (10) + C3 llm-guard (10) + C4 ai-gateway wiring (7) + C5 colang parse (4) — **complete**
- Phase D (GCP live prereqs) — D1 tf gcs backend (4) + D2 tf private cluster (5) + D3 teardown guard (3) — **offline portion complete**
- ESO controller GSA + WIF binding wired into iam.tf (5)
- **Total: 203 static tests green. Live tests skip cleanly when
  kubeconfig is absent — no mocks, no fallbacks.** Drift in this
  number is asserted against `pytest --collect-only -m static` by the
  Phase A6 test.

## Phase 1 Preconditions (authoritative)
1. **GCP project ID:** `burritbot-kubecon-2026` (placeholder — confirm real
   ID before `terraform apply`).
2. **Region:** `us-west1`.
3. **GKE mode:** **Standard with node auto-provisioning.** Not Autopilot —
   Falco DaemonSet needs privileged container support.
4. **Gemini model:** `gemini-3-pro` (GA) accessed via `google-genai` with
   `vertexai=True`. 1.5 is unsupported; 2.0 Flash is retired; 2.5 Flash/Pro
   retire 2026-10-16 — four weeks before the talk; 3 Flash is preview-tier.
   3 Pro is the only Vertex AI model guaranteed to be live on demo day.
5. **Audience frontend backend:** FastAPI (matches the rest of the stack).
6. **Licensing:** Apache 2.0 (matching kubeauto-ai-day lineage).

## Local Tooling
- Installed: `yamllint`, `jq`, `kyverno`, `shellcheck`, `uv`, `python3.13`,
  `terraform`, `kubectl`, `helm`, `gcloud`
- Still missing: `kubeconform`, `docker`
- gcloud accounts authenticated: `michael@kodekloud.com` (active, intended
  GCP identity), `michaelrishiforrester@gmail.com` (personal, do not use)
- ADC for the Terraform google provider: not yet set up — run
  `gcloud auth application-default login` before the first
  `terraform init`.

Offline TDD strategy: Python code via pytest; Kyverno via `kyverno test`;
YAML via yamllint; JSON dashboards via `jq empty`; shell via shellcheck.
Terraform `init`/`validate`/`plan` are now runnable locally; `apply`
remains a deliberate operator step.

## Known Gaps (deferred — not blocking the critical-fix series)

These were surfaced in the senior review but are out of scope for the
critical-fix pass. Each is tracked here so a future session can pick
them up without re-discovering them.

### From the senior review
- **C3 live verification.** Colang `1.0` matches the rail syntax, but
  this needs to be confirmed against a running NeMo Guardrails 0.11
  container before demo day.
- **C7 — CORS `allow_origins=["*"]`.** Lock to known audience hostnames.
- **C8 — per-pod rate limiter.** slowapi in-memory storage scales
  per replica; either keep replicas: 1 or wire to Redis.
- **C10 — `cast-net.sh` hardcoded `containers/0`.** Switch to
  `kubectl set env deployment/...` or look up by container name.
- **C11 — Terraform GCS backend.** No `backend "gcs"` block; first
  `terraform apply` writes local state.
- **C12 — Public GKE nodes.** No `private_cluster_config` despite the
  NAT gateway suggesting private intent.
- **C13 — `deletion_protection = false`.** Combined with
  `teardown.sh --yes`, the cluster could be destroyed by a stray CI run.
- All Medium/Low items (#14–#27 in the senior review).

### Newly surfaced (deeper structural)
- **No Deployment manifests for the AI Gateway / NeMo / LLM Guard /
  OTel Collector / Falco DaemonSet / Grafana dashboards.** The
  `deploy/` Kustomizations created in Phase A1 are deliberately
  shallow — they reference what *is* deployable today (Kyverno
  ClusterPolicies, Envoy Gateway CR, BurritBot + audience workloads)
  and carry TODO comments for the rest. Future work needs to author
  the missing manifests (ConfigMap-wrap configs, Deployment specs,
  ServiceMonitor / PodMonitor, etc.).

## Next Session — Phase 1 Live Validation
Once a GCP project is confirmed and Terraform is installed:

```bash
claude -p "Read CLAUDE.md, PROJECT_STATE.md, \
presentations/kubecon-na-2026/docs/BUILD-INSTRUCTIONS.md, \
presentations/kubecon-na-2026/docs/PLAN.md, \
and docs/CRITICAL-FIXES-PLAN.md. Validate Phase 1: GKE \
Foundation. Run terraform validate, terraform plan, then terraform apply. \
Run tests/test_phase_01_foundation.py with the live marker." --max-iterations 20
```

Then walk Phases 2 → 8 forward in the same autonomous staging→main
workflow, promoting YELLOW scorecard rows to GREEN as each live check
passes. **Do not green-wash the scorecard.**

## Demo-Day Artifacts (Phase 8)
- `presentations/kubecon-na-2026/docs/RUNBOOK.md` — Pre-flight / Act 1 / Cast the Net / Act 2 / Teardown / Rollback
- `presentations/kubecon-na-2026/docs/SCORECARD.md` — honest per-component status, YELLOW where live
  validation has not happened yet
- `docs/CRITICAL-FIXES-PLAN.md` — the senior-review repair plan
- `scripts/teardown.sh` — `terraform destroy` with a two-step confirmation
- `scripts/cast-net.sh` — the single-command live traffic toggle

## Branch & Test Status
- **Branch**: `staging` (default working branch)
- **Remote**: `origin → https://github.com/peopleforrester/burritobot`
- **Static tests**: 80 passing, 0 failing, live tests skip when kubeconfig absent

## Key References
- `CLAUDE.md` — project Claude Code instructions
- `presentations/<event>/docs/BUILD-INSTRUCTIONS.md` — talk-specific burritbot spec
- `docs/CRITICAL-FIXES-PLAN.md` — senior-review repair plan (this session)
- `presentations/<event>/docs/RUNBOOK.md` — demo-day operational runbook
- `presentations/<event>/docs/SCORECARD.md` — per-component scorecard
- `spec/BUILD-SPEC.md` — build-time pointer and completion protocol
- `spec/phases/phase-0[1-8]-*.md` — per-phase specs with completion promises
- Local reuse source: `~/repos/_archive/events/kubeauto-ai-day/` (local-only)
- Remote reuse source: https://github.com/peopleforrester/kubeauto-ai-day
