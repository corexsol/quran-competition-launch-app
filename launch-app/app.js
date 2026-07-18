(() => {
  "use strict";

  const root = document.documentElement;
  const button = document.getElementById("start-button");
  const screenStart = document.getElementById("screen-start");
  const screenStatistics = document.getElementById("screen-statistics");
  const criticalImages = Array.from(document.querySelectorAll("img"));
  let launched = false;

  const decodeImage = (image) => {
    if (typeof image.decode !== "function") {
      return Promise.resolve();
    }
    return image.decode().catch(() => undefined);
  };

  Promise.all(criticalImages.map(decodeImage)).then(() => {
    root.classList.remove("app-loading");
    root.classList.add("app-ready");
    button.disabled = false;
  });

  const launch = () => {
    if (launched || button.disabled) {
      return;
    }
    launched = true;
    button.disabled = true;
    screenStart.setAttribute("aria-hidden", "true");
    screenStatistics.setAttribute("aria-hidden", "false");
    root.classList.add("is-launching");

    window.setTimeout(() => {
      root.classList.remove("is-launching");
      root.classList.add("is-launched");
    }, 1900);
  };

  button.addEventListener("click", launch, { once: true });

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
