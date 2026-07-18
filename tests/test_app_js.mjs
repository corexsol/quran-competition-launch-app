import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

async function loadAppHarness() {
  const classes = new Set(["app-loading"]);
  const classList = {
    add: (...names) => names.forEach((name) => classes.add(name)),
    remove: (...names) => names.forEach((name) => classes.delete(name)),
  };
  const documentListeners = new Map();
  const timers = new Map();
  let timerId = 0;
  let now = 0;

  const makeElement = () => ({
    disabled: true,
    attributes: new Map(),
    listeners: new Map(),
    setAttribute(name, value) {
      this.attributes.set(name, value);
    },
    addEventListener(type, listener, options = {}) {
      this.listeners.set(type, { listener, options });
    },
  });
  const button = makeElement();
  const screenStart = makeElement();
  const screenCeremony = makeElement();

  const context = {
    console,
    navigator: {},
    document: {
      documentElement: { classList },
      getElementById(id) {
        return {
          "start-button": button,
          "screen-start": screenStart,
          "screen-ceremony": screenCeremony,
        }[id];
      },
      querySelectorAll() {
        return [
          { decode: () => Promise.resolve() },
          { decode: () => Promise.reject(new Error("decode failed")) },
        ];
      },
      addEventListener(type, listener, options = {}) {
        documentListeners.set(type, { listener, options });
      },
    },
    window: {
      performance: { now: () => now },
      addEventListener() {},
      setTimeout(listener, delay) {
        const id = ++timerId;
        timers.set(id, { listener, delay, active: true });
        return id;
      },
      clearTimeout(id) {
        if (timers.has(id)) timers.get(id).active = false;
      },
    },
  };

  const source = await readFile(new URL("../launch-app/app.js", import.meta.url), "utf8");
  vm.runInNewContext(source, context);
  await new Promise((resolve) => setImmediate(resolve));

  const runTimer = (delay) => {
    const match = [...timers.values()].find(
      (timer) => timer.active && timer.delay === delay,
    );
    assert.ok(match, `missing active ${delay}ms timer`);
    match.active = false;
    match.listener();
  };

  return {
    source,
    classes,
    button: {
      get disabled() {
        return button.disabled;
      },
      get listenerOptions() {
        return button.listeners.get("click").options;
      },
      click: () => button.listeners.get("click").listener(),
    },
    startAttribute: (name) => screenStart.attributes.get(name),
    ceremony: {
      attribute: (name) => screenCeremony.attributes.get(name),
      pointerup: () => screenCeremony.listeners.get("pointerup").listener(),
    },
    documentListeners,
    setNow: (value) => {
      now = value;
    },
    pendingTimers: (delay) =>
      [...timers.values()].filter(
        (timer) => timer.active && timer.delay === delay,
      ).length,
    runTimer,
  };
}

async function loadLaunchedAppHarness() {
  const app = await loadAppHarness();
  app.button.click();
  app.runTimer(1900);
  return app;
}

test("enables start after mixed image decode outcomes using allSettled readiness", async () => {
  const app = await loadAppHarness();

  assert.match(app.source, /Promise\.allSettled\(/);
  assert.equal(app.button.disabled, false);
  assert.equal(app.classes.has("app-loading"), false);
  assert.equal(app.classes.has("app-ready"), true);
});

test("guards launch, returns on three fast taps, and launches again", async () => {
  const app = await loadAppHarness();

  app.button.click();
  app.button.click();
  assert.notEqual(app.button.listenerOptions.once, true);
  assert.equal(app.pendingTimers(1900), 1);
  assert.equal(app.startAttribute("aria-hidden"), "true");
  assert.equal(app.ceremony.attribute("aria-hidden"), "false");

  app.runTimer(1900);
  assert.equal(app.classes.has("is-launching"), false);
  assert.equal(app.classes.has("is-launched"), true);

  app.setNow(100);
  app.ceremony.pointerup();
  app.setNow(450);
  app.ceremony.pointerup();
  app.setNow(850);
  app.ceremony.pointerup();
  assert.equal(app.classes.has("is-launched"), false);
  assert.equal(app.classes.has("is-returning"), true);
  assert.equal(app.pendingTimers(600), 1);
  assert.equal(app.startAttribute("aria-hidden"), "false");
  assert.equal(app.ceremony.attribute("aria-hidden"), "true");

  app.runTimer(600);
  assert.equal(app.classes.has("is-returning"), false);
  assert.equal(app.button.disabled, false);

  app.button.click();
  assert.equal(app.pendingTimers(1900), 1);
});

test("ignores return taps outside ceremony state", async () => {
  const app = await loadAppHarness();

  for (const time of [0, 100, 200]) {
    app.setNow(time);
    app.ceremony.pointerup();
  }
  assert.equal(app.classes.has("is-returning"), false);

  app.button.click();
  for (const time of [300, 400, 500]) {
    app.setNow(time);
    app.ceremony.pointerup();
  }
  assert.equal(app.classes.has("is-launching"), true);
  assert.equal(app.classes.has("is-returning"), false);
  assert.equal(app.pendingTimers(1900), 1);
});

test("does not return for incomplete or slow tap sequences", async () => {
  const app = await loadLaunchedAppHarness();

  for (const time of [0, 500, 1200]) {
    app.setNow(time);
    app.ceremony.pointerup();
  }
  assert.equal(app.classes.has("is-launched"), true);
  assert.equal(app.classes.has("is-returning"), false);
  assert.equal(app.pendingTimers(600), 0);
});

test("registers non-passive blockers for callout selection drag and gestures", async () => {
  const app = await loadAppHarness();

  for (const type of [
    "contextmenu",
    "dragstart",
    "selectstart",
    "touchmove",
    "gesturestart",
    "gesturechange",
    "gestureend",
  ]) {
    const registration = app.documentListeners.get(type);
    assert.ok(registration, `missing ${type} blocker`);
    assert.equal(registration.options.passive, false);
    const event = {
      prevented: false,
      preventDefault() {
        this.prevented = true;
      },
    };
    registration.listener(event);
    assert.equal(event.prevented, true);
  }
});
