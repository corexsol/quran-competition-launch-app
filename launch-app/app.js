(() => {
  "use strict";

  const root = document.documentElement;
  const button = document.getElementById("start-button");
  const screenStart = document.getElementById("screen-start");
  const screenCeremony = document.getElementById("screen-ceremony");
  const criticalImages = Array.from(document.querySelectorAll("img"));
  const FORWARD_DURATION = 700;
  const RETURN_DURATION = 600;
  const RETURN_WINDOW = 900;
  const BLOCKED_EVENTS = [
    "contextmenu",
    "dragstart",
    "selectstart",
    "touchmove",
    "gesturestart",
    "gesturechange",
    "gestureend",
  ];
  let state = "loading";
  let transitionTimer = 0;
  let returnTapTimes = [];

  const decodeImage = (image) => {
    if (typeof image.decode !== "function") {
      return Promise.resolve();
    }
    return image.decode();
  };

  const finishStartReadiness = () => {
    state = "start";
    root.classList.remove("app-loading");
    root.classList.add("app-ready");
    button.disabled = false;
  };

  const launch = () => {
    if (state !== "start" || button.disabled) return;
    state = "launching";
    button.disabled = true;
    returnTapTimes = [];
    screenStart.setAttribute("aria-hidden", "true");
    screenCeremony.setAttribute("aria-hidden", "false");
    root.classList.add("is-launching");
    window.clearTimeout(transitionTimer);
    transitionTimer = window.setTimeout(() => {
      if (state !== "launching") return;
      root.classList.remove("is-launching");
      root.classList.add("is-launched");
      state = "ceremony";
    }, FORWARD_DURATION);
  };

  const returnToStart = () => {
    if (state !== "ceremony") return;
    state = "returning";
    returnTapTimes = [];
    window.clearTimeout(transitionTimer);
    root.classList.remove("is-launched", "is-launching");
    root.classList.add("is-returning");
    screenStart.setAttribute("aria-hidden", "false");
    screenCeremony.setAttribute("aria-hidden", "true");
    transitionTimer = window.setTimeout(() => {
      if (state !== "returning") return;
      root.classList.remove("is-returning");
      button.disabled = false;
      state = "start";
    }, RETURN_DURATION);
  };

  const recordReturnTap = () => {
    if (state !== "ceremony") return;
    const time = window.performance.now();
    returnTapTimes = returnTapTimes.filter(
      (recorded) => time - recorded <= RETURN_WINDOW,
    );
    returnTapTimes.push(time);
    if (returnTapTimes.length >= 3) returnToStart();
  };

  Promise.allSettled(criticalImages.map(decodeImage)).then(finishStartReadiness);

  button.addEventListener("click", launch);
  screenCeremony.addEventListener("pointerup", recordReturnTap);

  for (const type of BLOCKED_EVENTS) {
    document.addEventListener(type, (event) => event.preventDefault(), {
      passive: false,
    });
  }

  if ("serviceWorker" in navigator) {
    window.addEventListener(
      "load",
      () => {
        navigator.serviceWorker.register("./sw.js").catch((error) => {
          console.error("Service worker registration failed", error);
        });
      },
      { once: true },
    );
  }
})();
