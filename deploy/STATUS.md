# Q-Trust deployment status

_Last updated: 2026-10-20_

## Live now

| Component | Where | URL / reference |
|---|---|---|
| Frontend | Vercel (`q-trust`, team `devesh-tiwari-p-projects1`) | https://q-trust-nu.vercel.app |
| Backend API + indexer | Docker on this machine, exposed with a Cloudflare quick tunnel | https://sculpture-stylus-ultimate-burning.trycloudflare.com |
| GNN planner (v3, CPU) | Docker on this machine (`qtrust-planner:2.2.0`) | reachable only through the API (`POST /v1/plans`) |
| Postgres | Docker on this machine | `qtrust-postgres` (127.0.0.1:5433) |
| Redis / Key Value | Docker on this machine | `qtrust-redis` (127.0.0.1:6379) |
| Contracts | Base Sepolia (chain 84532) | see `deploy/logs/contracts-deploy.log` and `.env` |

Vercel Deployment Protection is **disabled** for the `q-trust` project so the
site is publicly reachable.

### Smoke test (passed)

```
powershell -File deploy/smoke-test.ps1 `
  -ApiUrl https://sculpture-stylus-ultimate-burning.trycloudflare.com `
  -FrontendUrl https://q-trust-nu.vercel.app `
  -ScanDirectory /workspace/projects/backend/src
```

All checks passed: API health, authenticated docs, planner plan, scanner,
frontend HTTP 200.

## Base Sepolia contracts

| Contract | Address |
|---|---|
| AssetRegistry | `0x98727508C2ca1dba85DbB10A1b1DBAc255c232BC` |
| VendorRegistry | `0xd8Bb8E02B2680A8C7D3b4788c038b6c727BD5607` |
| MigrationRegistry | `0xe5c71e228d49752434dA9D8Ec8F078d1bA45287D` |
| AuditRegistry | `0xDA8CFE63e53400ad6146A04C1dfBBfb1Dc17EA82` |
| RevocationAnchor | `0x2bb1F82E36554e22C3772e0f7a4E68d9ea16974f` |
| PolicyCommitment | `0xde9cBe5A3bC07A87F8BD0C0759CdbF53185C3187` |
| SchemaRegistry | `0x6d8d2B0018e4Df6599c9E39dE539D1CA6A908850` |
| TrustAnchorRegistry | `0xF89B94cC31725CF004Bbad8faA0cE64F58e7e15d` |

Indexer start block: `48333836`. Operational roles were granted to the relayer
`0xE610569aE0352DC3262419bb051a86145f52875c` (funded with 0.01 Base Sepolia
ETH via the OpenFaucet proof-of-work faucet).

## Known limitations

- **Backend is not on Render yet.** Render account creation is blocked by an
  hCaptcha challenge and no `RENDER_API_KEY` is available. The backend and
  planner currently run on this machine behind a temporary
  `*.trycloudflare.com` tunnel.
- **Tunnel URL is not stable.** If `cloudflared` restarts, the URL changes.
  Update `.env` (`QTRUST_PUBLIC_URL`, `QTRUST_BACKEND_URL`,
  `NEXT_PUBLIC_QTRUST_API_URL`) and the Vercel env vars
  (`QTRUST_BACKEND_URL`, `NEXT_PUBLIC_QTRUST_API_URL`), then redeploy:
  `cd frontend && vercel deploy --prod --yes`.
- **WalletConnect uses the public `demo` project ID** with
  `NEXT_PUBLIC_QTRUST_ALLOW_DEMO_WALLETCONNECT=1`. Connections work but are
  rate-limited. Create a project at https://cloud.walletconnect.com, then set
  `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID` and redeploy.
- **No custom domain.** The Vercel and trycloudflare URLs are the production
  entry points for now.
- **No GitHub push access.** The upstream repo (`humoge7502/q-trust`) is not
  writable with the available credentials, so local fixes are committed on
  `main` (`713a3d5`) but not pushed. Render blueprint/git deploys need a repo
  that contains those commits.

## Render sizing notes (for the eventual migration)

Measured locally with `docker stats`:

| Service | Idle memory |
|---|---|
| API + indexer | ~93 MB |
| Planner (GNN v3, CPU) | ~462 MB |
| Postgres | ~32 MB |
| Redis | ~8 MB |

- Backend + Postgres + Key Value fit Render's free plans.
- The planner sits close to the 512 MB limit on Free/Starter and can spike
  during inference; Render **Standard (2 GB)** is the safe choice.
- Render's free web services sleep on idle and free Postgres instances expire,
  so a long-lived deployment needs at least Starter for the backend/datastores.

## Next steps to finish the Render migration

1. Obtain a Render account/API key (human hCaptcha step or existing account).
2. Get the local commits onto a GitHub/GitLab repo Render can read
   (fork `humoge7502/q-trust`, push `main`, or grant a token with `repo` scope).
3. Run `deploy/deploy-render.ps1` with `-RepoUrl <your repo>` and the desired
   `-Plan`/`-Region`.
4. Point the Vercel env vars at the new `onrender.com` backend URL and redeploy.
5. Optionally set a real WalletConnect project ID and the custom domain.
