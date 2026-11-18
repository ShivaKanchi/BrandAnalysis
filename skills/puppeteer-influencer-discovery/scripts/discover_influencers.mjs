#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { existsSync } from "node:fs";

const argv = process.argv.slice(2);
const values = { query: [] };
for (let index = 0; index < argv.length; index += 1) {
  const token = argv[index];
  if (!token.startsWith("--")) continue;
  const key = token.slice(2);
  const next = argv[index + 1];
  const value = next && !next.startsWith("--") ? next : "true";
  if (next && !next.startsWith("--")) index += 1;
  if (key === "query") values.query.push(value.trim());
  else values[key] = value;
}

const queries = values.query.filter(Boolean);
const output = values.output?.trim();
const source = (values.source ?? "youtube").toLowerCase();
const region = (values.region ?? "IN").toUpperCase();
const limit = Number.parseInt(values.limit ?? "25", 10);
const minFollowers = Number.parseInt(values["min-followers"] ?? "0", 10);
const maxFollowers = Number.parseInt(values["max-followers"] ?? "999999999", 10);
const exclude = values.exclude ? new RegExp(values.exclude, "i") : null;

if (
  queries.length === 0 ||
  !output ||
  !["youtube", "bing"].includes(source) ||
  !Number.isInteger(limit) ||
  limit < 1 ||
  limit > 100 ||
  !Number.isInteger(minFollowers) ||
  !Number.isInteger(maxFollowers) ||
  minFollowers < 0 ||
  minFollowers > maxFollowers
) {
  console.error(
    "Usage: node discover_influencers.mjs --query <text> [--query <text> ...] --source <youtube|bing>\n" +
      "         --min-followers <n> --max-followers <n> --limit <1-100> --region <IN> --output <csv> [--exclude <regex>]"
  );
  process.exit(1);
}

const normalize = (value = "") => value.toLowerCase().replace(/[^a-z0-9]/g, "");
const csvEscape = (value = "") => `"${String(value).replaceAll('"', '""')}"`;
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const followerPattern =
  /(\d[\d,]*(?:\.\d+)?)\s*(k|m|b|thousand|million|billion|lakh|lakhs|lac|lacs|crore|crores|cr)?\s*(?:followers?|subscribers?)/i;

const multiplierFor = (unit = "") => {
  const key = unit.toLowerCase();
  if (key === "k" || key === "thousand") return 1_000;
  if (key === "lakh" || key === "lakhs" || key === "lac" || key === "lacs") return 100_000;
  if (key === "m" || key === "million") return 1_000_000;
  if (key === "crore" || key === "crores" || key === "cr") return 10_000_000;
  if (key === "b" || key === "billion") return 1_000_000_000;
  return 1;
};

function followerCount(text = "") {
  const match = text.match(followerPattern);
  if (!match) return null;
  const number = Number.parseFloat(match[1].replaceAll(",", ""));
  if (!Number.isFinite(number)) return null;
  return Math.round(number * multiplierFor(match[2] ?? ""));
}

function handleFromUrl(url = "") {
  const match = url.match(/(?:youtube\.com|instagram\.com)\/@?([a-z0-9._-]{2,})/i);
  return match ? match[1] : "";
}

function cleanName(title = "") {
  return title
    .replace(/\s*[-|–]\s*YouTube\s*$/i, "")
    .replace(/\s*[•|]\s*Instagram.*$/i, "")
    .replace(/\s*\([^)]*(?:followers?|subscribers?)[^)]*\)/i, "")
    .replace(/\s*\(@[a-z0-9._-]+\)/i, "")
    .trim();
}

function extractYouTubeChannels(root) {
  const channels = [];
  const seen = new Set();
  const textOf = (value) => value?.simpleText ?? value?.runs?.map((run) => run.text).join("") ?? "";
  const walk = (node) => {
    if (!node || typeof node !== "object") return;
    if (Array.isArray(node)) {
      for (const item of node) walk(item);
      return;
    }
    if (node.channelRenderer) {
      const renderer = node.channelRenderer;
      const channelId = renderer.channelId ?? "";
      if (channelId && !seen.has(channelId)) {
        seen.add(channelId);
        // Channel-search results keep the handle in subscriberCountText and the
        // subscriber total in videoCountText, despite the field names.
        channels.push({
          title: textOf(renderer.title),
          handle: textOf(renderer.subscriberCountText).trim(),
          rawFollowers:
            textOf(renderer.videoCountText) ||
            renderer.videoCountText?.accessibility?.accessibilityData?.label ||
            "",
          snippet: textOf(renderer.descriptionSnippet),
          channelId,
          url:
            renderer.navigationEndpoint?.commandMetadata?.webCommandMetadata?.url ??
            renderer.navigationEndpoint?.browseEndpoint?.canonicalBaseUrl ??
            "",
          verified: Boolean(
            renderer.ownerBadges?.some(
              (badge) => badge.metadataBadgeRenderer?.style === "BADGE_STYLE_TYPE_VERIFIED"
            )
          ),
        });
      }
    }
    for (const value of Object.values(node)) walk(value);
  };
  walk(root);
  return channels;
}

async function collectYouTube(query) {
  const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}&sp=EgIQAg%253D%253D&hl=en&gl=${region}`;
  let lastError;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch(searchUrl, {
        headers: {
          "user-agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
          "accept-language": "en-IN,en;q=0.9",
        },
      });
      if (response.status === 429) {
        lastError = new Error("HTTP 429 (rate limited)");
        await sleep(5_000 * (attempt + 1));
        continue;
      }
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const html = await response.text();
      const match =
        html.match(/var ytInitialData = (\{.*?\});<\/script>/s) ??
        html.match(/ytInitialData"\]\s*=\s*(\{.*?\});/s);
      if (!match) return [];
      return extractYouTubeChannels(JSON.parse(match[1]));
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}

async function loadPuppeteer() {
  for (const packageName of ["puppeteer", "puppeteer-core"]) {
    try {
      const loaded = await import(packageName);
      return { puppeteer: loaded.default, core: packageName === "puppeteer-core" };
    } catch {
      // Fall through to the next package.
    }
  }
  return null;
}

let puppeteer = null;
let executablePath = null;
if (source === "bing") {
  const loaded = await loadPuppeteer();
  if (!loaded) {
    console.error("Puppeteer is required for --source bing. Run: npm --prefix skills/puppeteer-influencer-discovery install --no-save puppeteer-core");
    process.exit(1);
  }
  puppeteer = loaded.puppeteer;
  if (loaded.core) {
    const browserCandidates = [
      process.env.PUPPETEER_EXECUTABLE_PATH,
      "C:/Program Files/Google/Chrome/Application/chrome.exe",
      "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
      "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
      "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
      "/usr/bin/google-chrome",
      "/usr/bin/chromium",
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ].filter(Boolean);
    executablePath = browserCandidates.find((candidate) => existsSync(candidate));
    if (!executablePath) {
      console.error("No Chrome/Edge executable found. Set PUPPETEER_EXECUTABLE_PATH or install full Puppeteer.");
      process.exit(1);
    }
  }
}

async function collectBing(page, query) {
  const rangeTerm =
    minFollowers === 0 && maxFollowers >= 999_999_999
      ? ""
      : ` ${minFollowers} ${maxFollowers} followers OR subscribers`;
  const searchUrl = `https://www.bing.com/search?q=${encodeURIComponent(`${query}${rangeTerm}`)}`;
  await page.goto(searchUrl, { waitUntil: "domcontentloaded", timeout: 45_000 });
  return page.$$eval("li.b_algo", (items) =>
    items.map((item) => {
      const link = item.querySelector("h2 a");
      const snippet = item.querySelector(".b_caption p") ?? item.querySelector("p");
      return {
        title: link?.textContent?.trim() ?? "",
        url: link?.href ?? "",
        snippet: snippet?.textContent?.trim() ?? "",
      };
    })
  );
}

const browser = source === "bing" ? await puppeteer.launch({ headless: true, executablePath }) : null;
try {
  const page = browser ? await browser.newPage() : null;
  if (page) {
    await page.setUserAgent(
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    );
    await page.setExtraHTTPHeaders({ "accept-language": "en-IN,en;q=0.9" });
  }

  const seenHandles = new Set();
  const seenNames = new Set();
  const rows = [];

  for (const query of queries) {
    if (rows.length >= limit) break;
    if (source === "youtube" && rows.length > 0) await sleep(1_500);
    let results;
    try {
      results = source === "youtube" ? await collectYouTube(query) : await collectBing(page, query);
    } catch (error) {
      console.error(`Skipping query "${query}": ${error.message}`);
      continue;
    }
    for (const result of results) {
      if (rows.length >= limit) break;
      const evidence = source === "youtube" ? result.rawFollowers : `${result.title} ${result.snippet}`;
      const observedFollowers =
        source === "youtube"
          ? followerCount(result.rawFollowers ?? "")
          : followerCount(`${evidence} ${result.snippet ?? ""}`);
      if (observedFollowers === null || observedFollowers < minFollowers || observedFollowers > maxFollowers) continue;

      const handle = (result.handle?.match(/@[a-z0-9._-]+/i) ?? [])[0] ?? handleFromUrl(result.url ?? "");
      const creatorName = cleanName(result.title ?? "");
      const handleId = normalize(handle);
      const nameId = normalize(creatorName);
      if (!nameId || seenNames.has(nameId) || (handleId && seenHandles.has(handleId))) continue;
      if (exclude?.test(`${creatorName} ${handle} ${result.snippet ?? ""}`)) continue;
      if (source === "youtube" && !handleId && !result.channelId) continue;

      seenNames.add(nameId);
      if (handleId) seenHandles.add(handleId);
      const normalizedHandle = handle && !handle.startsWith("@") ? `@${handle}` : handle;
      rows.push({
        creator_name: creatorName,
        handle: normalizedHandle ?? "",
        channel_id: result.channelId ?? "",
        observed_followers: observedFollowers,
        follower_evidence: `${evidence}${result.snippet ? ` — ${result.snippet}` : ""}`.trim(),
        matched_query: query,
        source_url:
          source === "youtube" && normalizedHandle
            ? `https://www.youtube.com/${normalizedHandle}`
            : (result.url ?? ""),
        verified: source === "youtube" ? String(result.verified ?? false) : "",
        discovered_at: new Date().toISOString(),
        review_status: "needs_review",
      });
    }
  }

  const columns = [
    "creator_name",
    "handle",
    "channel_id",
    "observed_followers",
    "follower_evidence",
    "matched_query",
    "source_url",
    "verified",
    "discovered_at",
    "review_status",
  ];
  const csv = [columns.join(","), ...rows.map((row) => columns.map((column) => csvEscape(row[column])).join(","))].join("\n");
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.writeFile(output, csv, "utf8");
  console.log(`Saved ${rows.length} review-required candidates to ${output}`);
} finally {
  if (browser) await browser.close();
}
