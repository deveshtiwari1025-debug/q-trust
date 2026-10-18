# 7. Identity, tenancy and RBAC for the control plane

## Status

Proposed — 2026-10-18 (design agreed; implementation tracked as EN-01..EN-03 in
`docs/BEST_IN_CLASS_ROADMAP.md`).

## Context

The backend currently authenticates every privileged route with a single global
list of API keys (`backend/src/middleware/auth.ts`). It has no organization or
tenant model, no roles, no SSO, and no immutable audit trail. That is enough for
a single-operator demo and not enough for any enterprise security review:

* one key grants every write across every organization;
* a leaked key cannot be scoped, expired, or attributed to a person;
* there is no way to answer “who changed this asset and when?”;
* wallet-gated pages (`/dashboard`, `/vendors`) exclude non-crypto users.

The on-chain contracts already separate `orgDid` and role-gated writes, so the
control plane must catch up without changing the evidence layer.

## Decision

1. **Identity.** Enterprise deployments integrate an OIDC or SAML 2.0 IdP;
   local deployments keep API keys. Add TOTP/passkeys for local accounts.
   SCIM 2.0 provisions users and groups. Wallet connection becomes an optional
   signing method, never the primary login.
2. **Hierarchy.** `organization → workspace → project`. Every stored row that
   belongs to a customer carries `org_id`; `workspace_id`/`project_id` narrow
   queries. On-chain `orgDid` maps to `organization.did`.
3. **Roles.** `owner`, `admin`, `analyst`, `auditor`, `viewer`, plus scoped
   service accounts. Writes require `admin`/`analyst`; evidence export and
   audit-log read require `auditor`; billing and SSO config require `owner`.
   Roles are evaluated server-side on every request; the UI only hides
   controls.
4. **API keys.** Store only a SHA-256 hash and a prefix for display. Keys carry
   scopes, an expiry, and an optional IP allowlist; rotation invalidates the old
   key immediately. Audit entries record `key:<hash-prefix>`, never the key.
5. **Tenant isolation.** Postgres row-level security on every tenant table,
   with `SET LOCAL app.org_id` per transaction. Per-tenant envelope encryption
   (KMS) for webhook secrets and stored evidence. No cross-tenant joins.
6. **Audit log.** Append-only hash-chained table (`audit_log`, EN-02), written
   on every mutating request, with redacted bodies, actor, org, IP, request id
   and status. A trigger rejects UPDATE/DELETE. Export to SIEM is a follow-up.
7. **Break-glass.** A time-boxed, heavily audited operator role may bypass SSO
   for incident response; it is disabled by default and requires two-person
   approval.

## Consequences

* The API surface stays backward compatible: API keys remain valid, but new
  keys are scoped and hashed; existing deployments must rotate.
* Every tenant table needs `org_id` and an RLS policy before the first
  multi-tenant release. The indexer writes `org_did` today; the migration maps
  it to `organizations.did`.
* Wallet-only flows remain for public verification (`/v/[id]`) but are removed
  from enterprise onboarding.
* Tests must include cross-tenant denial, role denial, key expiry/rotation,
  audit-chain tamper detection, and SIEM export.

## Alternatives considered

* **Per-customer deployments only.** Simpler isolation, but rules out the
  hosted control plane and shared benchmark telemetry.
* **OAuth scopes without roles.** Scopes describe tokens, not people; auditors
  need role-based read access independent of a token.
* **On-chain roles as the only authorization source.** Wrong layer: on-chain
  roles govern attestations, not dashboard access, and cannot express
  workspace-level permissions without leaking customer structure.
