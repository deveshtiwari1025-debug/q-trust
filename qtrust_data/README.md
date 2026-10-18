# qtrust_data — working directory, not a data dump

The tracked directories (`raw/`, `bronze/`, `silver/`, `gold/`, `splits/`,
`annotations/`) intentionally contain only `.gitkeep` plus the public
popularity list. The real corpus and benchmark fixtures are **hundreds of
megabytes** and belong in a versioned dataset package, not in Git.

## Authoritative dataset package

<https://huggingface.co/datasets/KRISHNAPURI/q-trust-datasets>

Fetch it (checksums verified against the package's `SHA256SUMS.txt`):

```bash
# small: manifests, README, DATASETS.md, SHA256SUMS.txt
python scripts/fetch_datasets.py --subset manifest

# typed tables used by the risk/migration benchmarks
python scripts/fetch_datasets.py --subset parquet

# planner CBOM/estate fixtures used by the LOO benchmark
python scripts/fetch_datasets.py --subset corpus
python scripts/fetch_datasets.py --subset cboms

# the real code corpus (large)
python scripts/fetch_datasets.py --subset code

# everything (~375 MB)
python scripts/fetch_datasets.py --subset all
```

Default destination: `qtrust_data/hf/` (git-ignored). Use `--dest` to place it
elsewhere, `--dry-run` to inspect, and `--insecure` only behind a trusted
interception proxy.

**Checksum policy.** Data files must match `SHA256SUMS.txt` or the fetch fails.
Package metadata (`README.md`, `DATASETS.md`, `manifest.json`) is allowed to
drift with a recorded warning, because the package updates it without
regenerating sums. As of 2026-10-18 the published `DATASETS.md` does not match
the package's own `SHA256SUMS.txt` (expected `d500bae0…`, actual `f0cd54a4…`);
this is upstream drift, not a local error. `--allow-checksum-drift` does the
same for data files and records the expected/actual pair in
`FETCH_LEDGER.json`. Never use that flag for data files without inspecting the
ledger.

## What the pipeline expects

| Path | Used by |
|---|---|
| `qtrust_data/splits/` | `python -m qtrust.evaluation.run_all` (DVC evaluate stage) |
| `qtrust_data/gold/cboms/` (fetched) | **canonical 42-CBOM / 277-host corpus** for E-06 |
| `planner/data/real_cboms_v2_2026_09_18/` | historical package copy (38 of 42 files — do not use for E-06) |
| `planner/data/estates_v1/` | RL real-CBOM benchmark |
| `qtrust_ai/artifacts/real_datasets/` | CodeBERTa / risk / vendor training |

See [DATASETS.md](../DATASETS.md), [docs/TRUTH_AUDIT.md](../docs/TRUTH_AUDIT.md)
and [docs/REPRODUCE.md](../docs/REPRODUCE.md).
