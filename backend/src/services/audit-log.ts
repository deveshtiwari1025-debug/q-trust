/**
 * Append-only, hash-chained audit log (EN-02).
 *
 * Every mutating request is recorded with actor, org, action, resource,
 * status, redacted before/after bodies and a request id. Each row's hash
 * covers the canonical entry plus the previous row's hash, so deleting or
 * editing history is detectable. Postgres enforces append-only with a trigger
 * (see db/schema.sql); MemoryAuditSink exists for tests and local dev.
 */
import { createHash, randomUUID } from "node:crypto";
import type { FastifyInstance, FastifyRequest } from "fastify";
import type { Pool } from "pg";

export const GENESIS_HASH = "0".repeat(64);
const MAX_DEPTH = 6;
const MAX_STRING = 1024;
const MAX_ARRAY = 50;

const SENSITIVE_KEY = /(pass(word|phrase)?|secret|token|api[-_]?key|authorization|signature|cookie|private[-_]?key|credential)/i;

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export interface AuditAppendInput {
  orgId?: string;
  actor?: string;
  action: string;
  resource?: string;
  method: string;
  path: string;
  statusCode: number;
  ip?: string;
  requestId?: string;
  before?: unknown;
  after?: unknown;
}

export interface AuditEntry extends AuditAppendInput {
  entryId: string;
  createdAt: string;
  prevHash: string;
  hash: string;
}

export interface AuditSink {
  lastHash(): Promise<string>;
  append(entry: AuditEntry): Promise<void>;
}

/** Deterministic JSON: object keys sorted recursively, undefined → null. */
export function canonicalJson(value: unknown, depth = 0): string {
  if (depth > MAX_DEPTH) return JSON.stringify("[truncated]");
  if (value === null || value === undefined) return "null";
  if (typeof value === "number") return Number.isFinite(value) ? JSON.stringify(value) : "null";
  if (typeof value === "string" || typeof value === "boolean") return JSON.stringify(value);
  if (typeof value === "bigint") return JSON.stringify(value.toString());
  if (Array.isArray(value)) {
    return `[${value.map((item) => canonicalJson(item, depth + 1)).join(",")}]`;
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const keys = Object.keys(record).sort();
    return `{${keys
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(record[key], depth + 1)}`)
      .join(",")}}`;
  }
  return "null";
}

/** Redact secrets and bound the size of attacker-controlled request bodies. */
export function redact(value: unknown, depth = 0): JsonValue {
  if (depth > MAX_DEPTH) return "[truncated]";
  if (value === null || value === undefined) return null;
  if (typeof value === "string") {
    return value.length > MAX_STRING ? `${value.slice(0, MAX_STRING)}…` : value;
  }
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "boolean") return value;
  if (typeof value === "bigint") return value.toString();
  if (Array.isArray(value)) {
    return value.slice(0, MAX_ARRAY).map((item) => redact(item, depth + 1));
  }
  if (typeof value === "object") {
    const out: { [key: string]: JsonValue } = {};
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
      if (key === "__proto__" || key === "constructor" || key === "prototype") continue;
      out[key] = SENSITIVE_KEY.test(key) ? "[redacted]" : redact(item, depth + 1);
    }
    return out;
  }
  return null;
}

function payloadOf(entry: AuditEntry | (AuditAppendInput & { entryId: string; createdAt: string })) {
  return {
    entryId: entry.entryId,
    orgId: entry.orgId ?? "",
    actor: entry.actor ?? "",
    action: entry.action,
    resource: entry.resource ?? "",
    method: entry.method,
    path: entry.path,
    statusCode: entry.statusCode,
    ip: entry.ip ?? "",
    requestId: entry.requestId ?? "",
    before: entry.before ?? null,
    after: entry.after ?? null,
    createdAt: entry.createdAt,
  };
}

export function hashAuditEntry(
  prevHash: string,
  entry: AuditEntry | (AuditAppendInput & { entryId: string; createdAt: string }),
): string {
  return createHash("sha256")
    .update(prevHash)
    .update("\n")
    .update(canonicalJson(payloadOf(entry)))
    .digest("hex");
}

export class MemoryAuditSink implements AuditSink {
  private readonly entries: AuditEntry[] = [];

  async lastHash(): Promise<string> {
    return this.entries.at(-1)?.hash ?? GENESIS_HASH;
  }

  async append(entry: AuditEntry): Promise<void> {
    this.entries.push(entry);
  }

  list(): AuditEntry[] {
    return [...this.entries];
  }
}

export class PostgresAuditSink implements AuditSink {
  constructor(private readonly db: Pick<Pool, "query">) {}

  async lastHash(): Promise<string> {
    const result = await this.db.query("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1");
    const row = result.rows[0] as { hash?: string } | undefined;
    return row?.hash ?? GENESIS_HASH;
  }

  async append(entry: AuditEntry): Promise<void> {
    await this.db.query(
      `INSERT INTO audit_log
         (entry_id, org_id, actor, action, resource, method, path, status_code,
          ip, request_id, before, after, prev_hash, hash, created_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)`,
      [
        entry.entryId,
        entry.orgId ?? "",
        entry.actor ?? "",
        entry.action,
        entry.resource ?? "",
        entry.method,
        entry.path,
        entry.statusCode,
        entry.ip ?? "",
        entry.requestId ?? "",
        entry.before === undefined ? null : JSON.stringify(entry.before),
        entry.after === undefined ? null : JSON.stringify(entry.after),
        entry.prevHash,
        entry.hash,
        entry.createdAt,
      ],
    );
  }
}

export class AuditLog {
  private tail: Promise<void> = Promise.resolve();

  constructor(private readonly sink: AuditSink) {}

  /** Append in strict order; concurrent callers cannot fork the chain. */
  append(input: AuditAppendInput): Promise<AuditEntry> {
    return new Promise<AuditEntry>((resolve, reject) => {
      this.tail = this.tail.then(async () => {
        try {
          const prevHash = await this.sink.lastHash();
          const draft = {
            ...input,
            entryId: randomUUID(),
            createdAt: new Date().toISOString(),
          };
          const entry: AuditEntry = { ...draft, prevHash, hash: hashAuditEntry(prevHash, draft) };
          await this.sink.append(entry);
          resolve(entry);
        } catch (err) {
          reject(err);
        }
      });
    });
  }
}

/** Verify hashes and links; returns the index of the first broken entry. */
export function verifyAuditChain(entries: AuditEntry[]): {
  valid: boolean;
  brokenAt: number | null;
} {
  let prevHash = GENESIS_HASH;
  for (let index = 0; index < entries.length; index += 1) {
    const entry = entries[index];
    if (entry.prevHash !== prevHash) return { valid: false, brokenAt: index };
    if (entry.hash !== hashAuditEntry(prevHash, entry)) return { valid: false, brokenAt: index };
    prevHash = entry.hash;
  }
  return { valid: true, brokenAt: null };
}

export interface AuditLogOptions {
  log: AuditLog;
  disabled?: boolean;
}

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const SKIP_PREFIXES = ["/metrics", "/health", "/docs", "/documentation", "/openapi"];

function actorOf(request: FastifyRequest): string {
  const provided = request.headers["x-api-key"];
  if (typeof provided !== "string" || !provided) return "anonymous";
  return `key:${createHash("sha256").update(provided).digest("hex").slice(0, 16)}`;
}

function orgOf(request: FastifyRequest): string {
  const candidates: unknown[] = [];
  const body = request.body;
  if (body && typeof body === "object") {
    const record = body as Record<string, unknown>;
    candidates.push(record.orgId, record.org_id, record.orgDid, record.org_did, record.subject_did);
  }
  const params = request.params;
  if (params && typeof params === "object") {
    const record = params as Record<string, unknown>;
    candidates.push(record.orgId, record.org_id, record.orgDid, record.org_did);
  }
  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim()) return candidate.trim();
  }
  return "";
}

/**
 * Record every mutating request. Registered at the root so all route plugins
 * inherit it. Failures are logged but never affect the already-sent response.
 */
export function registerAuditLog(app: FastifyInstance, options: AuditLogOptions): void {
  if (options.disabled) return;

  app.addHook("onResponse", async (request, reply) => {
    const method = request.method.toUpperCase();
    if (!MUTATING_METHODS.has(method)) return;

    const path = request.url.split("?")[0];
    if (SKIP_PREFIXES.some((prefix) => path === prefix || path.startsWith(`${prefix}/`))) return;

    const route = request.routeOptions?.url ?? path;
    const body = request.body;
    const after = method === "DELETE" ? null : redact(body);

    try {
      await options.log.append({
        orgId: orgOf(request),
        actor: actorOf(request),
        action: `${method} ${route}`,
        resource: route,
        method,
        path,
        statusCode: reply.statusCode,
        ip: request.ip,
        requestId: request.id,
        before: null,
        after,
      });
    } catch (err) {
      request.log.warn({ err }, "audit log append failed; response already sent");
    }
  });
}
