import "https://deno.land/std@0.221.0/dotenv/load.ts";

const GH_TOKEN = Deno.env.get("GH_PAT")!;          // Deploy › Settings › Variables
const OWNER    = "tabasuco-kwa-ieg";
const REPO     = "skima-watcher";
const WORKFLOW = "notify.yml";                       // ファイル名 or ID
const BRANCH   = "main";

const headers = {
  "Authorization": `Bearer ${GH_TOKEN}`,
  "User-Agent":    "deno-cron-trigger",
  "Accept":        "application/vnd.github+json",
  "Content-Type":  "application/json",
};

async function trigger() {
  const url = `https://api.github.com/repos/${OWNER}/${REPO}` +
              `/actions/workflows/${WORKFLOW}/dispatches`;
  const body = {
    ref: BRANCH,
    inputs: { reason: "deno cron 5min" },
  };
  const r = await fetch(url, { method: "POST", headers, body: JSON.stringify(body) });
  console.log("GitHub API", r.status, await r.text());
  if (!r.ok) throw new Error(`GitHub dispatch failed ${r.status}`);
}

Deno.cron("github-actions-dispatch", "*/5 * * * *", trigger);
