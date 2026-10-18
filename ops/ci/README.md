# CI workflow hardening — apply with a `workflows`-scoped identity

`workflow-hardening.patch` contains the CI/CD changes built alongside the P0
credibility and supply-chain work. They are kept as a patch because the
automation identity used for this branch is a GitHub App **without the
`workflows` permission**: any git push that touches `.github/workflows/*` is
rejected with:

```
refusing to allow a GitHub App to create or update workflow ... without `workflows` permission
```

The patch is not speculative: the scripts it calls are committed and tested.

## What it adds

| File | Change | Why |
|---|---|---|
| `ci.yml` | `docs-contract` job | runs `scripts/check_version_sync.py` and `scripts/check_readme_claims.py` |
| `ci.yml` | `benchmark-artifacts` job | runs `scripts/check_benchmark_artifacts.py` against committed LOO/RL/CodeBERTa JSON |
| `ci.yml` | weekly `schedule` | catches advisory drift when `main` is idle (it went a month without full CI) |
| `ci.yml` | frontend audit `--omit=dev` | the full tree carries an unpatched dev-only `brace-expansion` advisory via `eslint-config-next`; the runtime tree is clean |
| `security.yml` | daily `npm-audit` matrix | backend (full), frontend and docs-v2 (runtime) |
| `docs.yml` | publish `.well-known/security.txt` | the advertised RFC 9116 URL currently 404s on Pages |
| `publish-docker.yml` | SBOM + max provenance + keyless cosign | images become verifiable |
| `publish-pypi.yml` | `attestations: write` | PEP 740 attestations for wheels |
| `release.yml` | keyless cosign signatures for wheel/sdist | release artifacts carry receipts |

## Apply

From the repository root:

```bash
git apply --check ops/ci/workflow-hardening.patch
git apply ops/ci/workflow-hardening.patch
git add .github/workflows
git commit -m "ci: enforce claim, benchmark, audit, and supply-chain gates"
git push
```

If the files have moved since this branch, use `git apply --3way` and resolve.

## Verify before merging

```bash
python scripts/check_version_sync.py
python scripts/check_readme_claims.py
python scripts/check_benchmark_artifacts.py
npx --yes js-yaml .github/workflows/ci.yml >/dev/null   # YAML parse
actionlint .github/workflows/                          # if installed
```

The two Python gates are stdlib-only and run in seconds; the benchmark gate
does not need the corpus (it warns and skips the host-disjointness check unless
`--require-corpus` is passed).
