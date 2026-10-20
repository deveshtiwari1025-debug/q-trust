# Q-Trust deployment status

_Last updated: 2026-10-20_

## Live now

| Component | Where | URL / reference |
|---|---|---|
| Frontend | Vercel (`q-trust`, team `devesh-tiwari-p-projects1`) | https://q-trust-nu.vercel.app |
| Backend API | **Vercel serverless** (`qtrust-backend`) — Fastify bridge at `backend/api/index.mjs` | https://qtrust-backend.vercel.app/api |
| Indexer | Docker on this machine (`qtrust-api`), writing to hosted Postgres | polls every 4 s; reorg check still runs |
| Python scanner + evidence chain | Docker on this machine, exposed through a Cloudflare quick tunnel; the hosted API proxies `/v1/scan/*` and `/v1/evidence/*` there | see `QTRUST_SCANNER_PROXY_URL` in `.env` |
| ML bridge (side-channel, anomaly, RL, quantum) | Same `qtrust-api` container, CPU-only torch + copied model weights (`/opt/qtrust-models`) | hosted API proxies `/v1/gpu/*` to it |
| GNN planner (v3 + RL) | Docker on this machine (`qtrust-planner:2.2.0`), exposed with a second Cloudflare quick tunnel | see `QTRUST_PLANNER_TUNNEL_URL` in `.env` |
| Postgres (hosted) | Neon, provisioned through the Vercel Marketplace | resource `quiet-sound-15608005`; pooled URL in `frontend/.env.local`, unpooled in `.env` |
| Postgres (local) | Docker on this machine (fallback/demo only) | `qtrust-postgres` (127.0.0.1:5433) |
| Redis | Docker on this machine (local API only; the hosted API uses an in-memory webhook fallback) | `qtrust-redis` (127.0.0.1:6379) |
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
- `QTRUST_SCANNER_PROXY_URL` points at the local API tunnel. The hosted API
  forwards `/v1/scan/`, `/v1/evidence/`, and `/v1/gpu/` there, preserving the
  caller's `x-api-key`, so the local API enforces the same policy. Everything
  else runs on Vercel, including planner calls through `QTRUST_PLANNER_URL`.
- The local API container was switched to the hosted Postgres with
  `docker-compose.override.yml` (`QTRUST_COMPOSE_PG_URL` in `.env`), so one
  Neon database backs both the local indexer and the deployed API.
- **Public compute for anonymous visitors.** The frontend proxy
  (`frontend/src/lib/api-route-policy.ts`) classifies scanner, evidence
  creation, Roadmap sync, planner, and GPU calls as `public-compute` and
  attaches the server key on the server side. Operator-only routes
  (`/v1/write/`, `/v1/relay/`, `/v1/webhooks/`, credential issuance) still
  require the caller's own key — this protects relayer gas and on-chain writes.
- **API docs are public** (`QTRUST_DOCS_PUBLIC=true`), so the header's
  "API docs" link works for everyone.
- **Indexer:** `watchEvent` now uses `poll: true` (HTTP transports have no push
  channel) and processes delivered logs immediately; reorg safety comes from the
  periodic `detectAndHandleReorg()` check. Address comparisons in read queries
  are case-insensitive (`lower(org_did) = lower($1)`), because contract events
  arrive checksummed while callers pass lowercase addresses.
- **CSP:** production `script-src` includes `'unsafe-inline'`. Next.js always
  emits inline bootstrap/RSC-streaming scripts; without it every page stayed on
  its loading skeleton because React never hydrated. The policy still locks
  down `object-src`, `base-uri`, `frame-ancestors`, and an explicit
  `connect-src` that includes the configured Base Sepolia RPC origin.
- Provisioning/redeploying the hosted API:

  ```
  powershell -File deploy/vercel-backend.ps1                # sync env + deploy
  powershell -File deploy/vercel-backend.ps1 -SkipEnvSync   # deploy only
  ```

  The script creates/reuses the `qtrust-backend` project, upserts every
  `QTRUST_*` variable from `.env` with hosted overrides, writes
  `backend/.vercel/project.json`, and runs `vercel deploy --prod`.

### Keeping the local half alive

`deploy/ensure-local-stack.ps1` is a safe-to-rerun watchdog:

1. starts Docker Desktop if it is not running;
2. ensures `postgres`, `redis`, `api`, and `planner` containers are up;
3. ensures both `cloudflared` quick tunnels exist (downloads `cloudflared` to
   `%LOCALAPPDATA%\qtrust\bin` on first use);
4. if a tunnel URL changed, updates `.env` and re-syncs + redeploys the Vercel
   backend automatically.

```
powershell -File deploy/ensure-local-stack.ps1                    # check once
powershell -File deploy/ensure-local-stack.ps1 -InstallStartup     # per-user, no admin
powershell -File deploy/ensure-local-stack.ps1 -InstallTask        # scheduled task, needs admin
```

The installed Startup-folder watcher (`QTrustLocalStack.vbs`) runs hidden at
logon and repeats every five minutes; `-InstallTask` is only an option for an
elevated shell. Logs: `deploy/logs/stack.log`. Container restart policies are
`unless-stopped`.

### Demo records (seeded and indexed)

`node backend/scripts/seed-demo-records.mjs` is idempotent: it reuses existing
CBOM documents, skips hashes already registered, records an RSA-2048 →
ML-KEM-768 migration, waits for the indexer, and writes
`deploy/demo-records.json` plus `frontend/src/lib/demo-records.json` (the home
page imports the latter to render its "Live on-chain records" strip, so redeploy
the frontend after reseeding).

| Target | Asset ID | Metadata |
|---|---|---|
| `/workspace/projects/inspector/qtrust_inspector` (23 findings) | `0x125fad1d7f435ea1dfeb014bdcbbbe0636fe7043b1e4e4ac90975768e3d1a349` | `/demo/cbom-inspector.json` |
| `/workspace/projects/planner/qtrust_planner` (7 findings) | `0xd30d41f474522329945e5927ba1e28c0ce376fba80942b1e80b7cdc3c74f7cac` | `/demo/cbom-planner.json` |
| `/workspace/projects/backend/src` (0 findings, clean) | `0xbc5464cb3f08b7984fcf6392a0ab12f01759ca3a4f654f6b070a2e3d2f7eddd7` | `/demo/cbom-backend.json` |

Migration record: `0xec0e55de99ddcb18b9a394be9f704c703e7d5ade53b29e16c4fc0a60264d3984`
(tx `0x014e6d93c8ded0e535ebecf11985736f867ea0708a949983c5b3ad16a794fe8e`).

### Verification

```
powershell -File deploy/smoke-test.ps1 -RepoRoot <repo>   # API + planner + scanner + frontend
node frontend/scripts/browser-check.mjs                   # live anonymous browser flows
npm test --prefix backend                                  # 108 tests
npm test --prefix frontend                                 # 138 tests
```

The browser check covers: home loads and links to real records, `/v/<id>`
renders VALID/REVOKED, `/scanner` runs a full scan and reaches the AI planner
and GPU lab panels, and `/dashboard` / `/vendors` load without server errors.

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
  required") — including free web services and free databases.
- **Hugging Face Docker Spaces:** creation returns HTTP 402 — free Docker
  Spaces require a PRO subscription.

The Vercel serverless deployment is the no-card path that works today.

## Known limitations

- **The local machine must stay on** for the indexer, Python scanner, evidence
  chain, ML bridge, and planner. If it goes offline, the hosted API keeps
  serving RPC-backed reads and the last indexed data; `/v1/scan/*`,
  `/v1/evidence/*`, `/v1/gpu/*` return a proxy error and `/v1/plans` fails.
  `deploy/ensure-local-stack.ps1` restarts the pieces after a reboot and
  re-points Vercel when tunnel URLs change.
- **Quick-tunnel URLs are not stable.** The watchdog updates `.env` and
  redeploys the backend when they change; otherwise run
  `deploy/vercel-backend.ps1` after editing the two tunnel variables.
- **Serverless cold starts.** The first request after idle takes ~1–2 s while
  the Fastify app boots; `/tmp/qtrust` on Vercel is ephemeral (evidence is
  proxied to the local API, which keeps the durable chain).
- **In-memory rate limiting on Vercel** (120 req/min per warm instance,
  `QTRUST_RATE_LIMIT_MAX`). No Redis-backed shared limits there.
- **Webhook subscribers on Vercel** are held in memory per warm instance and
  are lost on cold start. The local API uses Redis and is authoritative for
  long-lived subscriptions.
- **WalletConnect uses the public `demo` project ID** with
  `NEXT_PUBLIC_QTRUST_ALLOW_DEMO_WALLETCONNECT=1`. Browser-extension wallets
  work normally; WalletConnect pairing is rate-limited by the demo project.
  Create a project at https://cloud.walletconnect.com, set
  `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID`, and redeploy.
- **No custom domain.** The Vercel URLs are the production entry points.
- **Shared secrets were rotated** after an accidental env dump in the local
  session log: API key, planner key, webhook encryption key, and VC issuer key.
  The Base Sepolia relayer/deployer keys were also visible in that log; they
  are testnet-only and the relayer cannot be rotated because
  `DEFAULT_ADMIN_ROLE` was renounced.
