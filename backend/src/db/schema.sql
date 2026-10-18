-- Q-Trust indexer schema (Postgres).
-- The blockchain remains the source of truth; this is a read model for fast,
-- paginated, filtered API responses.

CREATE TABLE IF NOT EXISTS assets (
    asset_id      TEXT PRIMARY KEY,
    org_did       TEXT NOT NULL,
    cbom_hash     TEXT NOT NULL,
    metadata_uri  TEXT NOT NULL DEFAULT '',
    timestamp     BIGINT NOT NULL,
    last_updated  BIGINT NOT NULL,
    active        BOOLEAN NOT NULL DEFAULT TRUE,
    tx_hash       TEXT NOT NULL DEFAULT '',
    block_number  BIGINT NOT NULL DEFAULT 0,
    first_seen    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_assets_org ON assets (org_did);

CREATE TABLE IF NOT EXISTS attestations (
    attestation_id TEXT PRIMARY KEY,
    vendor_did     TEXT NOT NULL,
    product_id     TEXT NOT NULL,
    version        TEXT NOT NULL,
    algorithm      TEXT NOT NULL,
    supported      BOOLEAN NOT NULL,
    evidence_uri   TEXT NOT NULL DEFAULT '',
    timestamp      BIGINT NOT NULL,
    revoked        BOOLEAN NOT NULL DEFAULT FALSE,
    tx_hash        TEXT NOT NULL DEFAULT '',
    block_number   BIGINT NOT NULL DEFAULT 0,
    first_seen     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_att_vendor ON attestations (vendor_did);
CREATE INDEX IF NOT EXISTS idx_att_product ON attestations (product_id, version, algorithm);

CREATE TABLE IF NOT EXISTS migrations (
    migration_id   TEXT PRIMARY KEY,
    asset_id       TEXT NOT NULL,
    org_did        TEXT NOT NULL,
    from_algorithm TEXT NOT NULL,
    to_algorithm   TEXT NOT NULL,
    evidence_hash  TEXT NOT NULL,
    evidence_uri   TEXT NOT NULL DEFAULT '',
    timestamp      BIGINT NOT NULL,
    verified       BOOLEAN NOT NULL DEFAULT FALSE,
    tx_hash        TEXT NOT NULL DEFAULT '',
    block_number   BIGINT NOT NULL DEFAULT 0,
    first_seen     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mig_org ON migrations (org_did);
CREATE INDEX IF NOT EXISTS idx_mig_asset ON migrations (asset_id);

CREATE TABLE IF NOT EXISTS audits (
    audit_id        TEXT PRIMARY KEY,
    org_did         TEXT NOT NULL,
    auditor_did     TEXT NOT NULL,
    result          INTEGER NOT NULL,
    assets_reviewed BIGINT NOT NULL,
    assets_migrated BIGINT NOT NULL,
    report_hash     TEXT NOT NULL,
    report_uri      TEXT NOT NULL DEFAULT '',
    timestamp       BIGINT NOT NULL,
    tx_hash         TEXT NOT NULL DEFAULT '',
    block_number    BIGINT NOT NULL DEFAULT 0,
    first_seen      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_org ON audits (org_did);

-- Chain cursor: last block processed per contract/event.
CREATE TABLE IF NOT EXISTS indexer_state (
    key        TEXT PRIMARY KEY,
    block      BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Reorg support: block_hash may be added to existing deployments.
ALTER TABLE indexer_state ADD COLUMN IF NOT EXISTS block_hash TEXT NOT NULL DEFAULT '';

-- Blocks whose events have been indexed (block hash recorded so a later
-- poll can detect chain reorganizations by comparing canonical hashes).
CREATE TABLE IF NOT EXISTS processed_blocks (
    block_number BIGINT PRIMARY KEY,
    block_hash   TEXT NOT NULL,
    first_seen   TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- Append-only, hash-chained audit log for operator actions (EN-02).
-- The application computes each row's hash over the canonical entry plus the
-- previous row's hash, so deleting or editing history is detectable. The
-- trigger below makes the table physically append-only as well.
CREATE TABLE IF NOT EXISTS audit_log (
    id           BIGSERIAL PRIMARY KEY,
    entry_id     TEXT NOT NULL UNIQUE,
    org_id       TEXT NOT NULL DEFAULT '',
    actor        TEXT NOT NULL DEFAULT '',
    action       TEXT NOT NULL,
    resource     TEXT NOT NULL DEFAULT '',
    method       TEXT NOT NULL,
    path         TEXT NOT NULL,
    status_code  INTEGER NOT NULL,
    ip           TEXT NOT NULL DEFAULT '',
    request_id   TEXT NOT NULL DEFAULT '',
    before       JSONB,
    after        JSONB,
    prev_hash    TEXT NOT NULL,
    hash         TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_org_time ON audit_log (org_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action_time ON audit_log (action, created_at DESC);

CREATE OR REPLACE FUNCTION audit_log_immutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only (% rejected)', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_log_no_mutation ON audit_log;
CREATE TRIGGER audit_log_no_mutation
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();

CREATE INDEX IF NOT EXISTS idx_processed_blocks_number ON processed_blocks (block_number DESC);