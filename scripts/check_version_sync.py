#!/usr/bin/env python3
"""Assert every release-bearing manifest carries the same version.

The repo has four independently published/deployed manifests (backend,
frontend, SDK, inspector) plus GitHub releases and PyPI. They drifted before
(v2.2.2/v2.2.3 releases against v2.2.0 manifests), so CI now fails on drift.

Run locally: ``python scripts/check_version_sync.py``
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


def json_version(path: Path) -> str:
    return json.loads(path.read_text(encoding="utf-8"))["version"]


def pyproject_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    if not match:
        raise SystemExit(f"no [project].version in {path.relative_to(ROOT)}")
    return match.group(1)


def main() -> int:
    manifests = {
        "backend/package.json": json_version(ROOT / "backend/package.json"),
        "frontend/package.json": json_version(ROOT / "frontend/package.json"),
        "sdk/pyproject.toml": pyproject_version(ROOT / "sdk/pyproject.toml"),
        "inspector/pyproject.toml": pyproject_version(ROOT / "inspector/pyproject.toml"),
    }

    errors: list[str] = []
    for name, version in manifests.items():
        if not SEMVER.match(version):
            errors.append(f"{name}: {version!r} is not semver")

    unique = set(manifests.values())
    if len(unique) != 1:
        errors.append(
            "version drift: "
            + ", ".join(f"{name}={version}" for name, version in manifests.items())
        )

    if errors:
        print("Version sync check failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Version sync OK: {unique.pop()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
