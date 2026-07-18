import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import test from "node:test";

async function listRuntimeFiles(directory, prefix = "./") {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (entry.isDirectory()) {
      files.push(
        ...(await listRuntimeFiles(
          new URL(`${entry.name}/`, directory),
          `${prefix}${entry.name}/`,
        )),
      );
    } else if (entry.isFile()) {
      files.push(`${prefix}${entry.name}`);
    }
  }
  return files.sort();
}

test("precache mirrors the physical runtime inventory and owns its lifecycle", async () => {
  const app = new URL("../launch-app/", import.meta.url);
  const source = await readFile(new URL("sw.js", app), "utf8");
  const match = source.match(/Object\.freeze\((\[[\s\S]*?\])\)/);
  assert.ok(match, "PRECACHE_URLS array must be frozen");
  const urls = Function(`"use strict"; return (${match[1]});`)();
  const expected = ["./", ...(await listRuntimeFiles(app))];
  assert.deepEqual(new Set(urls), new Set(expected));
  assert.equal(urls.length, expected.length);
  assert.equal(new Set(urls).size, urls.length);
  assert.match(source, /cache\.addAll\(PRECACHE_URLS\)/);
  assert.match(source, /self\.skipWaiting\(\)/);
  assert.match(source, /self\.clients\.claim\(\)/);
  assert.match(source, /request\.mode === "navigate"/);
  assert.match(source, /new URL\(request\.url\)\.origin !== self\.location\.origin/);
  assert.match(source, /caches\.match\(request, \{ ignoreSearch: true \}\)/);
});
