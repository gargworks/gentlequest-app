#!/usr/bin/env node
/**
 * Nucleus Telemetry Config Validator
 *
 * Architecture docs:
 *   - WINDSURF_SUPER_PROMPT.md (Phase D1)
 *   - TELEMETRY_PIPELINE_README.md
 *
 * Usage:
 *   npm run telemetry:audit
 *   node scripts/telemetry-validate.mjs
 *
 * Checks:
 *   1. Upstash env vars present
 *   2. Collector container running + reachable
 *   3. Docker available
 *   4. Queue key naming consistency
 *   5. Tunnel hostname resolution
 */

import { execSync } from "child_process";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const CHECKS = [];
let exitCode = 0;

function check(name, fn) {
  try {
    const result = fn();
    CHECKS.push({ name, status: "PASS", detail: result || "" });
  } catch (err) {
    CHECKS.push({ name, status: "FAIL", detail: err.message || String(err) });
    exitCode = 1;
  }
}

function warn(name, fn) {
  try {
    const result = fn();
    CHECKS.push({ name, status: "PASS", detail: result || "" });
  } catch (err) {
    CHECKS.push({ name, status: "WARN", detail: err.message || String(err) });
  }
}

// ── Check 1: Docker available ──
check("Docker available", () => {
  execSync("docker version", { stdio: "pipe" });
  return "Docker CLI reachable";
});

// ── Check 2: Collector container running ──
check("OTel Collector running", () => {
  const out = execSync("docker ps --format '{{.Names}}'", { stdio: "pipe", encoding: "utf-8" });
  if (!out.includes("nucleus-otel-collector")) {
    throw new Error("Container 'nucleus-otel-collector' not in 'docker ps'. Start with: npm run telemetry:up");
  }
  return "nucleus-otel-collector is running";
});

// ── Check 3: Collector ports reachable ──
warn("Collector port 4318 (HTTP OTLP)", () => {
  try {
    execSync("curl -sf -o /dev/null -w '%{http_code}' http://localhost:4318/v1/traces 2>/dev/null", {
      stdio: "pipe",
      encoding: "utf-8",
      timeout: 3000,
    });
  } catch {
    throw new Error("localhost:4318 not reachable. Collector may not be exposing HTTP OTLP.");
  }
  return "Reachable";
});

warn("Collector port 4317 (gRPC OTLP)", () => {
  try {
    execSync("curl -sf -o /dev/null http://localhost:4317 2>/dev/null", {
      stdio: "pipe",
      encoding: "utf-8",
      timeout: 3000,
    });
  } catch {
    throw new Error("localhost:4317 not reachable (gRPC — may require special client).");
  }
  return "Reachable (or gRPC endpoint)";
});

// ── Check 4: Upstash env vars ──
check("UPSTASH_REDIS_URL set", () => {
  if (!process.env.UPSTASH_REDIS_URL) {
    throw new Error("Missing UPSTASH_REDIS_URL. Set it in your shell or .env file.");
  }
  const url = process.env.UPSTASH_REDIS_URL;
  if (!url.startsWith("rediss://") && !url.startsWith("redis://")) {
    throw new Error(`UPSTASH_REDIS_URL should start with redis:// or rediss://. Got: ${url.substring(0, 20)}...`);
  }
  return `Set (${url.substring(0, 30)}...)`;
});

check("UPSTASH_REDIS_TOKEN set", () => {
  if (!process.env.UPSTASH_REDIS_TOKEN) {
    throw new Error("Missing UPSTASH_REDIS_TOKEN. Set it in your shell or .env file.");
  }
  return `Set (...${process.env.UPSTASH_REDIS_TOKEN.slice(-6)})`;
});

// ── Check 5: Queue key consistency ──
warn("Queue key consistency", () => {
  // Read Worker source and drain script, verify both use "nucleus:spans"
  const workerPath = join(__dirname, "..", "cloudflare", "worker-telemetry.js");
  const drainPath = join(__dirname, "drain-upstash-spans.js");

  let issues = [];
  try {
    const worker = readFileSync(workerPath, "utf-8");
    if (!worker.includes("nucleus:spans")) {
      issues.push("Worker does not reference 'nucleus:spans'");
    }
  } catch {
    issues.push("Could not read Worker source");
  }

  try {
    const drain = readFileSync(drainPath, "utf-8");
    if (!drain.includes("nucleus:spans")) {
      issues.push("Drain script does not reference 'nucleus:spans'");
    }
  } catch {
    issues.push("Could not read drain script");
  }

  if (issues.length > 0) {
    throw new Error(issues.join("; "));
  }
  return "Both Worker and drain use 'nucleus:spans'";
});

// ── Check 6: Tunnel hostname ──
warn("telemetry.nucleusos.dev DNS", () => {
  try {
    const out = execSync("dig +short telemetry.nucleusos.dev 2>/dev/null", {
      stdio: "pipe",
      encoding: "utf-8",
      timeout: 5000,
    });
    if (!out.trim()) {
      throw new Error("No DNS record found for telemetry.nucleusos.dev");
    }
    return `Resolves to: ${out.trim()}`;
  } catch (err) {
    throw new Error(`DNS lookup failed: ${err.message}`);
  }
});

// ── Check 7: Cloudflared installed ──
warn("cloudflared installed", () => {
  try {
    const out = execSync("cloudflared version 2>/dev/null", { stdio: "pipe", encoding: "utf-8" });
    return out.trim().split("\n")[0];
  } catch {
    throw new Error("cloudflared not found in PATH. Install from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/");
  }
});

// ── Output ──
const isJson = process.argv.includes("--json");

if (isJson) {
  console.log(JSON.stringify({ checks: CHECKS, overall: exitCode === 0 ? "PASS" : "FAIL" }, null, 2));
} else {
  console.log("");
  console.log("  ┌──────────────────────────────────────────────────────┐");
  console.log("  │        Nucleus Telemetry Audit                      │");
  console.log("  └──────────────────────────────────────────────────────┘");
  console.log("");

  for (const c of CHECKS) {
    const icon = c.status === "PASS" ? "✅" : c.status === "WARN" ? "⚠️ " : "❌";
    console.log(`  ${icon} ${c.name}`);
    if (c.status !== "PASS") {
      console.log(`     ${c.detail}`);
    }
  }

  const passed = CHECKS.filter((c) => c.status === "PASS").length;
  const failed = CHECKS.filter((c) => c.status === "FAIL").length;
  const warned = CHECKS.filter((c) => c.status === "WARN").length;

  console.log("");
  console.log(`  Result: ${passed} passed, ${warned} warnings, ${failed} failed`);

  if (exitCode !== 0) {
    console.log("  ❌ Some critical checks failed. Fix them before telemetry will work.");
  } else if (warned > 0) {
    console.log("  ⚠️  All critical checks passed, but some optional checks have warnings.");
  } else {
    console.log("  ✅ All checks passed. Telemetry pipeline is healthy.");
  }
  console.log("");
}

process.exit(exitCode);
