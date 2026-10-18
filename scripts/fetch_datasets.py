#!/usr/bin/env python3
"""Fetch the published Q-Trust datasets from Hugging Face with checksum checks.

The repository intentionally does not vendor the corpus (hundreds of MB). The
authoritative package lives at:

    https://huggingface.co/datasets/KRISHNAPURI/q-trust-datasets

Every download is verified against the package's SHA256SUMS.txt. A mismatch is
a hard failure — never a warning.

Examples:
    python scripts/fetch_datasets.py --subset manifest
    python scripts/fetch_datasets.py --subset parquet
    python scripts/fetch_datasets.py --subset cboms --dest qtrust_data/hf
    python scripts/fetch_datasets.py --subset all

Subsets:
    manifest  README, DATASETS.md, manifest.json, SHA256SUMS.txt (small)
    parquet   typed tables (riskbench pairs, migration outcomes, code features)
    corpus    the canonical 42-CBOM / 277-host corpus (E-06)
    cboms     the corpus + planner estate fixtures used by the RL benchmark
    code      the real code corpus (large; ~200 MB)
    all       every file in the dataset tree (~375 MB)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = "KRISHNAPURI/q-trust-datasets"
BASE = f"https://huggingface.co/datasets/{REPO}/resolve/main/"
TREE = f"https://huggingface.co/api/datasets/{REPO}/tree/main?recursive=true"
ROOT = Path(__file__).resolve().parents[1]

MANIFEST_FILES = {"README.md", "DATASETS.md", "manifest.json", "SHA256SUMS.txt"}
SUBSET_PREFIXES = {
    "parquet": ("parquet/",),
    "corpus": ("qtrust_data/gold/cboms/",),
    "cboms": (
        "qtrust_data/gold/cboms/",
        "planner/data/real_cboms",
        "planner/data/estates",
        "planner/data/algorithms.json",
    ),
    "code": ("code_corpus.json", "parquet/crypto-code.parquet"),
}


def _opener(insecure: bool):
    context = ssl._create_unverified_context() if insecure else ssl.create_default_context()
    return urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))


def _get(opener, url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "qtrust-fetch-datasets/1"})
    with opener.open(request, timeout=60) as response:
        return response.read()


def list_files(opener) -> list[dict]:
    return json.loads(_get(opener, TREE))


def parse_checksums(text: str) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        digest, path = parts
        checksums[path.lstrip("*").strip()] = digest.lower()
    return checksums


def selected(path: str, subset: str, size: int) -> bool:
    if path in MANIFEST_FILES:
        return True
    if subset == "manifest":
        return False
    if subset == "all":
        return True
    prefixes = SUBSET_PREFIXES[subset]
    return any(path == prefix or path.startswith(prefix) for prefix in prefixes)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(
    opener,
    path: str,
    dest: Path,
    expected: str | None,
    allow_drift: bool,
) -> tuple[str, dict | None]:
    target = dest / path
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and expected and sha256_file(target) == expected:
        return "cached", None

    url = BASE + urllib.parse.quote(path)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        request = urllib.request.Request(url, headers={"User-Agent": "qtrust-fetch-datasets/1"})
        with opener.open(request, timeout=120) as response:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)

    actual = sha256_file(temp_path)
    drift: dict | None = None
    if expected and actual != expected:
        if not allow_drift:
            temp_path.unlink(missing_ok=True)
            raise SystemExit(
                f"checksum mismatch for {path}\n  expected {expected}\n  actual   {actual}\n"
                "Re-run with --allow-checksum-drift only if you accept the published "
                "package drifted from its SHA256SUMS.txt."
            )
        drift = {
            "path": path,
            "expected": expected,
            "actual": actual,
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
    os.replace(temp_path, target)
    return ("downloaded" if expected else "downloaded (no checksum published)"), drift


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--subset",
        choices=["manifest", "parquet", "corpus", "cboms", "code", "all"],
        default="manifest",
    )
    parser.add_argument("--dest", type=Path, default=ROOT / "qtrust_data" / "hf")
    parser.add_argument("--dry-run", action="store_true", help="list what would be downloaded")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="disable TLS verification (only behind a trusted interception proxy)",
    )
    parser.add_argument(
        "--allow-checksum-drift",
        action="store_true",
        help="record (do not fail) files that differ from SHA256SUMS.txt",
    )
    args = parser.parse_args()

    opener = _opener(args.insecure)
    files = [item for item in list_files(opener) if item.get("type") == "file"]
    chosen = [item for item in files if selected(item["path"], args.subset, item.get("size", 0))]

    if not chosen:
        print("No files matched; nothing to do.", file=sys.stderr)
        return 1

    total_mb = sum(item.get("size", 0) for item in chosen) / 1e6
    print(f"{len(chosen)} files, {total_mb:.1f} MB → {args.dest}")
    if args.dry_run:
        for item in chosen:
            print(f"  {item['path']} ({item.get('size', 0) / 1e6:.2f} MB)")
        return 0

    checksums = parse_checksums(_get(opener, BASE + "SHA256SUMS.txt").decode("utf-8"))
    failures = 0
    drifts: list[dict] = []
    for index, item in enumerate(chosen, 1):
        path = item["path"]
        expected = checksums.get(path)
        try:
            status, drift = download(
                opener,
                path,
                args.dest,
                expected,
                args.allow_checksum_drift,
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"[{index}/{len(chosen)}] FAILED {path}: {exc}", file=sys.stderr)
            failures += 1
            continue
        if drift:
            drifts.append(drift)
            print(
                f"[{index}/{len(chosen)}] DRIFT    {path} "
                f"(expected {drift['expected'][:12]}…, got {drift['actual'][:12]}…)",
                file=sys.stderr,
            )
        else:
            print(f"[{index}/{len(chosen)}] {status:9s} {path}")

    if drifts:
        ledger = args.dest / "FETCH_LEDGER.json"
        existing: dict = {"files": {}}
        if ledger.exists():
            try:
                existing = json.loads(ledger.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {"files": {}}
        existing.setdefault("files", {})
        for drift in drifts:
            existing["files"][drift["path"]] = drift
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        ledger.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(
            f"WARNING: {len(drifts)} file(s) drifted from the published SHA256SUMS.txt; "
            f"recorded in {ledger}",
            file=sys.stderr,
        )

    if failures:
        print(f"{failures} download(s) failed", file=sys.stderr)
        return 1
    if drifts:
        print(
            f"Dataset fetch complete with {len(drifts)} recorded checksum drift(s); "
            "inspect FETCH_LEDGER.json before using the data."
        )
    else:
        print("Dataset fetch complete; all published checksums verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
