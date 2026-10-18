# Q-Trust Factory

> **RESEARCH ONLY — not part of the shipped product.** This package is the
> experiment/benchmark factory behind the papers and the `planner/` model. It
> is **not imported by** `backend/`, `planner/`, `inspector/`, `frontend/`, or
> `sdk/`, and several modules are explicit CPU stubs (greedy CP-SAT, placeholder
> digital twin, hard-coded what-if, synthetic graph builder). Do not present
> these as customer-facing capabilities. The product planner lives in
> `planner/qtrust_planner/`; see `docs/TRUTH_AUDIT.md` for the claim
> classification of every metric.

See `../README_FACTORY.md` for full 64-section strategy.

Quick start:
```bash
python scripts/train_factory.py --phase all
dvc repro
python -m qtrust.evaluation.run_all --splits qtrust_data/splits --out qtrust_bench/evaluation/report.json
```

Structure:
- `data/` — lineage, bronze, splits (hash-anchored)
- `data_pipeline/` — GitHub, CodeQL, Semgrep, AST, runtime, normalization
- `labeling/` — weak, active_learning, gold_builder (7 dims)
- `models/` — discovery, risk (pairwise), graph (blast radius), migration (cost/failure/interop), temporal, what_if, digital_twin
- `benchmarks/` — synthetic, real_world, expert, temporal, adversarial
- `evaluation/` — metrics (Critical Recall), calibration, robustness, leakage
- `mlops/` — MLflow, DVC, registry (shadow gates)
