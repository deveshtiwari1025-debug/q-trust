import { describe, expect, it } from "vitest";
import fastify from "fastify";
import {
  AuditLog,
  GENESIS_HASH,
  MemoryAuditSink,
  canonicalJson,
  redact,
  registerAuditLog,
  verifyAuditChain,
} from "../src/services/audit-log.js";

describe("audit log redaction and canonicalisation", () => {
  it("redacts secrets at any depth while keeping useful fields", () => {
    const result = redact({
      password: "p",
      nested: { apiKey: "k", keep: "v" },
      list: [1, "x", { secret: "s" }],
    });
    expect(result).toEqual({
      password: "[redacted]",
      nested: { apiKey: "[redacted]", keep: "v" },
      list: [1, "x", { secret: "[redacted]" }],
    });
  });

  it("canonical JSON is independent of key order", () => {
    expect(canonicalJson({ b: 1, a: { d: 2, c: 3 } })).toBe(
      canonicalJson({ a: { c: 3, d: 2 }, b: 1 }),
    );
  });
});

describe("AuditLog hash chain", () => {
  it("starts at genesis and verifies a clean chain", async () => {
    const sink = new MemoryAuditSink();
    const log = new AuditLog(sink);
    const first = await log.append({
      action: "POST /v1/write/assets",
      method: "POST",
      path: "/v1/write/assets",
      statusCode: 201,
      after: { cbomHash: "0xabc" },
    });
    await log.append({
      action: "POST /v1/write/assets",
      method: "POST",
      path: "/v1/write/assets",
      statusCode: 201,
    });

    expect(first.prevHash).toBe(GENESIS_HASH);
    expect(verifyAuditChain(sink.list())).toEqual({ valid: true, brokenAt: null });
  });

  it("detects tampering with a stored entry", async () => {
    const sink = new MemoryAuditSink();
    const log = new AuditLog(sink);
    await log.append({ action: "POST /a", method: "POST", path: "/a", statusCode: 200 });
    await log.append({ action: "POST /b", method: "POST", path: "/b", statusCode: 200 });

    const tampered = sink.list();
    tampered[1] = { ...tampered[1], statusCode: 500 };
    expect(verifyAuditChain(tampered)).toEqual({ valid: false, brokenAt: 1 });
  });

  it("serialises concurrent appends without forking the chain", async () => {
    const sink = new MemoryAuditSink();
    const log = new AuditLog(sink);
    await Promise.all(
      Array.from({ length: 10 }, (_, index) =>
        log.append({
          action: `POST /item/${index}`,
          method: "POST",
          path: `/item/${index}`,
          statusCode: 201,
        }),
      ),
    );
    const entries = sink.list();
    expect(entries).toHaveLength(10);
    expect(new Set(entries.map((entry) => entry.entryId)).size).toBe(10);
    expect(verifyAuditChain(entries)).toEqual({ valid: true, brokenAt: null });
  });
});

describe("registerAuditLog hook", () => {
  it("records mutating requests, hashes the API key and skips reads", async () => {
    const app = fastify();
    const sink = new MemoryAuditSink();
    registerAuditLog(app, { log: new AuditLog(sink) });
    app.post("/v1/write/assets", async () => ({ ok: true }));
    app.get("/health", async () => ({ ok: true }));
    await app.ready();

    await app.inject({
      method: "POST",
      url: "/v1/write/assets?trace=1",
      headers: { "x-api-key": "caller-key" },
      payload: { orgId: "org-1", apiKey: "super-secret", cbomHash: "0xabc" },
    });
    await app.inject({ method: "GET", url: "/health" });
    await app.close();

    const entries = sink.list();
    expect(entries).toHaveLength(1);
    const entry = entries[0];
    expect(entry.orgId).toBe("org-1");
    expect(entry.path).toBe("/v1/write/assets");
    expect(entry.statusCode).toBe(200);
    expect(entry.actor).toMatch(/^key:[0-9a-f]{16}$/);
    expect(entry.actor).not.toContain("caller-key");
    expect(JSON.stringify(entry.after)).not.toContain("super-secret");
    expect(JSON.stringify(entry.after)).toContain("[redacted]");
    expect(verifyAuditChain(entries)).toEqual({ valid: true, brokenAt: null });
  });
});
