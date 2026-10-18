# Reproducing Q-Trust's Benchmarks

This guide is for an independent reviewer. It assumes no access to the
maintainer, no private credentials, and no trust in the numbers in
`README.md`. The fast verification commands were exercised against `main` @
`8e478912` on 2026-10-18; the GPU runs are documented from the committed
artifacts and require A100-class hardware.

> **What is reproducible without a GPU:** scanner results, CBOM output, ACVP
> vectors, contract tests, API tests, the recommendation policy, and the
> dataset checksums. **What needs a GPU:** the 42-fold LOO fine-tune (E-06),
> side-channel retrain (E-07), and RL benchmark. The committed result JSONs are
> the evidence for those; their SHA-256s are below.

## 1. Environment

| Component | Version used |
|---|---|
| Python | 3.11 (3.10+ supported) |
| Node | 20+ (24 works) |
| Foundry | latest stable (`forge`, `anvil`) |
| CUDA | A100-class for the LOO/RL retrains; CPU works for tests |

```bash
git clone https://github.com/humoge7502/q-trust.git
cd q-trust
python3 -m venv .venv && . .venv/bin/activate
pip install -e "./inspector[dev,ml]" -e "./sdk[dev]"
pip install -r planner/requirements.txt pytest httpx scipy numpy
(cd backend && npm ci)
(cd frontend && npm ci)
```

## 2. Get the data (checksum-verified)

The corpus is **not** vendored in Git. It lives at
<https://huggingface.co/datasets/KRISHNAPURI/q-trust-datasets>.

```bash
python scripts/fetch_datasets.py --subset manifest
python scripts/fetch_datasets.py --subset parquet
python scripts/fetch_datasets.py --subset cboms
# optional, large (~200 MB): python scripts/fetch_datasets.py --subset code
```

A mismatch is a hard failure. **Known upstream drift (2026-10-18):** the
package's own `DATASETS.md` does not match its `SHA256SUMS.txt`
(expected `d500bae0…`, actual `f0cd54a4…`). Use
`--allow-checksum-drift` only for that metadata file; the script records the
observed hash in `qtrust_data/hf/FETCH_LEDGER.json`. Data files must verify
without that flag.

If `pip` cannot reach PyPI because of a TLS interception proxy, use the
environment's package mirror; do not disable TLS verification for code.

## 3. Fast verification (no GPU)

```bash
# Scanner: produces a CycloneDX 1.7 CBOM with line-level evidence
crypto-inspector scan example.com --risk --compliance nist,cnsa \
  --cyclonedx /tmp/cbom.json --evidence /tmp/ledger.json

# Contract suite (213 tests: unit + invariant + fuzz + attack)
(cd contracts && forge test)

# Python suites
pytest planner/tests inspector/tests sdk/tests qtrust_ai/tests -q

# Backend and frontend
(cd backend && npm run typecheck && npm test)
(cd frontend && npm test)

# ACVP oracle vectors + liboqs KATs (skip cleanly without liboqs binaries)
pytest inspector/tests/test_acvp_vectors.py inspector/tests/test_liboqs_kats.py -q

# Model integrity (pins committed checkpoints)
./scripts/verify_models.sh

# Headline artifacts still match the documented numbers/provenance
python scripts/check_benchmark_artifacts.py
python scripts/check_benchmark_artifacts.py --require-corpus  # after --subset cboms
```

The plan API now returns a deterministic `recommendation` object per asset
(target algorithm, alternative, standard, rationale, confidence). Check it
without a model:

```bash
pytest planner/tests/test_recommend.py -q
```

## 4. Reproduce E-06 — 42-fold host-disjoint LOO (GPU)

Corpus: `qtrust_data/hf/qtrust_data/gold/cboms/` after `--subset corpus`
(42 CBOM files + `MANIFEST.json`, 277 unique hosts, zero cross-CBOM overlap).
The repository keeps the historical 40-CBOM corpus under
`planner/data/real_cboms/`. Note: the package's
`planner/data/real_cboms_v2_2026_09_18/` directory is **incomplete** (38 of 42
CBOMs); use `qtrust_data/gold/cboms/` for E-06. The protocol fine-tunes a fresh
model per fold on the other 41 + synthetic mix and scores the held-out estate.

```bash
python scripts/fetch_datasets.py --subset corpus

python scripts/eval_real_cbom_loo.py --quick \
  --cbom-dir qtrust_data/hf/qtrust_data/gold/cboms \
  --out /tmp/loo_quick.json          # 3-fold smoke; CPU-feasible but slow

# Full run (2×A100 used for the published number; 30 epochs)
python scripts/eval_real_cbom_loo.py --epochs 30 --seed 42 \
  --cbom-dir qtrust_data/hf/qtrust_data/gold/cboms \
  --out planner/results/real_cbom_loo_42_reproduced.json
```

Expected out-of-sample result (the published tie):

| Metric | Value |
|---|---|
| Model τ-b | **0.7168** |
| Doctrine heuristic τ-b | **0.7210** |
| Δ | **−0.0042** (medians identical, 0.7237) |
| Fold outcomes | 0 wins / 41 ties / 1 loss |
| Model top-10 | 1.0 on every fold |
| vs random | **+0.687** |

The model does **not** beat the heuristic. That is the honest result; beating it
requires the expert pairwise labels in `QTrust-RiskBench`.

## 5. Artifact hashes (what “reproduced” means)

```text
083000fd320c57bcc2ecfd7b1ab29bd4e50b1ab1f19bd8cc1226f0511e0699d1  planner/results/real_cbom_loo_42.json
cf8684baff7e4c781227f64e3c0fa8b15a047dbdfbb379b2e8470c446f0c1233  planner/results/benchmark_v3.json
d9447579a5a797b2b34f88e69d67f24a3692501e775862059c2946bea95b593c  planner/results/real_cbom_loo_40.json
df64c73d33f506482af3633f8d78ce96240acb4e2f14ded0b5fde9f15972b845  qtrust_ai/artifacts/training_report_real.json
08baced4eecec1f9382be05510c75dc275431215138a4064b39bc15816455d65  qtrust_ai/artifacts/benchmark_comparison.json
2b04b639b8838d8ef06adfd09e25db2b40b63cf079bbc3819dc5df92f7a8cc5f  inspector/tests/test_acvp_vectors.py
```

A retrain need not be bit-identical across GPUs (nondeterministic kernels), but
the protocol, seeds, corpus, and reported deltas must reproduce. If they do
not, open an issue with the command, the artifact hash, and the GPU model.
