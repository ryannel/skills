// Renders each option at 375 px wide (phone emulation, touch) in headless Chrome over the
// DevTools Protocol, then renders sheet.html (the side-by-side sheet) to ../options.png.
// Usage: node capture.mjs   (Node 24; CHROME overrides the browser path)
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const chrome = process.env.CHROME ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const profile = mkdtempSync(join(tmpdir(), "options-chrome-"));
const proc = spawn(chrome, ["--headless", "--disable-gpu", "--hide-scrollbars", "--remote-debugging-port=0",
  `--user-data-dir=${profile}`, "about:blank"], { stdio: ["ignore", "ignore", "pipe"] });
const wsUrl = await new Promise((ok, fail) => {
  let buf = "";
  proc.stderr.on("data", (d) => { buf += d; const m = buf.match(/ws:\/\/\S+/); if (m) ok(m[0]); });
  proc.on("exit", () => fail(new Error("chrome exited: " + buf)));
});
const browser = new WebSocket(wsUrl);
await new Promise((ok) => browser.addEventListener("open", ok));
let nextId = 1; const pending = new Map();
browser.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}, sessionId) => new Promise((ok, fail) => {
  const id = nextId++; pending.set(id, (m) => (m.error ? fail(new Error(method + ": " + m.error.message)) : ok(m.result)));
  browser.send(JSON.stringify({ id, method, params, sessionId }));
});

async function shot(file, out, { width, height, mobile, fullPage }) {
  const { targetId } = await send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
  await send("Page.enable", {}, sessionId);
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile }, sessionId);
  if (mobile) await send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 }, sessionId);
  await send("Page.navigate", { url: pathToFileURL(join(here, file)).href }, sessionId);
  await new Promise((r) => setTimeout(r, 800));
  const { result } = await send("Runtime.evaluate", { expression: "JSON.stringify([innerWidth, document.documentElement.scrollHeight, document.documentElement.scrollWidth])", returnByValue: true }, sessionId);
  const [w, h, sw] = JSON.parse(result.value);
  const clipH = fullPage ? Math.max(height, h) : height;
  const { data } = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width, height: clipH, scale: 1 } }, sessionId);
  writeFileSync(join(here, out), Buffer.from(data, "base64"));
  console.log(`${out}: viewport ${w}px wide, page ${sw}x${h}, captured ${width}x${clipH}`);
  await send("Target.closeTarget", { targetId });
}

try {
  for (const o of ["a-day-list", "b-week-strip", "c-plain-letter"])
    await shot(`${o}.html`, `${o}.png`, { width: 375, height: 812, mobile: true, fullPage: true });
  await shot("sheet.html", "../options.png", { width: 2440, height: 800, mobile: false, fullPage: true });
} finally {
  browser.close(); proc.kill();
  await new Promise((r) => (proc.exitCode !== null ? r() : proc.on("exit", r)));
  rmSync(profile, { recursive: true, force: true, maxRetries: 5 });
}
