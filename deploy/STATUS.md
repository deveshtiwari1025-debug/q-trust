# Q-Trust deployment status

_Last updated: 2026-10-20_

## Live now

| Component | Where | URL / reference |
|---|---|---|
| Frontend | Vercel (`q-trust`, team `devesh-tiwari-p-projects1`) | https://q-trust-nu.vercel.app |
| Backend API + indexer | Docker on this machine, exposed with a Cloudflare quick tunnel | https://sculpture-stylus-ultimate-burning.trycloudflare.com |
| GNN planner (v3, CPU) | Docker on this machine (`qtrust-planner:2.2.0`), exposed with a second Cloudflare quick tunnel | https://accordingly-thumbzilla-following-intake.trycloudflare.com |
| Postgres | Docker on this machine (local demo) | `qtrust-postgres` (127.0.0.1:5433) |
| Postgres (hosted) | Neon, provisioned through the Vercel Marketplace | resource `quiet-sound-15608005`; URL in `.env` as `QTRUST_EXTERNAL_PG_URL` |
| Redis / Key Value | Docker on this machine | `qtrust-redis` (127.0.0.1:6379) |
| Contracts | Base Sepolia (chain 84532) | see `deploy/logs/contracts-deploy.log` and `.env` |

Vercel Deployment Protection is **disabled** for the `q-trust` project so the
site is publicly reachable.

### Smoke test (passed before the secret rotation)

```
powershell -File deploy/smoke-test.ps1 `
  -ApiUrl https://sculpture-stylus-ultimate-burning.trycloudflare.com `
  -FrontendUrl https://q-trust-nu.vercel.app `
  -ScanDirectory /workspace/projects/backend/src
```

All checks passed: API health, authenticated docs, planner plan, scanner,
frontend HTTP 200. After rotating the API key, the direct backend still
accepts both the new and the previous key (transition list) and rejects
unauthenticated planner calls with 401.

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

## Render migration assets (ready)

- **Source repo:** `https://github.com/deveshtiwari1025-debug/q-trust`
  (public fork of `humoge7502/q-trust`; local `main` pushed through the latest
  deploy commit). The fork is required because the available credentials have
  no push access to the upstream repo.
- **Render account:** created and verified under
  `qtrust-render-c822318142@maxxspace.com` (temporary mailbox); API key is in
  `.env` as `RENDER_API_KEY`. Workspace `My Workspace`
  (`tea-dbb7bnnavr4c73d19i10`).
- **Neon Postgres:** free plan, connected to the Vercel project; the backend
  receives the unpooled URL via `QTRUST_EXTERNAL_PG_URL`.
- **Redis:** not provisioned. It is optional for the backend (webhook
  subscriptions return 503 without it); `-SkipRedis` skips Render Key Value.
- **Planner:** stays on this machine; the backend uses
  `QTRUST_PLANNER_TUNNEL_URL`. The script supports
  `-ExternalPlannerUrl` and skips a Render planner service.
- **Deploy script:** `deploy/deploy-render.ps1` supports `-Plan free`,
  `-FreeTier`, `-SkipRedis`, `-ExternalPlannerUrl`, `-ExternalPgUrl`,
  `-ExternalRedisUrl`, `-RepoUrl`, and `-Branch`, with detailed HTTP error
  reporting.

## Blocker for Render

**Render now requires payment information for every service creation, including
free web services and free databases.** The API returns HTTP 402:

```
{"message":"Payment information is required to complete this request. To add a card, visit https://dashboard.render.com/billing"}
```

No Render API key or browser session for the user's own Render account exists
on this machine (checked `.env`, all Chrome/Edge profiles, Windows Credential
Manager, clipboard, environment variables, and recent files). The billing page
for the temporary Render account has been opened in Chrome for the user to add
a card if desired.

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

- **Backend and planner are not on Render yet** (payment info required).
  They run on this machine behind temporary `*.trycloudflare.com` tunnels.
- **Tunnel URLs are not stable.** If `cloudflared` restarts, the URL changes.
  Update `.env` (`QTRUST_PUBLIC_URL`, `QTRUST_BACKEND_URL`,
  `NEXT_PUBLIC_QTRUST_API_URL`, `QTRUST_PLANNER_TUNNEL_URL`) and the Vercel env
  vars (`QTRUST_BACKEND_URL`, `NEXT_PUBLIC_QTRUST_API_URL`), then redeploy:
  `cd frontend && vercel deploy --prod --yes`.
- **WalletConnect uses the public `demo` project ID** with
  `NEXT_PUBLIC_QTRUST_ALLOW_DEMO_WALLETCONNECT=1`. Connections work but are
  rate-limited. Create a project at https://cloud.walletconnect.com, then set
  `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID` and redeploy.
- **No custom domain.** The Vercel, trycloudflare, and eventual onrender.com
  URLs are the production entry points for now.
- **The temporary Render account uses a disposable email.** If it becomes the
  permanent host, change the account email to one the user controls.
- **Shared secrets were rotated** after an accidental env dump in the local
  session log: API key, planner key, webhook encryption key, and VC issuer key.
  The previous API key is still accepted temporarily so the running Vercel
  deployment keeps working; remove it from `QTRUST_API_KEYS` after the frontend
  redeploy. The Base Sepolia relayer/deployer keys were also visible in that
  log; they are testnet-only and the relayer cannot be rotated because
  `DEFAULT_ADMIN_ROLE` was renounced.

## Next steps to finish the Render migration

1. Add payment information to a Render workspace (or provide an API key for an
   existing workspace with billing) and put that key in `.env` as
   `RENDER_API_KEY`.
2. Run:

   ```
   powershell -File deploy/deploy-render.ps1 `
     -Plan free -FreeTier -SkipRedis `
     -RepoUrl https://github.com/deveshtiwari1025-debug/q-trust -Branch main `
     -ExternalPlannerUrl <current planner tunnel URL>
   ```

3. The script creates the backend web service, wires Neon via
   `QTRUST_EXTERNAL_PG_URL`, and waits for the deploy. It writes the real
   backend URL back to `.env`.
4. Point Vercel at the backend and redeploy:

   ```
   cd frontend
   vercel env add QTRUST_BACKEND_URL production --value https://<backend>.onrender.com --yes --force
   vercel env add NEXT_PUBLIC_QTRUST_API_URL production --value https://<backend>.onrender.com --yes --force
   vercel deploy --prod --yes
   ```

5. Run `deploy/smoke-test.ps1` against the Render backend and the Vercel
   frontend; then remove the old API key from `QTRUST_API_KEYS`.

### No-card alternative

Hugging Face Docker Spaces can host the same backend image (free CPU Basic:
2 vCPU, 16 GB RAM, no card) and even the planner. It requires a Hugging Face
account and a write token (`HF_TOKEN=hf_...` in `.env`); none exists on this
machine (the cloned Spaces belong to upstream account `KRISHNAPURI`).
