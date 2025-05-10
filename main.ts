import "https://deno.land/std@0.221.0/dotenv/load.ts";

const WEBHOOK = Deno.env.get("DISCORD_URL")!;

Deno.cron("discord ping (5min)", "*/5 * * * *", async () => {
  await fetch(WEBHOOK, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ content: `Edge ping ${Date.now()}` }),
  });
  console.log("sent");
});
