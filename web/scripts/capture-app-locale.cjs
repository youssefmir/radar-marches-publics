// Capture de l'application locale (profil personnalisé). Prérequis : `make app` lancé dans un autre terminal.
const { chromium } = require("playwright");
const path = require("node:path");
(async () => {
  const out = path.resolve(process.argv[2] ?? "../docs/img/app-locale.png");
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, colorScheme: "light" });
  await page.goto("http://127.0.0.1:8000/radar-marches-publics/#/radar", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Mon entreprise/ }).click();
  await page.fill("#p-desc", "Bureau d'études en ingénierie des réseaux d'eau potable et d'assainissement, maîtrise d'œuvre de travaux de voirie et réseaux divers.");
  await page.fill("#p-cpv", "71300000 71320000");
  await page.fill("#p-dep", "33 40 64 47 24");
  await page.fill("#p-min", "30000");
  await page.fill("#p-max", "500000");
  await page.getByRole("button", { name: "Classer les avis" }).click();
  await page.waitForSelector("article.avis", { timeout: 120000 });
  await page.waitForTimeout(2500);
  await page.evaluate(() => window.scrollTo(0, 420));
  await page.waitForTimeout(800);
  await page.screenshot({ path: out });
  console.log("capture", out);
  await browser.close();
})();
