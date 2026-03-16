/**
 * Nucleus Telemetry Drain: Upstash Redis → Local OTel Collector
 *
 * Architecture docs:
 *   - TELEMETRY_PIPELINE_README.md  (end-to-end flow)
 *   - CLOUD_TELEMETRY_QUICKSTART.md (cloud-side encoding contract)
 *   - WINDSURF_SUPER_PROMPT.md      (mission charter, Phase A)
 *
 * Encoding contract:
 *   - Worker (worker-telemetry.js) encodes OTLP binary as base64 via btoa()
 *   - This script decodes with Buffer.from(val, 'base64')
 *   - Forwards raw binary to local collector on localhost:4318/v1/traces (HTTP OTLP)
 *
 * Env vars:
 *   - UPSTASH_REDIS_URL          — Redis TCP URL (rediss://...)
 *   - UPSTASH_REDIS_TOKEN        — Redis password
 *   - NUCLEUS_DRAIN_BATCH_SIZE   — Spans per batch (default: 50)
 *   - NUCLEUS_DRAIN_INTERVAL_MS  — Loop interval ms (default: 1000)
 *   - NUCLEUS_COLLECTOR_URL      — OTLP HTTP endpoint (default: http://localhost:4318/v1/traces)
 */

import fetch from "node-fetch";
import Redis from "ioredis";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

// Load env vars from parent .env file manually
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, "..", "..");
const envPath = join(projectRoot, ".env");

try {
  const envFile = readFileSync(envPath, "utf8");
  envFile.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) return;
    const match = trimmed.match(/^([^=]+)=(.*)$/);
    if (match) {
      const key = match[1].trim();
      let value = match[2].trim();
      // Remove quotes if present
      if ((value.startsWith('"') && value.endsWith('"')) || 
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      process.env[key] = value;
    }
  });
} catch (err) {
  // .env file not found, continue with existing env vars
}

const {
  UPSTASH_REDIS_URL,
  UPSTASH_REDIS_TOKEN,
  NUCLEUS_DRAIN_BATCH_SIZE = "50",
  NUCLEUS_DRAIN_INTERVAL_MS = "1000",
  NUCLEUS_COLLECTOR_URL = "http://localhost:4318/v1/traces",
} = process.env;

if (!UPSTASH_REDIS_URL || !UPSTASH_REDIS_TOKEN) {
  console.error("[drain] ❌ Missing UPSTASH_REDIS_URL or UPSTASH_REDIS_TOKEN env vars");
  process.exit(1);
}

const redis = new Redis(UPSTASH_REDIS_URL, {
  password: UPSTASH_REDIS_TOKEN,
  lazyConnect: false,
  tls: UPSTASH_REDIS_URL.startsWith("rediss://") ? {} : undefined,
});

const BATCH_SIZE = parseInt(NUCLEUS_DRAIN_BATCH_SIZE, 10) || 50;
const INTERVAL_MS = parseInt(NUCLEUS_DRAIN_INTERVAL_MS, 10) || 1000;
const QUEUE_KEY = "nucleus:spans";

// Counters for structured logging
let totalDrained = 0;
let totalErrors = 0;
let totalRetries = 0;

function ts() {
  return new Date().toISOString();
}

async function drainOnce() {
  const rawEntries = [];

  for (let i = 0; i < BATCH_SIZE; i++) {
    // LPOP returns string from Upstash (base64-encoded by Worker)
    const val = await redis.lpop(QUEUE_KEY);
    if (!val) break;
    rawEntries.push(val);
  }

  if (rawEntries.length === 0) return 0;

  let forwarded = 0;

  for (const entry of rawEntries) {
    try {
      // Decode base64 → binary (matches Worker's btoa() encoding)
      const binarySpan = Buffer.from(entry, "base64");

      // Auto-detect content type: JSON starts with '{', protobuf is binary
      let contentType = "application/x-protobuf";
      try {
        const text = binarySpan.toString("utf8");
        if (text.trim().startsWith("{")) {
          contentType = "application/json";
        }
      } catch {
        // Binary data, use protobuf
      }

      const res = await fetch(NUCLEUS_COLLECTOR_URL, {
        method: "POST",
        body: binarySpan,
        headers: {
          "Content-Type": contentType,
        },
      });

      if (!res.ok) {
        console.error(`[drain] ${ts()} ⚠️  Collector rejected span: HTTP ${res.status}`);
        totalErrors++;
        // Push back for retry
        await redis.rpush(QUEUE_KEY, entry);
        totalRetries++;
      } else {
        forwarded++;
        totalDrained++;
      }
    } catch (err) {
      console.error(`[drain] ${ts()} ❌ Error forwarding span: ${err.message || err}`);
      totalErrors++;
      await redis.rpush(QUEUE_KEY, entry);
      totalRetries++;
    }
  }

  if (forwarded > 0) {
    console.log(`[drain] ${ts()} ✅ Forwarded ${forwarded} spans (total: ${totalDrained}, errors: ${totalErrors}, retries: ${totalRetries})`);
  }

  return forwarded;
}

let running = true;

// Graceful shutdown
process.on("SIGINT", () => {
  console.log(`\n[drain] ${ts()} 🛑 Shutting down. Total drained: ${totalDrained}, errors: ${totalErrors}`);
  running = false;
  redis.disconnect();
  process.exit(0);
});

process.on("SIGTERM", () => {
  running = false;
  redis.disconnect();
  process.exit(0);
});

async function main() {
  console.log(`[drain] ${ts()} Starting Upstash → OTLP drain loop...`);
  console.log(`[drain]   Queue key:    ${QUEUE_KEY}`);
  console.log(`[drain]   Collector:    ${NUCLEUS_COLLECTOR_URL}`);
  console.log(`[drain]   Batch size:   ${BATCH_SIZE}`);
  console.log(`[drain]   Interval:     ${INTERVAL_MS}ms`);

  // Check if we should run once or loop
  const runOnce = process.env.NUCLEUS_DRAIN_ONCE === "true";

  do {
    try {
      const forwarded = await drainOnce();
      if (forwarded > 0) {
        console.log(
          `[drain] ${ts()} ✅ Forwarded ${forwarded} spans (total: ${totalDrained}, errors: ${totalErrors}, retries: ${totalRetries})`
        );
      } else if (runOnce) {
        console.log(`[drain] ${ts()} ℹ️  No spans in queue`);
      }
    } catch (err) {
      console.error(`[drain] ${ts()} ❌ Drain error: ${err.message || err}`);
      totalErrors++;
    }

    if (!runOnce) {
      // Sleep between batches
      await new Promise((resolve) => setTimeout(resolve, INTERVAL_MS));
    }
  } while (!runOnce);

  console.log(`[drain] ${ts()} 🛑 Shutting down. Total drained: ${totalDrained}, errors: ${totalErrors}`);
  process.exit(0);
}

main().catch((err) => {
  console.error(`[drain] ${ts()} 💀 Fatal error: ${err.message || err}`);
  process.exit(1);
});
