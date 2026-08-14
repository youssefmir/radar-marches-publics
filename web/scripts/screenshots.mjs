// Captures Playwright des pages clés (clair / sombre, ordinateur / mobile), prises après les animations.
// Lance `vite preview` en arrière-plan, capture, puis l'arrête.
// Usage : node scripts/screenshots.mjs [dossier_sortie]
import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
import path from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const OUT = path.resolve(process.argv[2] ?? "../docs/img");
const PORT = 4173;
const BASE = `http://127.0.0.1:${PORT}/radar-marches-publics/`;
mkdirSync(OUT, { recursive: true });

const server = spawn("npx", ["vite", "preview", "--port", String(PORT), "--strictPort", "--host", "127.0.0.1"], { stdio: "ignore", detached: true });
const stop = () => { try { process.kill(-server.pid); } catch { /* déjà arrêté */ } };
process.on("exit", stop);

async function waitServer() {
  for (let i = 0; i < 60; i++) {
    try { if ((await fetch(BASE)).ok) return; } catch { /* pas encore prêt */ }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error("serveur de prévisualisation injoignable");
}

const SHOTS = [
  // nom, route, thème, appareil, pleine page, action
  ["hero", "#/", "light", "desktop", false],
  ["accueil-sombre", "#/", "dark", "desktop", false],
  ["accueil-page", "#/", "light", "desktop", true],
  ["radar", "#/radar", "light", "desktop", false],
  ["radar-analyse", "#/radar", "light", "desktop", false, "analyse"],
  ["radar-sombre", "#/radar", "dark", "desktop", false],
  ["panorama", "#/panorama", "light", "desktop", true],
  ["panorama-sombre", "#/panorama", "dark", "desktop", false],
  ["acheteurs", "#/acheteurs", "light", "desktop", false],
  ["fiche-acheteur", "#/acheteurs/21690123100011", "light", "desktop", true],
  ["methode", "#/methode", "light", "desktop", true],
  ["mobile-accueil", "#/", "light", "mobile", false],
  ["mobile-radar", "#/radar", "light", "mobile", false],
  ["mobile-panorama-sombre", "#/panorama", "dark", "mobile", false],
];

await waitServer();
const browser = await chromium.launch();
const errors = [];
for (const [name, route, theme, device, full, action] of SHOTS) {
  const ctx = await browser.newContext({
    viewport: device === "mobile" ? { width: 390, height: 844 } : { width: 1440, height: 900 },
    deviceScaleFactor: 1, colorScheme: theme,
  });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(`${name}: ${e.message}`));
  page.on("console", (m) => m.type() === "error" && errors.push(`${name}: ${m.text()}`));
  await page.goto(BASE + route, { waitUntil: "networkidle" });
  await page.waitForTimeout(2600); // fin des animations d'entrée
  if (action === "analyse") {
    await page.getByRole("button", { name: "Voir l'analyse" }).first().click();
    await page.waitForTimeout(500);
    await page.locator("article.avis").first().scrollIntoViewIfNeeded();
  }
  if (full) {
    // Déclenche les apparitions au défilement avant la capture pleine page.
    const h = await page.evaluate(() => document.body.scrollHeight);
    for (let y = 0; y < h; y += 500) { await page.evaluate((v) => window.scrollTo(0, v), y); await page.waitForTimeout(120); }
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(900);
  }
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: !!full });
  console.log("capture", file);
  await ctx.close();
}
await browser.close();
stop();
if (errors.length) {
  console.error("Erreurs dans la console :\n" + errors.join("\n"));
  process.exit(1);
}
