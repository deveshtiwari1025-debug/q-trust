# Q-Trust deployment status

_Last updated: 2026-10-20_

## Live now

| Component | Where | URL / reference |
|---|---|---|
| Frontend | Vercel (`q-trust`, team `devesh-tiwari-p-projects1`) | https://q-trust-nu.vercel.app |
| Backend API | **Vercel serverless** (`qtrust-backend`) — Fastify bridge at `backend/api/index.mjs` | https://qtrust-backend.vercel.app/api |
| Indexer | Docker on this machine (`qtrust-api`), writing to the hosted Postgres | runs inside the local API container |
| Python scanner + evidence chain | Docker on this machine, exposed through a Cloudflare quick tunnel; the hosted API proxies `/v1/scan/*` and `/v1/evidence/*` there | https://sculpture-stylus-ultimate-burning.trycloudflare.com |
| GNN planner (v3, CPU) | Docker on this machine (`qtrust-planner:2.2.0`), exposed with a second Cloudflare quick tunnel | https://accordingly-thumbzilla-following-intake.trycloudflare.com |
| Postgres (hosted) | Neon, provisioned through the Vercel Marketplace | resource `quiet-sound-15608005`; pooled URL in `frontend/.env.local` `DATABASE_URL`, unpooled in `.env` `QTRUST_EXTERNAL_PG_URL` |
| Postgres (local) | Docker on this machine (fallback/demo only) | `qtrust-postgres` (127.0.0.1:5433) |
| Redis | Docker on this machine (local API only; not used by the hosted API) | `qtrust-redis` (127.0.0.1:6379) |
| Contracts | Base Sepolia (chain 84532) | see `deploy/logs/contracts-deploy.log` and `.env` |

Vercel Deployment Protection is **disabled** for the `q-trust` project so the
site is publicly reachable.

### How the hosted split works

- The backend runs as a single Vercel Function (`backend/api/index.mjs`). The
  function builds the same Fastify app as the Docker image
  (`backend/src/server.ts` exports `buildServer()`), never starts the indexer,
  and receives every request through one rewrite:
  `{"source":"/api/:path*","destination":"/api/index?__p=:path*"}`.
- Body parsing is disabled (`config.api.bodyParser = false`) so Fastify reads
  the raw request stream itself.
- `QTRUST_SCANNER_PROXY_URL` points at the local API tunnel; the hosted API
  forwards `/v1/scan/*` and `/v1/evidence/*` there (the caller's `x-api-key` is
  preserved, so the local API enforces the same policy). Everything else runs
  on Vercel, including planner calls through `QTRUST_PLANNER_URL`.
- The local API container was switched to the hosted Postgres with
  `docker-compose.override.yml` (`QTRUST_COMPOSE_PG_URL` in `.env`), so one
  Neon database backs both the local indexer and the deployed API.
- Provisioning/redeploying the hosted API:

  ```
  powershell -File deploy/vercel-backend.ps1                # sync env + deploy
  powershell -File deploy/vercel-backend.ps1 -SkipEnvSync   # deploy only
  ```

  The script creates/reuses the `qtrust-backend` project, upserts every
  `QTRUST_*` variable from `.env` with hosted overrides, writes
  `backend/.vercel/project.json`, and runs `vercel deploy --prod`.

### Smoke test (passed)

```
powershell -File deploy/smoke-test.ps1 `
  -ApiUrl https://qtrust-backend.vercel.app/api `
  -FrontendUrl https://q-trust-nu.vercel.app `
  -ScanDirectory /workspace/projects/backend/src
```

All checks passed: API health (chain 84532, relayer
`0xE610569aE0352DC3262419bb051a86145f52875c`), authenticated `/docs/json`,
planner plan (v3), scanner through the local tunnel, frontend HTTP 200.
Browser path also verified: `GET /api/health` through the frontend proxy,
`POST /api/v1/scan/source` with `x-qtrust-api-key`, and the rebuilt CSP now
allow-lists `https://qtrust-backend.vercel.app/api`.

The Vercel `/api/*` proxy intentionally **does not** attach the server-side
key to operator routes (planner/scanner/relayer/webhooks). Those require the
caller's own key in the `x-qtrust-api-key` header from the operator panel;
anonymous planner POSTs through the dashboard proxy return 403
`operator_key_required`. This is by design (`frontend/src/lib/api-route-policy`).

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
ETH via the OpenFaucet proof-of-work faucet); `DEFAULT_ADMIN_ROLE` was
renounced.

## Hosting blockers (checked 2026-10-20)

- **Render:** every service creation returns HTTP 402 ("Payment information is
  required") — including free web services and free databases. No API key or
  browser session for a billed workspace exists on this machine.
- **Hugging Face Docker Spaces:** creation now returns HTTP 402 as well —
  "hosting Gradio and Docker Spaces on free cpu-basic requires a PRO
  subscription". The available fine-grained token maps to account
  `KRISHNAPURI` (owner of the static `q-trust-scanner` Space) but the account
  is not PRO, so the no-card Docker Space fallback is closed.

The Vercel serverless deployment is the no-card path that works today.

## Remaining Render migration assets

- **Source repo:** `https://github.com/deveshtiwari1025-debug/q-trust`
  (public fork of `humoge7502/q-trust`; local `main` pushed through the latest
  deploy commit). The fork is required because the available credentials have
  no push access to the upstream repo.
- **Render account:** created and verified under
  `qtrust-render-c822318142@maxxspace.com` (temporary mailbox); API key is in
  `.env` as `RENDER_API_KEY`. Workspace `My Workspace`
  (`tea-dbb7bnnavr4c73d19i10`).
- **Neon Postgres:** free plan, connected to the Vercel project; the local
  indexer writes through `QTRUST_COMPOSE_PG_URL` (unpooled) and the hosted API
  reads through the pooled `DATABASE_URL`.
- **Redis:** not provisioned. The hosted API runs without Redis (webhook
  subscriptions return 503 there); the local API keeps Redis for full parity.
- **Deploy script:** `deploy/deploy-render.ps1` supports `-Plan free`,
  `-FreeTier`, `-SkipRedis`, `-ExternalPlannerUrl`, `-ExternalPgUrl`,
  `-ExternalRedisUrl`, `-RepoUrl`, and `-Branch`, with detailed HTTP error
  reporting.

If a Render workspace with billing becomes available, run:

```
powershell -File deploy/deploy-render.ps1 `
  -Plan free -FreeTier -SkipRedis `
  -RepoUrl https://github.com/deveshtiwari1025-debug/q-trust -Branch main `
  -ExternalPlannerUrl <current planner tunnel URL>
```

then re-point the Vercel env vars (`QTRUST_BACKEND_URL`,
`NEXT_PUBLIC_QTRUST_API_URL`) at the `onrender.com` URL and redeploy the
frontend.

## Planner sizing (measured)

| Service | Idle memory |
|---|---|
| API + indexer | ~93 MB |
| Planner (GNN v3, CPU) | ~462 MB |
| Postgres | ~32 MB |
| Redis | ~8 MB |

A planner container constrained with `--memory=512m --memory-swap=512m`
completed a 60-asset plan at 435–438 MiB with no OOM kill, so Render Free/
Starter (512 MB) is viable for demo workloads; inference spikes above that are
still possible. Render Standard (2 GB) remains the safe choice.

## Known limitations

- **The local machine must stay on** for the indexer, the Python scanner,
  the evidence chain, and the planner. If it goes offline, the hosted API keeps
  serving RPC-backed reads and the last indexed data, while `/v1/scan/*`,
  `/v1/evidence/*`, and `/v1/plans` fail (the hosted API returns 503 for
  proxied scanner calls and a planner error otherwise).
- **Tunnel URLs are not stable.** If `cloudflared` restarts, update
  `QTRUST_SCANNER_PROXY_URL` and `QTRUST_PLANNER_URL` for the Vercel project
  (rerun `deploy/vercel-backend.ps1` after updating `.env`) and redeploy the
  hosted API.
- **Serverless cold starts.** The first request after idle takes ~1–2 s while
  the Fastify app boots; `/tmp/qtrust` on Vercel is ephemeral (evidence is
  proxied to the local API, which keeps the durable chain).
- **In-memory rate limiting on Vercel** (120 req/min per warm instance,
  `QTRUST_RATE_LIMIT_MAX`). No Redis-backed shared limits there.
- **WalletConnect uses the public `demo` project ID** with
  `NEXT_PUBLIC_QTRUST_ALLOW_DEMO_WALLETCONNECT=1`. Connections work but are
  rate-limited. Create a project at https://cloud.walletconnect.com, then set
  `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID` and redeploy.
- **No custom domain.** The Vercel URLs are the production entry points for
  now.
- **The temporary Render account uses a disposable email.** If it becomes the
  permanent host, change the account email to one the user controls.
- **Shared secrets were rotated** after an accidental env dump in the local
  session log: API key, planner key, webhook encryption key, and VC issuer key.
  The Base Sepolia relayer/deployer keys were also visible in that log; they
  are testnet-only and the relayer cannot be rotated because
  `DEFAULT_ADMIN_ROLE` was renounced. Rotate the API keys again and drop the
  transition key from `QTRUST_API_KEYS`/`QTRUST_API_KEY` when convenient.
