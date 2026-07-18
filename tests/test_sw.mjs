import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

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
  assert.match(source, /quran-launch-/);
  assert.match(source, /CACHE_NAME = `\$\{CACHE_PREFIX\}v2`/);
  const match = source.match(/Object\.freeze\((\[[\s\S]*?\])\)/);
  assert.ok(match, "PRECACHE_URLS array must be frozen");
  const urls = Function(`"use strict"; return (${match[1]});`)();
  const expected = ["./", ...(await listRuntimeFiles(app))];
  assert.deepEqual(new Set(urls), new Set(expected));
  assert.equal(urls.length, expected.length);
  assert.equal(new Set(urls).size, urls.length);
  assert.match(source, /cache\.addAll\(PRECACHE_REQUESTS\)/);
  assert.match(source, /self\.skipWaiting\(\)/);
  assert.match(source, /self\.clients\.claim\(\)/);
  assert.match(source, /request\.mode === "navigate"/);
  assert.match(source, /new URL\(request\.url\)\.origin !== self\.location\.origin/);
  assert.match(source, /caches\.match\(request, \{ ignoreSearch: true \}\)/);
});

test("install precaches every runtime URL with forced-fresh requests", async () => {
  const app = new URL("../launch-app/", import.meta.url);
  const source = await readFile(new URL("sw.js", app), "utf8");
  const listeners = new Map();
  let addedRequests;
  let installPromise;

  class TestRequest {
    constructor(input, options = {}) {
      this.url = input;
      this.cache = options.cache ?? "default";
    }
  }

  const context = {
    Request: TestRequest,
    URL,
    caches: {
      open: async () => ({
        addAll: async (requests) => {
          addedRequests = requests;
        },
      }),
    },
    self: {
      addEventListener(type, listener) {
        listeners.set(type, listener);
      },
      skipWaiting: async () => {},
      clients: { claim: async () => {} },
      location: { origin: "https://example.test" },
    },
  };

  vm.runInNewContext(source, context);
  listeners.get("install")({
    waitUntil(promise) {
      installPromise = Promise.resolve(promise);
    },
  });
  await installPromise;

  const expected = ["./", ...(await listRuntimeFiles(app))];
  assert.equal(addedRequests.length, expected.length);
  assert.ok(
    addedRequests.every((request) => request instanceof TestRequest),
    "install must pass Request objects to cache.addAll",
  );
  assert.deepEqual(
    new Set(addedRequests.map((request) => request.url)),
    new Set(expected),
  );
  assert.ok(
    addedRequests.every((request) => request.cache === "reload"),
    "every precache request must bypass a warm HTTP cache",
  );
});
