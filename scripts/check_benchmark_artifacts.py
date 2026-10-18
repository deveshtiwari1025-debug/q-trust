#!/usr/bin/env python3
"""Gate committed benchmark artifacts against the claims the README makes.

An ML result is only trustworthy if the artifact that produced it cannot drift
silently. This script re-reads the committed JSON and fails when a headline
number, fold count, provenance field, or baseline relationship changes.

Run locally: ``python scripts/check_benchmark_artifacts.py``
Release gate: add ``--require-corpus`` to also require the fetched 42-CBOM
corpus and verify host-disjointness.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOO_42 = ROOT / "planner" / "results" / "real_cbom_loo_42.json"
LOO_40 = ROOT / "planner" / "results" / "real_cbom_loo_40.json"
RL_REAL = ROOT / "planner" / "results" / "rl_benchmark_real_cbom.json"
CODEBERT = ROOT / "qtrust_ai" / "artifacts" / "benchmark_comparison.json"
CORPUS_CANDIDATES = (
    ROOT / "qtrust_data" / "hf" / "qtrust_data" / "gold" / "cboms",
    ROOT / "qtrust_data" / "gold" / "cboms",
    ROOT / "planner" / "data" / "real_cboms_v2_2026_09_18",
    ROOT / "qtrust_data" / "hf" / "planner" / "data" / "real_cboms_v2_2026_09_18",
)

TOL = 0.0005


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing benchmark artifact: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def close(actual: float, expected: float, label: str, errors: list[str], tol: float = TOL) -> None:
    if abs(actual - expected) > tol:
        errors.append(f"{label}: expected {expected:.4f} ± {tol}, got {actual:.4f}")


def check_loo_42(errors: list[str]) -> None:
    data = load(LOO_42)
    if data.get("n_cboms") != 42:
        errors.append(f"LOO-42 n_cboms: expected 42, got {data.get('n_cboms')}")
    if data.get("n_hosts") != 277:
        errors.append(f"LOO-42 n_hosts: expected 277, got {data.get('n_hosts')}")
    if len(data.get("fold_metrics", {})) != 42:
        errors.append(f"LOO-42 fold_metrics: expected 42 folds, got {len(data.get('fold_metrics', {}))}")
    if "host-disjoint" not in str(data.get("protocol", "")).lower():
        errors.append("LOO-42 protocol does not state host-disjoint")

    model = data["aggregate"]["model"]["kendall"]["mean"]
    heuristic = data["aggregate"]["heuristic"]["kendall"]["mean"]
    close(model, 0.7168, "LOO-42 model τ-b", errors)
    close(heuristic, 0.7210, "LOO-42 heuristic τ-b", errors)
    close(data["model_vs_heuristic_tau_b"], model - heuristic, "LOO-42 Δ", errors, 0.0001)
    if data["aggregate"]["model"]["top10"]["mean"] != 1.0:
        errors.append("LOO-42 model top-10 is no longer 1.0 on every fold")

    config = data.get("config", {})
    if config.get("seed") != 42 or config.get("epochs") != 30 or config.get("n_synthetic") != 2000:
        errors.append(f"LOO-42 provenance drifted: {config}")
    if not data.get("device"):
        errors.append("LOO-42 device provenance is missing")


def check_loo_40(errors: list[str]) -> None:
    data = load(LOO_40)
    if data.get("n_cboms") != 40:
        errors.append(f"LOO-40 n_cboms: expected 40, got {data.get('n_cboms')}")


def check_rl(errors: list[str]) -> None:
    data = load(RL_REAL)
    if data.get("n_envs") != 40:
        errors.append(f"RL n_envs: expected 40, got {data.get('n_envs')}")
    close(data["agent_mean_reward"], 140.343, "RL agent reward", errors, 0.01)
    close(data["heuristic_mean_reward"], 140.622, "RL heuristic reward", errors, 0.01)
    close(data["agent_vs_heuristic"], -0.279, "RL agent−heuristic", errors, 0.01)
    if data.get("agent_completion_rate") != 1.0:
        errors.append("RL completion rate is no longer 100%")


def check_codebert(errors: list[str]) -> None:
    data = load(CODEBERT)
    if data.get("seed") != 42:
        errors.append(f"CodeBERTa seed: expected 42, got {data.get('seed')}")
    comparison = next(
        (
            item
            for item in data.get("comparisons", [])
            if item.get("model", "").endswith("CryptoCodeDetector")
        ),
        None,
    )
    if comparison is None:
        errors.append("CodeBERTa artifact has no CryptoCodeDetector comparison")
        return
    if comparison.get("n") != 2415:
        errors.append(f"CodeBERTa n: expected 2415, got {comparison.get('n')}")
    qtrust = comparison.get("qtrust", {})
    close(qtrust.get("precision", 0), 0.952, "CodeBERTa precision", errors, 0.001)
    close(qtrust.get("recall", 0), 0.953, "CodeBERTa recall", errors, 0.001)
    close(qtrust.get("f1", 0), 0.9525, "CodeBERTa F1", errors, 0.001)


def check_corpus(errors: list[str], require: bool, warnings: list[str]) -> None:
    corpus = next((path for path in CORPUS_CANDIDATES if path.exists()), None)
    if corpus is None:
        message = (
            "42-CBOM corpus is not present; run "
            "'python scripts/fetch_datasets.py --subset corpus' to verify host-disjointness"
        )
        (errors if require else warnings).append(message)
        return

    files = [path for path in sorted(corpus.glob("*.json")) if path.name.upper() != "MANIFEST.JSON"]
    hosts: list[str] = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        for asset in data.get("assets", []):
            host = str(asset.get("host") or "").strip()
            if host:
                hosts.append(host)

    if len(files) != 42:
        errors.append(f"corpus files: expected 42, got {len(files)} ({corpus.relative_to(ROOT)})")
    if len(set(hosts)) != 277:
        errors.append(f"corpus unique hosts: expected 277, got {len(set(hosts))}")
    if len(hosts) != len(set(hosts)):
        errors.append(f"corpus host overlap: {len(hosts) - len(set(hosts))} duplicate asset-hosts")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-corpus",
        action="store_true",
        help="fail when the fetched 42-CBOM corpus is absent",
    )
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    check_loo_42(errors)
    check_loo_40(errors)
    check_rl(errors)
    check_codebert(errors)
    check_corpus(errors, args.require_corpus, warnings)

    for warning in warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    if errors:
        print("Benchmark artifact gate failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        "Benchmark artifacts OK: LOO-42 τ-b 0.7168 vs 0.7210, RL 140.343 vs "
        "140.622, CodeBERTa F1 0.9525 (n=2415)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
