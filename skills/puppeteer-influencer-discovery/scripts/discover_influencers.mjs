#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((pairs, value, index, values) => {
    if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
    return pairs;
  }, [])
);

const query = args.query?.trim();
const output = args.output?.trim();
const limit = Number.parseInt(args.limit ?? "25", 10);
const minFollowers = Number.parseInt(args["min-followers"] ?? "0", 10);
const maxFollowers = Number.parseInt(args["max-followers"] ?? "999999999", 10);

if (!query || !output || !Number.isInteger(limit) || limit < 1 || minFollowers > maxFollowers) {
  console.error("Usage: node discover_influencers.mjs --query <text> --min-followers <n> --max-followers <n> --limit <n> --output <csv>");
  process.exit(1);
}

let puppeteer;
try {
  ({ default: puppeteer } = await import("puppeteer"));
} catch {
  console.error("Puppeteer is required. Run: npm --prefix frontend install --save-dev puppeteer");
  process.exit(1);
}

const normalize = (value = "") => value.toLowerCase().replace(/[^a-z0-9]/g, "");
const csvEscape = (value = "") => `"${String(value).replaceAll('"', '""')}"`;
const followerPattern = /(?:\b|@)(\d+(?:\.\d+)?)\s*([km])?\s+followers?\b/i;

function followerCount(text) {
  const match = text.match(followerPattern);
  if (!match) return null;
  const number = Number.parseFloat(match[1]);
  const multiplier = match[2]?.toLowerCase() === "m" ? 1_000_000 : match[2]?.toLowerCase() === "k" ? 1_000 : 1;
  return Math.round(number * multiplier);
}

const browser = await puppeteer.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.setUserAgent("Mozilla/5.0 (compatible; BrandAnalysisInfluencerResearch/1.0)");
  const searchUrl = `https://www.bing.com/search?q=${encodeURIComponent(`${query} ${minFollowers / 1000}K ${maxFollowers / 1000}K followers`)}`;
  await page.goto(searchUrl, { waitUntil: "domcontentloaded", timeout: 30_000 });
  const results = await page.$$eval("li.b_algo", (items) => items.map((item) => {
    const link = item.querySelector("h2 a");
    const snippet = item.querySelector(".b_caption p") ?? item.querySelector("p");
    return { title: link?.textContent?.trim() ?? "", url: link?.href ?? "", snippet: snippet?.textContent?.trim() ?? "" };
  }));

  const seen = new Set();
  const rows = results.flatMap((result) => {
    const observedFollowers = followerCount(`${result.title} ${result.snippet}`);
    if (!result.title || !result.url || observedFollowers === null || observedFollowers < minFollowers || observedFollowers > maxFollowers) return [];
    const handle = (result.title.match(/@([a-z0-9._]+)/i) ?? [])[1] ?? "";
    const id = normalize(handle || result.title);
    if (!id || seen.has(id)) return [];
    seen.add(id);
    return [{
      creator_name: result.title.replace(/\s*\([^)]*followers?[^)]*\)/i, "").trim(),
      handle: handle ? `@${handle}` : "",
      observed_followers: observedFollowers,
      follower_evidence: result.snippet,
      matched_query: query,
      source_url: result.url,
      discovered_at: new Date().toISOString(),
      review_status: "needs_review",
    }];
  }).slice(0, limit);

  const headers = Object.keys(rows[0] ?? {
    creator_name: "", handle: "", observed_followers: "", follower_evidence: "", matched_query: "", source_url: "", discovered_at: "", review_status: "",
  });
  const csv = [headers.join(","), ...rows.map((row) => headers.map((header) => csvEscape(row[header])).join(","))].join("\n");
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.writeFile(output, csv, "utf8");
  console.log(`Saved ${rows.length} review-required candidates to ${output}`);
} finally {
  await browser.close();
}
