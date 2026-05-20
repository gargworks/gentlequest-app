#!/usr/bin/env node
// register-commands.js — Register the /eidetic global slash command.
//
// Run this ONCE after creating your Discord application. Discord caches
// global commands for up to an hour; re-run any time you change the schema
// below.
//
// Usage:
//   DISCORD_APPLICATION_ID=... DISCORD_BOT_TOKEN=... \
//     node integrations/discord-bot/register-commands.js
//
//   # During development you can register a guild-scoped copy (instant
//   # propagation, no 1h cache) by also exporting DISCORD_DEV_GUILD_ID:
//   DISCORD_APPLICATION_ID=... DISCORD_BOT_TOKEN=... DISCORD_DEV_GUILD_ID=... \
//     node integrations/discord-bot/register-commands.js
//
// What this script does:
//   1. PUTs the command list below to either
//        /applications/{app_id}/commands             (global, ~1h cache)
//      or
//        /applications/{app_id}/guilds/{gid}/commands (guild, instant)
//   2. Prints the response so you can confirm Discord accepted the schema.
//
// What it does NOT do:
//   - Does not create the Discord app for you.
//   - Does not write any secrets anywhere. Bot token is read from env only.
//   - Does not deploy the Worker. Use `wrangler deploy` for that.

const APP_ID    = process.env.DISCORD_APPLICATION_ID;
const BOT_TOKEN = process.env.DISCORD_BOT_TOKEN;
const DEV_GUILD = process.env.DISCORD_DEV_GUILD_ID || "";

// CommandOption types from Discord's interaction docs:
//   1=SUB_COMMAND  2=SUB_COMMAND_GROUP  3=STRING  4=INTEGER  5=BOOLEAN ...
const OPTION_TYPE_STRING = 3;

// Single global command: /eidetic question:<string>
const COMMANDS = [
  {
    name: "eidetic",
    description: "Ask your local eidetic-daemon a question (only you see the reply).",
    type: 1, // CHAT_INPUT
    dm_permission: true, // allow in DMs as well as in guilds
    options: [
      {
        name: "question",
        description: "What do you want to ask your eidetic-daemon?",
        type: OPTION_TYPE_STRING,
        required: true,
        // Discord caps option description at 100 chars; this is well within.
      },
    ],
  },
];

async function main() {
  if (!APP_ID || !BOT_TOKEN) {
    console.error(
      "ERR: set DISCORD_APPLICATION_ID and DISCORD_BOT_TOKEN environment variables.\n" +
      "  Find both in https://discord.com/developers/applications → your app."
    );
    process.exit(2);
  }

  const base = "https://discord.com/api/v10";
  const path = DEV_GUILD
    ? `${base}/applications/${APP_ID}/guilds/${DEV_GUILD}/commands`
    : `${base}/applications/${APP_ID}/commands`;

  const scope = DEV_GUILD ? `guild ${DEV_GUILD}` : "global";
  console.log(`Registering ${COMMANDS.length} command(s) into ${scope} scope…`);

  // PUT replaces the entire command list at this scope — exactly what we
  // want for a tiny single-command bot. If you ever expand the bot to
  // multiple commands, keep all of them in COMMANDS or you'll silently
  // delete the ones you omit.
  const res = await fetch(path, {
    method: "PUT",
    headers: {
      "Authorization": `Bot ${BOT_TOKEN}`,
      "Content-Type":  "application/json",
      "User-Agent":    "eidetic-discord-bot (register-commands.js, +https://eidetic.works)",
    },
    body: JSON.stringify(COMMANDS),
  });

  const text = await res.text();
  if (!res.ok) {
    console.error(`Discord rejected the registration: HTTP ${res.status}`);
    console.error(text);
    process.exit(1);
  }

  let parsed;
  try { parsed = JSON.parse(text); } catch { parsed = text; }
  console.log("OK. Discord response:");
  console.log(JSON.stringify(parsed, null, 2));
  if (!DEV_GUILD) {
    console.log("\nNote: global commands can take up to an hour to appear in every guild.");
    console.log("For instant iteration during development, set DISCORD_DEV_GUILD_ID.");
  }
}

main().catch((err) => {
  console.error("Unexpected error:", err);
  process.exit(1);
});
