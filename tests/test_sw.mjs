import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("precache lists every runtime file and owns its lifecycle", async () => {
  const source = await readFile(new URL("../launch-app/sw.js", import.meta.url), "utf8");
  const match = source.match(/Object\.freeze\((\[[\s\S]*?\])\)/);
  assert.ok(match, "PRECACHE_URLS array must be frozen");
  const urls = Function(`"use strict"; return (${match[1]});`)();
  const expected = [
    "./",
    "./index.html",
    "./style.css",
    "./app.js",
    "./sw.js",
    "./manifest.json",
    "./assets/title.png",
    "./assets/minister.png",
    "./assets/start-button.png",
    "./assets/background-sides.png",
    "./assets/background-medallion.png",
    "./assets/statistics.png",
    "./assets/icon-180.png",
    "./assets/icon-192.png",
    "./assets/icon-512.png",
  ];
  assert.deepEqual(new Set(urls), new Set(expected));
  assert.match(source, /cache\.addAll\(PRECACHE_URLS\)/);
  assert.match(source, /self\.skipWaiting\(\)/);
  assert.match(source, /self\.clients\.claim\(\)/);
  assert.match(source, /request\.mode === "navigate"/);
  assert.match(source, /caches\.match\(request, \{ ignoreSearch: true \}\)/);
});
