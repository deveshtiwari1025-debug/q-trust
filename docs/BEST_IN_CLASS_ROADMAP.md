# Q-Trust — What It Takes to Be Best in Its Domain

**Status:** evidence-based gap analysis and execution plan
**Baseline:** `main` @ `8e478912` (2026-10-18)
**Scope:** the domain Q-Trust actually competes in — *enterprise post-quantum
cryptography discovery, migration planning, and verifiable attestation* — not
"security tooling" in general.

> **How to read this.** Facts marked **[verified]** were checked against the
> repository, CI, PyPI, or the public internet on 2026-10-18 and are cited to a
> file/line. Items marked **[inference]** are judgement calls about buyers,
> competitors, or effort. Nothing here repeats a number from a document without
> saying where the number comes from.

---

## 0 · The one-paragraph answer

Q-Trust is already an unusually complete *engineering* artifact: 11 UUPS
contracts, a Fastify backend with 52 documented API paths, a 27-module scanner package
emitting CycloneDX 1.7, an ACVP-verified conformance suite, a GNN/RL planner
with a leakage-audited 42-fold benchmark, and an on-chain evidence layer. It is
**not yet best in its domain**, and the reason is not missing features. It is
that the project cannot yet be *trusted*, *operated*, or *bought* by the people
who decide: there is no external audit, no production deployment, no SSO/RBAC/
multi-tenancy/audit log, no expert-labeled data, no scale proof, and almost no
distribution (0 stars, 3 contributors, 0 external PRs **[verified]**). The path
to best-in-domain is therefore: **pay the credibility debt first, then earn
enterprise trust, then deepen the data moat** — in that order. Adding more
scanners or chains before those three steps would make the project broader, not
better.

---

## 0.1 · Implementation status on this branch (2026-10-18)

Code-level items from the plan are implemented and tested here. Items that
require an auditor, a funded key, a cloud account, or a commercial agreement
are explicitly **not** claimed as done.

| Plan item | Status | Evidence |
|---|---|---|
| CR-01 metric truth | **Done** | README headline is out-of-sample τ-b 0.7168; 0.975 labeled synthetic |
| CR-02 claim counts | **Done** | `scripts/check_readme_claims.py` + `docs-contract` CI job |
| CR-03 version sync | **Done in repo** (publish pending tag) | all four manifests at 2.2.3; `scripts/check_version_sync.py` |
| CR-04 dependency debt | **Done** | backend audit 0; frontend runtime audit 0; daily `npm-audit` job |
| CR-05 disclosure | **Done** | `.well-known/security.txt` + Pages publish + stale TODO removed |
| CR-06 data reproducibility | **Done** | `scripts/fetch_datasets.py` verifies HF `SHA256SUMS.txt`; `--subset corpus` yields 42 CBOMs / 277 hosts / 0 overlap. The package's `real_cboms_v2_2026_09_18/` copy is incomplete (38/42); documented in `docs/REPRODUCE.md` |
| CR-07 demo ownership | **Open (external)** | HF space still under `KRISHNAPURI` |
| CR-08 positioning | **Open** | README Reality Check + SECURITY.md remain the honest status |
| TR-05 supply chain | **Done** | SBOM + provenance + keyless cosign + PEP 740 |
| TR-08 reproduce guide | **Done** | `docs/REPRODUCE.md` with artifact hashes |
| EN-02 audit log | **Partial** | hash-chained table + hook + 6 tests; SIEM export pending |
| MI-01 target algorithms | **Done** | `planner/qtrust_planner/recommend.py` + 10 tests |
| ML-05 research isolation | **Done** | RESEARCH-ONLY banners; no product imports |
| TR-01/02/03/04/06/07 | **Open (external)** | audit, pen test, deployment, KMS/multisig, SOC 2, IR |
| EN-01/03–08, CO-*, MI-02–06, ML-01–04/06, ST-* | **Open** | multi-week work tracked below |

---

## 1 · What "best in domain" has to mean

### 1.1 The buyer and the decision

The buyer is not a developer looking for a scanner. The buying committee is:

| Role | Question they ask | What has to exist to answer it |
|---|---|---|
| CISO / VP Security | "Can I prove our PQC exposure and our plan to the board and regulators?" | Executive reporting, standards mapping, defensible numbers |
| Crypto / PKI lead | "Does it find *everything*, including the things I forgot?" | Coverage across code, certs, keys, cloud KMS/HSM, protocols, binaries |
| Platform / DevSecOps | "Will it fit our pipelines and not create a second backlog?" | CI gates, ticketing, auto-remediation PRs, policy-as-code |
| Auditor / regulator | "Is this evidence tamper-proof and independently checkable?" | Attestations, audit trail, reproducible methodology |
| Procurement / IT | "Can we run it in our environment and pass our security review?" | SSO, RBAC, tenancy, SOC 2/ISO, on-prem/air-gap, DPA, SLA |

### 1.2 The rubric (target: 4.5 / 5 average, with two 5s)

| Dimension | Weight | What 5/5 looks like | Q-Trust today |
|---|---:|---|---|
| Discovery coverage & accuracy | 20% | Code, binaries, TLS/SSH/IPsec/QUIC, cloud KMS/HSM, certs, images, IaC; measured precision/recall per class | **3/5** |
| Evidence quality & explainability | 15% | Line-level provenance, reproducible scan IDs, per-asset feature attribution, no unlabeled metric | **4/5** |
| Trust & assurance | 15% | External audits, signed releases, SOC 2/ISO, public deployment, independent benchmark reproduction | **1/5** |
| Enterprise operability | 15% | SSO/SCIM, RBAC, tenancy, immutable audit log, HA/DR, on-prem/air-gap, SLOs | **1/5** |
| Migration execution | 15% | Target-algorithm recommendations, verified code patches/PRs, real cost/failure models, outcome loop | **3/5** |
| Scale & performance | 5% | 1M assets/org, 100k files/min, p95 < 1s planning at 10k assets, published load tests | **2/5** |
| Standards & interoperability | 5% | CycloneDX/ECMA-424, OSCAL, VEX, SPDX, SARIF, OpenAPI 3.1, PQCA/NIST contribution | **3.5/5** |
| Ecosystem & distribution | 5% | GitHub App, Jira/ServiceNow/SIEM, MCP registry, 500+ stars, 20+ contributors | **1/5** |
| Commercial viability | 5% | Design partners, pricing, 3 case studies, support/SLA, open-core boundary | **0.5/5** |
| **Weighted today** | | | **≈ 2.1 / 5** |

### 1.3 Table stakes vs. differentiators

Do not try to win every row. Win the last column; match the first.

| Table stakes (must match to be considered) | Differentiators Q-Trust must own |
|---|---|
| CBOM generation (CycloneDX 1.7 / ECMA-424) | **Public, reproducible, host-disjoint real-estate benchmarks** |
| TLS + source-code discovery | **Auditor-grade, tamper-proof evidence anchored on-chain** |
| NIST/CNSA/FIPS compliance mapping | **Migration intelligence trained on real outcomes** |
| Dashboard + export | **Open, self-hostable, air-gapped deployment** |
| SSO, RBAC, audit log | **Developer-first CI + MCP integration** |
| Ticketing/SIEM integrations | **Honest metrics no competitor can fake** |

Competitor archetypes to benchmark against: SandboxAQ, IBM Quantum Safe,
Keyfactor/Venafi, DigiCert, PQShield, QuSecure, InfoSec Global, Thales/Entrust;
open-source CBOM tools (IBM CBOMkit, CryptoGuard, `cbom-action`) **[inference:
public positioning, not tested here]**. Q-Trust cannot out-spend them on
coverage or sales. It can out-execute them on **verifiability and openness** —
but only if the trust layer is real.

---

## 2 · Verified baseline (2026-10-18)

### 2.1 What is genuinely strong

| Area | Evidence |
|---|---|
| Contract architecture | 11 UUPS registries + timelock governance (`contracts/src/*.sol`); 213 forge tests incl. invariant + attack suites (`PROJECT_SCORECARD.md`); Slither gated on HIGH (`security.yml`) **[verified in repo]** |
| API surface | 52 documented paths (`backend/openapi.yaml`); constant-time API-key comparison (`backend/src/middleware/auth.ts`); fail-closed production gates; Prometheus `/metrics` + optional Sentry (`backend/src/plugins/`) |
| Scanner breadth | 27 modules incl. TLS, SSH, source, binary, manifest, PCAP, anomaly, side-channel, remediation, K8s policy, MCP (`inspector/qtrust_inspector/`) |
| Standards work | CycloneDX **1.7** emitter (`cyclonedx.py:128`), SARIF, 11 compliance frameworks (`compliance.py:12-24`), ACVP oracle tests + liboqs KATs (`inspector/tests/test_acvp_vectors.py`, `test_liboqs_kats.py`) |
| ML honesty | 42-fold host-disjoint LOO: τ-b **0.7168** vs heuristic **0.7210** (tie), 0 wins/41 ties/1 loss (`EXPERIMENTS.md` E-06); CodeBERTa F1 **0.9525** on 13,973 real files; leakage audit reproduced |
| Governance docs | `TRUTH_AUDIT.md`, `RISK_REGISTER.md`, `TECHNICAL_DEBT.md`, `PROJECT_SCORECARD.md` classify claims as REAL/SYNTHETIC/DEMO — rare and valuable |
| Distribution | `qtrust-inspector` and `qtrust-sdk` live on PyPI at **2.2.0** **[verified via PyPI API]**; HF demo returns **200** **[verified]** |

### 2.2 What blocks "best in domain"

| # | Gap | Verified evidence | Why it blocks the claim |
|---|---|---|---|
| G-1 | **No external audit; self-described pre-release** | `SECURITY.md`: "research / pre-release … no external audit yet … do not anchor production trust decisions" | Enterprise security review stops here. No amount of features compensates. |
| G-2 | **No production deployment** | `docs/deployment/GO_LIVE_CHECKLIST.md` items 1–5 blocked on accounts/keys; testnet only | The core promise (tamper-proof evidence) is unproven in public. |
| G-3 | **No enterprise identity/tenancy** | Auth is a global list of API keys (`backend/src/middleware/auth.ts`); no OIDC/SAML/SCIM/RBAC/tenant model; no audit log (`grep` returned none) | Cannot sell to an org with more than one team, let alone pass procurement. |
| G-4 | **Datasets are not in the repo** | `qtrust_data/{raw,bronze,silver,gold,splits}/` contain only `.gitkeep`; `dvc.yaml` declares only an `evaluate` stage | "Reproducible data moat" is currently a claim, not an artifact. |
| G-5 | **The ML "factory" is largely stubs** | `qtrust/models/planner/cpsat.py` (greedy fallback), `qtrust/models/digital_twin.py` (placeholder), `qtrust_ai/graph/temporal_gnn.py` (CPU stub), `qtrust_ai/migration/multi_objective_rl.py` (stub), `qtrust_ai/discovery/code_detector.py` (hash stub); none imported by product code | Two ML narratives exist. The product planner is real; the factory is not. A credibility liability if not separated. |
| G-6 | **Model ceiling** | GNN ties its own heuristic out-of-sample (`EXPERIMENTS.md` E-06); RL agent also ties it | The "AI" advantage is unproven. Expert labels are the only honest path. |
| G-7 | **Coverage gaps** | No cloud KMS/ACM/Key Vault/GCP KMS connector, no live K8s collector, no CT-log ingestion, no HSM/PKCS#11 inventory, no container-image scanner (`grep` across `inspector/`) | Buyers' crypto estates live in exactly those places. |
| G-8 | **Distribution is near zero** | 0 stars, 0 forks, 3 contributors, 0 non-dependabot PRs, 42 open Dependabot PRs (oldest 2026-08-23), 125 PyPI downloads/month **[verified via GitHub + pypistats APIs]** | A project cannot be "best" if nobody uses it. |
| G-9 | **Dependency debt is accumulating on `main`** | `npm audit --package-lock-only` in `backend/`: **6 vulnerabilities (3 high)** incl. `fastify <=5.12.4`; daily `security.yml` has **no npm audit**; full CI last ran 2026-09-20 | Undetected supply-chain risk in the shipped service. |
| G-10 | **Headline claims contradict the honest benchmark** | README says **τ 0.975 "GNN ranking accuracy"** at lines 101/176/200/221/358/621, while the out-of-sample result is **τ-b 0.7168 (tie)** | The single fastest way to lose an expert evaluator's trust. |
| G-11 | **Small internal inconsistencies** | README says 211 contract tests (lines 101/365/465/619) vs 213 in scorecard; "7 compliance frameworks" vs 11 in code; "10 scanner modules" vs 27 modules; draft release v2.2.3 / latest release v2.2.2 vs manifests & PyPI 2.2.0 | Signals docs are not generated/verified. |
| G-12 | **Wallet-first UX** | `/dashboard` and `/vendors` gate on `useAccount` (`TECHNICAL_DEBT.md` TD-12); no email/passkey path | Enterprise users do not have wallets. |

---

## 3 · P0 — Pay the credibility debt (week 1–2, ~6 engineering days)

These are cheap, mechanical, and remove the reasons an expert dismisses the
project before looking at the architecture.

| ID | Action | Exact files / commands | Acceptance test |
|---|---|---|---|
| CR-01 | Make every headline metric out-of-sample and labeled | `README.md:101,176,200,221,358,621` → "out-of-sample τ-b 0.7168 (heuristic 0.7210, tie); in-distribution 0.971" | `grep -n "0.975" README.md` returns only lines that explicitly say "in-distribution/synthetic" |
| CR-02 | Regenerate counts from artifacts | 211→213 tests; 7→11 frameworks; 10→27 modules (`README.md:101,252,365,465,619`) | `scripts/check_readme_claims.py` asserts counts against `forge test --list`, `ComplianceFramework`, and scanner module count |
| CR-03 | Re-cut the release | Draft release `v2.2.3`, latest release `v2.2.2`, but every manifest and PyPI say `2.2.0`; bump `backend/package.json`, `frontend/package.json`, `sdk/pyproject.toml`, `inspector/pyproject.toml`, publish, verify install | `pip index versions qtrust-inspector` shows 2.2.3; a CI `version-sync` job fails on drift |
| CR-04 | Close the dependency debt and keep it closed | `npm audit fix` in `backend/` and `frontend/`; bump `fastify` `^5.12.7`, `fast-uri` `^4.2.2`, `ip-address` `^10.7.4`; merge/close the 42 Dependabot PRs; add a daily `npm-audit` job to `security.yml`; schedule full CI weekly | `npm audit --audit-level=high` exits 0; `security.yml` fails on high |
| CR-05 | Make vulnerability reporting real | Private-reporting endpoint already returns **200** **[verified]**; remove the stale `TODO(owner)` block at `SECURITY.md:30`; `frontend/public/.well-known/security.txt` exists but its GitHub Pages canonical **404s** and it uses `qtrust.example` — also publish under `docs/.well-known/`, set the real domain, and monitor expiry (2027-08-26) | Both canonical URLs return 200; TODO removed; expiry monitored |
| CR-06 | Publish the data or stop claiming it | Export splits/CBOMs/corpus manifest to HF datasets with a data card + SHA-256 manifest; add the remaining DVC stages **or** narrow the docs to "evaluate only" | A clean clone runs `python -m qtrust.evaluation.run_all` and gets the published numbers |
| CR-07 | Make the demo project-owned | HF space is under `KRISHNAPURI`, repo under `humoge7502` **[verified]**; move/rename or document ownership; add a weekly URL check | README links resolve; link checker is green |
| CR-08 | Unify positioning | Pick one label: "research preview" or "production-preview". `SECURITY.md` says the former, README implies the latter | One sentence appears consistently in README, SECURITY, docs index, PyPI description |

**Exit criterion for P0:** every public number is traceable to an artifact; CI is
green on `main` *and* on PRs; a clean clone reproduces the published evaluation;
no unqualified in-distribution metric appears anywhere.

---

## 4 · P1 — Trust & assurance (weeks 2–8; the highest-leverage spend)

Nothing else on this list converts to enterprise revenue until this section is
true. The good news: the preparation is already done (`docs/audit/DOSSIER.md`,
`docs/SECURITY_THREAT_MODEL.md`).

| ID | Action | Why | Acceptance test |
|---|---|---|---|
| TR-01 | **External smart-contract audit** (Trail of Bits / OpenZeppelin / Code4rena class), publish the full report and remediation | Turns "well-engineered" into "independently verified"; closes `RISK_REGISTER.md` R-01 | Report in `docs/audits/`; all High/Critical fixed; register updated |
| TR-02 | **External application/API penetration test** (auth, relay, SSRF, webhooks, frontend) | The backend holds a relayer key and fetches attacker-controlled URIs | Report + retest clean; TM register updated |
| TR-03 | **Public Base Sepolia deployment** of all 11 registries, verified on Basescan, addresses + receipts committed; then **Base mainnet** after TR-01 | Converts the attestation story from claim to public evidence; closes G-2 | `docs/deployment/BASE_SEPOLIA.md` has live addresses; CI verifies bytecode; a public `/v/<id>` page resolves |
| TR-04 | **Decentralize operational trust** | EOA relayer is a single point of forgery; `RISK_REGISTER.md` R-08 | Safe 2/3 + Timelock 7 d own admin; relayer key in KMS/HSM with rotation + per-tenant spend caps; ≥2 RPC providers with failover |
| TR-05 | **Supply-chain hardening** | A tool that preaches attestation must attest itself | cosign keyless signatures on images + wheels, SLSA L3 provenance, CycloneDX SBOM per image, digest-pinned base images, OpenSSF Scorecard ≥ 8 |
| TR-06 | **Certification roadmap** | Procurement gates on it | SOC 2 Type I in ≤ 120 days → Type II; ISO 27001 gap assessment; DPA + subprocessor list + data-residency options |
| TR-07 | **Incident response & disclosure** | Buyers ask "what happens when it breaks?" | `SECURITY.md` + `docs/runbook/incident-response.md`; CVE process; 72 h ack / 30 d fix SLAs; bug bounty after TR-01 |
| TR-08 | **Independent benchmark reproduction** | The moat is only a moat if others can verify it | A container + `REPRODUCE.md` that regenerates E-06/E-08/E-09 from published data; artifacts on HF/Zenodo with a DOI |

**Exit criterion for P1:** an outside security team can read the audit, deploy
the stack from public artifacts, verify a receipt on-chain, and reproduce the
headline benchmark without talking to the maintainer.

---

## 5 · P2 — Enterprise operability (weeks 6–16)

This is the difference between a respected open-source project and a product a
Fortune 500 can adopt. Today the backend authenticates with a global API-key
list and has no concept of a tenant, a role, or an audit trail **[verified]**.

| ID | Action | Acceptance test |
|---|---|---|
| EN-01 | **Identity**: OIDC + SAML SSO, SCIM provisioning, MFA/passkeys; org → workspace → project hierarchy; RBAC (`owner`, `admin`, `analyst`, `auditor`, `viewer`); scoped API keys with expiry/rotation; service accounts | A test IdP logs in; a viewer cannot write; a revoked key fails within 30 s |
| EN-02 | **Immutable audit log**: actor, action, resource, before/after, IP, request ID; append-only hash chain; export to SIEM; retention policy | Tampering with a row breaks chain verification; Splunk/Sentinel export test passes |
| EN-03 | **Tenant isolation**: row-level security in Postgres, per-tenant envelope encryption (KMS), quotas, data-residency pinning | Cross-tenant read attempt returns 404 in test; key rotation re-wraps without downtime |
| EN-04 | **Deployment artifacts**: Helm chart + K8s operator/collector, Terraform module, air-gapped bundle with signed images, HA Postgres/Redis, backup/PITR, DR runbook with RTO ≤ 1 h / RPO ≤ 15 min | `helm install` on a clean cluster reaches healthy in < 10 min; restore drill passes |
| EN-05 | **Observability**: OpenTelemetry traces across backend → planner, RED/USE dashboards, SLOs (99.9% read API), alert routing, on-call runbook | A synthetic failure pages the on-call route; trace shows both services |
| EN-06 | **Scale proof**: 1M assets/org, 100k files/min scan, p95 < 1 s planning at 10k assets, pagination everywhere, nightly load test with published results | `docs/PERFORMANCE.md` has reproducible numbers at those sizes; k6 gate in CI |
| EN-07 | **Reporting**: executive PDF, auditor portal, evidence export in OSCAL, retention/legal hold, scheduled reports | An auditor can verify a report end-to-end without an account |
| EN-08 | **UX**: remove the wallet requirement from enterprise paths (email/passkey + org-managed wallet), onboarding wizard, bulk import/export, saved views, email/Slack/Teams notifications, light/dark theme (TD-11) | A non-crypto user completes scan → plan → export in < 10 min without installing MetaMask |

**Exit criterion for P2:** a 50-person security team can self-host, connect SSO,
assign roles, pass an internal security review, and operate the system without
the maintainer.

---

## 6 · P3 — Discovery coverage & accuracy (weeks 8–24)

The scanner is strong for code/TLS and thin everywhere else. Coverage is the
first thing a crypto lead tests, and the first place a competitor wins.

| ID | Action | Acceptance test |
|---|---|---|
| CO-01 | **Cloud/KMS/HSM connectors** (read-only): AWS KMS/ACM/ELB/CloudFront, Azure Key Vault, GCP KMS, HashiCorp Vault, PKCS#11/HSM inventory | Each connector has a recorded-fixture test + least-privilege IAM policy; a real sandbox account scan is documented |
| CO-02 | **Images/K8s/IaC collectors**: OCI image scanning, registry crawl, live-cluster collector (beyond the existing `k8s_policy.py` generators), Helm/Terraform/CloudFormation parsing (the MCP `scan_infrastructure` tool is a start) | A cluster with 3 workloads yields certs, keys, and TLS configs; image scan finds a known-vulnerable OpenSSL |
| CO-03 | **Certificates & keys**: CT-log ingestion, CA inventory (ADCS/Venafi/Let's Encrypt), SSH keys (`authorized_keys`, GitHub), code-signing certs, S/MIME | CT ingestion finds the org's public certs; SSH inventory flags weak/duplicate keys |
| CO-04 | **Protocol depth**: TLS 1.3 hybrid detection, SSH, IPsec/IKE, Kerberos, MQTT, DNSSEC, SMB, LDAP, QUIC; passive PCAP enrichment | Protocol matrix in docs with a test per row |
| CO-05 | **Binary depth**: Go/Rust symbol recovery, Java/.NET, stripped binaries, firmware | Detection recall ≥ 0.90 on a labeled binary corpus |
| CO-06 | **Transitive/reachability**: SBOM + call-graph reachability, vendored-code fuzzy dedupe, near-duplicate detection | Reachability removes ≥ 30% of unreachable-crypto findings in a measured sample |
| CO-07 | **Accuracy program**: per-language labeled corpora, precision/recall published per class, confidence per rule, suppression with expiry, human-review queue | Code F1 ≥ 0.95 and FP ≤ 2% on a held-out, source-disjoint corpus; numbers published per language |
| CO-08 | **Evidence provenance**: line/column + snippet hash + AST path + git commit + container digest + scan ID | Any finding can be re-derived from the recorded inputs alone |

**Exit criterion for P3:** a buyer's "did you find X?" test passes for code,
certs, keys, cloud KMS, HSM, images, and network endpoints — with published
accuracy per class.

---

## 7 · P4 — Migration execution & workflow (weeks 10–24)

Inventory without remediation is a report. The domain is moving from "find
crypto" to "migrate it", and that is where the recurring revenue sits.

| ID | Action | Acceptance test |
|---|---|---|
| MI-01 | **Target-algorithm recommendations**: per-asset target (ML-KEM-768, ML-DSA-65, SLH-DSA, hybrid X25519MLKEM768) with key size, library, FIPS/CNSA/BSI/ANSSI profile, interoperability notes | Every plan row has a concrete target + rationale + standard citation |
| MI-02 | **Remediation that compiles**: expand beyond the 11 template languages, verify patches in a sandbox (compile/test), open PRs via GitHub App, support rollback and human approval | ≥ 80% of generated patches build in CI; PR flow demonstrated on a real repo |
| MI-03 | **Planning realism**: cost/failure models trained on actual migration outcomes, dependency/blast-radius graph from imports/calls/SBOM, CP-SAT schedules with maintenance windows and rollback plans, what-if simulation | Planner output matches actual durations within ±25% on 20 completed migrations |
| MI-04 | **Continuous operation**: scheduled re-scans, drift detection, CBOM diff, regression gates in CI, policy-as-code (OPA/Kyverno), SARIF upload | A crypto regression fails the customer's PR check with an actionable diff |
| MI-05 | **Workflow integrations**: Jira and ServiceNow ticket sync, Slack/Teams notifications, GitHub/GitLab/Bitbucket apps, Jenkins/Argo/GitLab CI, SIEM (Splunk/Sentinel/Chronicle) | Each integration has an end-to-end test against a sandbox; webhooks (already present) reused |
| MI-06 | **Outcome feedback loop**: capture actual duration, cost, failure reason, rollback; feed the planner; publish accuracy deltas | `planner` retrains on outcome data and reports before/after calibration |

**Exit criterion for P4:** a customer can go from a finding to a merged,
verified remediation PR and a closed ticket without leaving their existing
workflow.

---

## 8 · P5 — The data & ML moat (weeks 8–52)

The honest position today is that the GNN **ties** a hand-written heuristic
out-of-sample (τ-b 0.7168 vs 0.7210) and the RL agent ties it too. That is a
respectable scientific result, but it is not a moat. The moat is **expert
labels + real outcomes + a corpus nobody else has**.

| ID | Action | Acceptance test |
|---|---|---|
| ML-01 | **QTrust-RiskBench v1**: 5–10 experts, 5k–10k blinded pairwise comparisons, adjudication, inter-rater κ ≥ 0.6, published with a datasheet | Dataset on HF with DOI; κ reported; baseline + model scores reproduced by an outsider |
| ML-02 | **Scale the corpus**: 1,000+ organizations / 10,000 host-disjoint CBOMs from CT logs, Sonar, cloud connectors, with consent and legal review; hash-anchored manifest | Corpus stats published; host-disjointness verified by a script; growth rate tracked monthly |
| ML-03 | **Model quality targets**: beat the heuristic on expert labels (τ-b ≥ 0.80 vs 0.72), calibrated risk (ECE ≤ 0.05), per-asset attribution (SHAP/IG), temporal forecast, drift monitor | All four metrics in a public model card; calibration curve published |
| ML-04 | **Evaluation in CI**: nightly/weekly gates (Critical Recall ≥ 97%, τ-b no regression > 0.01, ECE ≤ 0.05), model cards, datasheets, containerized reproduction | A deliberately degraded model fails the gate; the gate runs on a schedule, not only on push |
| ML-05 | **Retire or isolate the stubs**: `qtrust/` and `qtrust_ai/` contain greedy CP-SAT, placeholder digital twin, fabricated what-if, linear synthetic graph, hash-based code detector. Either implement them or mark the package **research-only** and remove it from customer-facing docs | No stub is reachable from any product endpoint; `qtrust/README.md` states research status |
| ML-06 | **Publish**: arXiv paper on the LOO protocol + the tie, a reproducible leaderboard, and a PQCA/NIST workshop submission | Paper accepted/preprinted; ≥ 3 external reproductions or citations |

**Exit criterion for P5:** an independent researcher can download the data,
reproduce the benchmark, and confirm that Q-Trust beats the heuristic on expert
labels — or the project states plainly that it does not.

---

## 9 · P6 — Standards, ecosystem & distribution (parallel, weeks 4–52)

The project already has more standards surface than most commercial tools
(CycloneDX 1.7, SARIF, OpenAPI, EIP-712, VCs, MCP, Kyverno/Gatekeeper, ACVP).
The gap is turning that surface into **distribution**.

| ID | Action | Acceptance test |
|---|---|---|
| ST-01 | **CBOM conformance & interop**: ECMA-424 conformance suite, `cbom merge/diff/validate` CLI, import from IBM CBOMkit and CycloneDX tooling | Official/validator-clean output; round-trip import/export preserves semantics |
| ST-02 | **Format coverage**: OSCAL, VEX, SPDX 3.0, OCI referrers, OpenAPI 3.1, SLSA | Each format has a schema test and a documented example |
| ST-03 | **Standards presence**: PQCA/Linux Foundation contribution, NIST NCCoE collaboration, BSI/ANSSI/ENISA mapping review, ACVP coverage expansion to PQC families | At least one merged upstream contribution or listed tool; mapping reviewed externally |
| ST-04 | **Developer distribution**: harden and list the MCP server, ship an IDE extension, a pre-commit hook, and a GitHub Action with SARIF upload | Marketplace/Action listings live; 100 installs/month |
| ST-05 | **Community engine**: public roadmap, monthly release cadence, 20+ `good first issue`s, Discussions office hours, two named maintainers, CODEOWNERS enforcement, launch kit execution (`growth/launch-kit.md` already drafted) | 500 stars, 20 contributors, 10 external issues/month, release every month |
| ST-06 | **Commercial model**: 5–10 design partners, 3 case studies with measured outcomes, open-core boundary (OSS scanner/CLI vs paid control plane/SSO/audit), pricing page, support tiers, cloud-marketplace listings | 3 signed pilots; 10 paying customers by month 12; documented packaging |
| ST-07 | **Documentation**: consolidate `docs/` and `docs-v2/` (TD-03), persona quickstarts, versioned API with deprecation policy, error catalogue, runbooks, migration guides | `mkdocs build --strict` + docs-v2 build green; a new user completes a scan from docs alone |

**Exit criterion for P6:** a developer can discover, install, integrate, and
contribute without a personal introduction — and a buyer can find a price.

---

## 10 · Sequence and exit criteria

| Window | Theme | Must be true at the end | Effort **[inference]** |
|---|---|---|---|
| **Week 0–2** | Credibility | P0 complete; CI green on main + PRs; no contradictory public metric; data published or claims narrowed | ~6 eng-days |
| **Week 2–8** | Trust | Audit engaged/reported; Sepolia live with receipts; relayer in KMS + multisig/timelock; supply chain signed; benchmark reproducible | 3–5 eng-weeks + audit budget |
| **Week 6–16** | Enterprise | SSO/RBAC/tenancy/audit log; Helm/Terraform/air-gap; SLOs; wallet-free UX; 50-user team operable | 12–16 eng-weeks |
| **Week 8–24** | Coverage + execution | Cloud/KMS/HSM/images/certs/protocols; accuracy published; target recommendations; verified patches + PRs; Jira/ServiceNow/SIEM | 16–20 eng-weeks |
| **Week 8–52** | Data/ML moat | RiskBench v1; 1k+ orgs / 10k CBOMs; expert-label win (τ-b ≥ 0.80); calibration + attribution; paper | 8–12 eng-weeks + labeling budget |
| **Week 4–52** | Distribution | 500 stars, 20 contributors, 10 paying customers, 3 case studies, PQCA/standards presence | 4–6 h/week + GTM |

### The 12-month "best in domain" proof points

1. A public, audited deployment where anyone can verify an attestation.
2. A published benchmark that an outsider reproduces, with expert labels that
   show the model beats the heuristic.
3. A security review pack a Fortune 500 accepts (audit + pen test + SOC 2 + SBOM).
4. A 10-minute self-serve path from install to CBOM to plan.
5. Integrations that put findings where work already happens.
6. Adoption evidence: 500+ stars, 3 case studies, 10 paying customers.

---

## 11 · KPI dashboard (what to measure, and the target)

| Metric | Today (verified) | 90 days | 180 days | 365 days |
|---|---|---|---|---|
| Public claims traceable to an artifact | ~60% | 100% | 100% | 100% |
| External audits (contracts + app) | 0 | 1 engaged | 2 complete | 2 + annual retest |
| Production deployment | testnet only | Sepolia live | mainnet canary | mainnet + DR drill |
| SSO / RBAC / tenancy / audit log | none | designed | shipped | SOC 2 Type I |
| Assets supported per org (tested) | 2,000 | 50,000 | 250,000 | 1,000,000 |
| Host-disjoint CBOMs in corpus | 42 | 250 | 1,000 | 10,000 |
| Expert pairwise labels | 0 | 1,000 | 5,000 | 10,000 |
| τ-b vs heuristic on expert labels | 0.7168 (tie) | baseline | ≥ 0.76 | ≥ 0.80 |
| Calibration (ECE) | not measured | measured | ≤ 0.07 | ≤ 0.05 |
| Code-detection F1 / FP | 0.9525 / not published | per-language | F1 ≥ 0.95, FP ≤ 2% | same, 20+ languages |
| p95 planning latency | 43–337 ms @ 50–2,000 assets | < 500 ms @ 10k | < 1 s @ 100k | < 1 s @ 1M |
| High/critical dependency vulns on `main` | 3 high (backend lockfile) | 0 | 0 | 0 |
| CI cadence | push/PR only; last full run 2026-09-20 | daily + weekly | daily + weekly | daily + weekly |
| Release cadence | last 2026-09-20 | monthly | monthly | monthly |
| PyPI downloads / month | 125 | 1,000 | 5,000 | 10,000 |
| GitHub stars / contributors | 0 / 3 | 100 / 8 | 300 / 15 | 500+ / 20+ |
| Design partners / paying customers | 0 / 0 | 3 / 0 | 5 / 3 | 10 / 10 |
| Uptime (hosted control plane) | n/a | 99.5% | 99.9% | 99.9% + status page |
| Vulnerability ack time | undefined | 72 h | 72 h | 24 h |

---

## 12 · Anti-goals (things that would make it worse)

1. **Do not add chains, tokens, or ZK proofs before the audit and the
   enterprise basics.** They increase surface area and distract from trust.
2. **Do not ship new scanner breadth without an accuracy budget.** A noisy
   scanner is worse than a narrow accurate one.
3. **Do not put an LLM in the risk-scoring path.** Use it for explanation and
   drafting only; keep scoring deterministic and auditable.
4. **Do not quote in-distribution metrics as headline results.** The honest tie
   is a differentiator; a misleading τ 0.975 is a liability.
5. **Do not present the research factory (`qtrust/`, `qtrust_ai/`) as product.**
   Stubs in a customer path destroy credibility faster than missing features.
6. **Do not split the backend into microservices.** The current two-service
   shape is right for the team size.
7. **Do not compete on feature count with SandboxAQ/IBM.** Compete on
   verifiability, openness, and migration outcomes.
8. **Do not gate the only demo behind a wallet.** Enterprise evaluators will
   bounce.

---

## 13 · The next 10 actions (do these first)

| Order | Action | Where | Done when |
|---:|---|---|---|
| 1 | Fix the τ 0.975 headline and stale counts | `README.md:101,176,200,221,358,365,465,619` | Media/lines show out-of-sample numbers + labels |
| 2 | Remove the 3 high CVEs | `backend/` (`npm audit fix`; fastify ≥ 5.12.7) | `npm audit --audit-level=high` exits 0 |
| 3 | Add daily npm audit + weekly full CI | `.github/workflows/security.yml`, `ci.yml` | A failed audit turns the daily job red |
| 4 | Fix the disclosure surface | `SECURITY.md:30`; `frontend/public/.well-known/security.txt`; add `docs/.well-known/security.txt` | Both `security.txt` canonical URLs return 200; stale TODO removed |
| 5 | Cut and publish `2.2.3` consistently | 4 version files + PyPI trusted publisher | `pip install qtrust-inspector==2.2.3` works |
| 6 | Publish the datasets + manifest to HF | `qtrust_data/`, HF dataset, `DATASETS.md` | Clean clone reproduces E-06 numbers |
| 7 | Deploy 11 registries to Base Sepolia and commit receipts | `docs/deployment/BASE_SEPOLIA.md` | Basescan links + CI bytecode check |
| 8 | Send the audit dossier to 3 firms | `docs/audit/DOSSIER.md` | At least one quote + scope agreed |
| 9 | Write the ADR for tenancy/auth/RBAC | `docs/adr/0007-*.md` | Reviewed and merged before EN-01 code |
| 10 | Start design-partner outreach with the honest benchmark | `growth/launch-kit.md` | 5 calls booked; 3 pilots scoped |

---

## Appendix A — Evidence log (2026-10-18)

Commands run against `main` @ `8e478912`; outputs summarized.

| Check | Result |
|---|---|
| `gh api repos/humoge7502/q-trust` | 0 stars, 0 forks, 0 watchers, 3 contributors, 42 open PRs (all Dependabot), 0 non-bot PRs |
| `gh run list --branch main --workflow ci.yml` | Last CI success 2026-09-20; no run since |
| `gh run view 39158186925 --log-failed` | PR CI fails on `npm audit --audit-level=high` (fastify, fast-uri, ip-address, fast-copy, brace-expansion) |
| `npm audit --package-lock-only` (backend) | 6 vulnerabilities (3 high, 3 moderate) |
| `npm view fastify version` | 5.12.7 (fix available) |
| `curl https://pypi.org/pypi/qtrust-inspector/json` | PyPI latest 2.2.0; GitHub latest release v2.2.2, draft v2.2.3; manifests 2.2.0 |
| `curl https://huggingface.co/api/spaces/KRISHNAPURI/q-trust-scanner` | space exists, `sdk: static`, owned by `KRISHNAPURI`, last modified 2026-09-20 |
| `curl https://humoge7502.github.io/q-trust/` | HTTP 200 |
| `curl .../q-trust/.well-known/security.txt` | **404** (canonical URL advertised in the file itself); `frontend/public/.well-known/security.txt` exists |
| `curl https://github.com/humoge7502/q-trust/security/advisories/new` | HTTP 200 (private reporting available) |
| `grep` for auth/tenancy/audit log | API-key-only auth; no org/tenant model; no audit log |
| `grep` for KMS/HSM/K8s/CT | no cloud KMS/HSM/CT connectors; K8s **policy generation** exists (`k8s_policy.py`) |
| `find qtrust_data -type f` | only `.gitkeep`, `__init__.py`, `raw/popularity-list-top1k.csv` |
| `grep` for stubs | CP-SAT greedy fallback, digital twin placeholder, what-if hard-coded, temporal/RL/discovery stubs |
| `python3 -m compileall` | all Python packages compile (syntax clean) |

## Appendix B — Claim-to-source index

| Claim | Source of truth | Current mismatch |
|---|---|---|
| "τ 0.975 GNN accuracy" | `planner/results/real_cbom_loo_42.json` (τ-b 0.7168) | In-distribution number used as headline |
| "211 contract tests" | `PROJECT_SCORECARD.md` (213) | Stale count |
| "7 compliance frameworks" | `inspector/qtrust_inspector/compliance.py:12-24` (11) | Stale count |
| "10 scanner modules" | `inspector/qtrust_inspector/` (27 modules) | Understated / undefined metric |
| "PyPI latest" | PyPI 2.2.0 vs release v2.2.2 / draft v2.2.3 / manifests 2.2.0 | Three-way release drift |
| "Reproducible data pipeline" | `qtrust_data/` (empty), `dvc.yaml` (evaluate only) | Not reproducible |
| "Production ready" | `SECURITY.md` ("research / pre-release") | Positioning conflict |

## Appendix C — Review cadence

- Re-run the evidence log **monthly** and update the KPI table.
- Review this document **quarterly**; move completed items to
  `PROJECT_SCORECARD.md` with the evidence link.
- Any new public claim must be added to Appendix B with its artifact before it
  ships. That single rule is what keeps "best" honest.






