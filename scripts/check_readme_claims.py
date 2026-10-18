#!/usr/bin/env python3
"""Fail when public README claims drift from repository evidence.

The README is the project's front door, so it is checked like code:

* every in-distribution metric is explicitly labeled (``synthetic`` or
  ``in-distribution``) — out-of-sample numbers are the only unqualified ones;
* counts (contract tests, compliance frameworks, scanner modules) match the
  source of truth in the repository;
* no known-stale numbers remain;
* relative links resolve;
* the two published ``security.txt`` copies are byte-identical and contain no
  placeholder domain.

Run locally: ``python scripts/check_readme_claims.py``
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
COMPLIANCE = ROOT / "inspector" / "qtrust_inspector" / "compliance.py"
INSPECTOR = ROOT / "inspector" / "qtrust_inspector"
SCORECARD = ROOT / "PROJECT_SCORECARD.md"
SECURITY_TXT = ROOT / ".well-known" / "security.txt"
FRONTEND_SECURITY_TXT = ROOT / "frontend" / "public" / ".well-known" / "security.txt"


def _read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def compliance_framework_count() -> int:
    """Count enum members in ``ComplianceFramework``."""
    text = _read(COMPLIANCE)
    block = re.search(
        r"class ComplianceFramework\(str,\s*Enum\):(.*?)(?=\n\nclass\s)",
        text,
        re.S,
    )
    if not block:
        raise SystemExit("could not locate ComplianceFramework enum")
    return len(re.findall(r"^\s{4}[A-Z0-9_]+\s*=\s*['\"]", block.group(1), re.M))


def scanner_module_count() -> int:
    """Count importable modules in the inspector package (exclude ``__init__``)."""
    return len([p for p in INSPECTOR.glob("*.py") if p.name != "__init__.py"])


def contract_test_count() -> int:
    """Read the executed forge count recorded in the project scorecard."""
    match = re.search(r"forge\s+\*{0,2}(\d+)/\1", _read(SCORECARD))
    if not match:
        raise SystemExit("could not find 'forge N/N' in PROJECT_SCORECARD.md")
    return int(match.group(1))


def check_metric_labels(readme: str, errors: list[str]) -> None:
    for lineno, line in enumerate(readme.splitlines(), 1):
        if "0.975" not in line:
            continue
        lowered = line.lower()
        if "synthetic" not in lowered and "in-distribution" not in lowered:
            errors.append(
                f"README:{lineno}: in-distribution 0.975 must be labeled "
                "'synthetic' or 'in-distribution'"
            )
    if "0.7168" not in readme:
        errors.append("README: missing the out-of-sample τ-b 0.7168 headline")
    if "0.7210" not in readme:
        errors.append("README: missing the doctrine-heuristic τ-b 0.7210 comparison")


def check_counts(readme: str, errors: list[str]) -> None:
    frameworks = compliance_framework_count()
    modules = scanner_module_count()
    tests = contract_test_count()

    expected = {
        f"**{frameworks}**<br>compliance frameworks": "compliance framework count",
        f"{frameworks} rule sets": "compliance rule-set count",
        f"**{modules}**<br>scanner modules": "scanner module count",
        f"**{tests}**<br>contract tests": "contract test count",
        f"Foundry — {tests} tests": "Foundry test count",
    }
    for needle, label in expected.items():
        if needle not in readme:
            errors.append(f"README: {label} is stale (expected {needle!r})")

    # 211 is the superseded forge count; 213 is current. Catch reintroduction.
    if re.search(r"\b211\b", readme):
        errors.append("README: stale contract-test count 211 (expected 213)")


def check_links(readme: str, errors: list[str]) -> None:
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", readme):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = target.split("#", 1)[0]
        if path and not (ROOT / path).exists():
            errors.append(f"README: broken relative link {target!r}")


def check_security_txt(errors: list[str]) -> None:
    root = _read(SECURITY_TXT)
    frontend = _read(FRONTEND_SECURITY_TXT)
    if root != frontend:
        errors.append(
            "security.txt copies differ: .well-known/security.txt and "
            "frontend/public/.well-known/security.txt"
        )
    for placeholder in ("qtrust.example", "example.com"):
        if placeholder in root:
            errors.append(f"security.txt still contains placeholder domain {placeholder!r}")
    for required in ("Contact:", "Expires:", "Canonical:", "Policy:"):
        if required not in root:
            errors.append(f"security.txt missing required field {required!r}")


def main() -> int:
    readme = _read(README)
    errors: list[str] = []
    check_metric_labels(readme, errors)
    check_counts(readme, errors)
    check_links(readme, errors)
    check_security_txt(errors)

    if errors:
        print("README claim check failed:\n", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        "README claims OK: "
        f"{contract_test_count()} contract tests, "
        f"{compliance_framework_count()} compliance frameworks, "
        f"{scanner_module_count()} scanner modules, out-of-sample τ-b 0.7168."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
