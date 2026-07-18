import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

test("enables after decode and accepts exactly one launch", async () => {
  const classes = new Set(["app-loading"]);
  const classList = {
    add: (...names) => names.forEach((name) => classes.add(name)),
    remove: (...names) => names.forEach((name) => classes.delete(name)),
  };
  const attributes = new Map();
  const button = {
    disabled: true,
    listener: null,
    options: null,
    addEventListener(_type, listener, options) {
      this.listener = listener;
      this.options = options;
    },
  };
  const screenStart = {
    setAttribute(name, value) { attributes.set(`start:${name}`, value); },
  };
  const screenStatistics = {
    setAttribute(name, value) { attributes.set(`statistics:${name}`, value); },
  };
  const timers = [];
  const context = {
    console,
    navigator: {},
    document: {
      documentElement: { classList },
      getElementById(id) {
        return {
          "start-button": button,
          "screen-start": screenStart,
          "screen-statistics": screenStatistics,
        }[id];
      },
      querySelectorAll() {
        return [{ decode: () => Promise.resolve() }];
      },
    },
    window: {
      addEventListener() {},
      setTimeout(listener, delay) { timers.push({ listener, delay }); },
    },
  };
  const source = await readFile(new URL("../launch-app/app.js", import.meta.url), "utf8");
  vm.runInNewContext(source, context);
  await new Promise((resolve) => setImmediate(resolve));

  assert.equal(button.disabled, false);
  assert.equal(classes.has("app-loading"), false);
  assert.equal(classes.has("app-ready"), true);
  assert.equal(button.options.once, true);

  button.listener();
  button.listener();
  assert.equal(button.disabled, true);
  assert.equal(classes.has("is-launching"), true);
  assert.equal(attributes.get("start:aria-hidden"), "true");
  assert.equal(attributes.get("statistics:aria-hidden"), "false");
  assert.equal(timers.length, 1);
  assert.equal(timers[0].delay, 1900);

  timers[0].listener();
  assert.equal(classes.has("is-launching"), false);
  assert.equal(classes.has("is-launched"), true);
});
