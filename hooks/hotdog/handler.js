import { spawn } from "node:child_process";
import os from "node:os";
import path from "node:path";

// message:received hook — deterministic /hotdog trigger.
// Fires scripts/hotdog.sh (which runs debate.py / judge.py and streams to Telegram).
// Only acts on messages starting with /hotdog; everything else passes through.
const handler = async (event) => {
  if (event.type !== "message" || event.action !== "received") return;
  const content = String(event?.context?.content ?? "").trim();
  const m = content.match(/^\/hotdog\b\s*([\s\S]*)$/i);
  if (!m) return;

  const rest = (m[1] || "").trim();
  const sp = rest.indexOf(" ");
  const sub = (sp === -1 ? rest : rest.slice(0, sp)).toLowerCase() || "help";
  const topic = sp === -1 ? "" : rest.slice(sp + 1).trim();

  const script = path.join(os.homedir(), ".openclaw", "scripts", "hotdog.sh");
  const args = [script, sub];
  if (topic) args.push(topic);
  args.push("--tg"); // stream results to Brian's Telegram

  try {
    const child = spawn("bash", args, { detached: true, stdio: "ignore" });
    child.unref();
    const label = topic ? `\`${sub}\` — ${topic}` : `\`${sub}\``;
    event.messages.push(`🌭 hotdog ${label} queued — streaming to your Telegram…`);
  } catch (err) {
    event.messages.push(`🌭 hotdog failed to launch: ${String(err && err.message ? err.message : err)}`);
  }
};

export { handler as default };
