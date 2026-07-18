# King Abdulaziz Quran Competition Launch App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-screen, ceremony-safe 4:3 launch PWA that transitions once from the Arabic Start screen to the competition statistics and works completely offline on a ninth-generation iPad.

**Architecture:** A plain static app under `launch-app/` uses pre-rendered local PNG artwork, a semantic two-screen DOM, CSS-only GPU-friendly animation, and a tiny JavaScript state controller. A versioned service worker precaches every runtime file, while repository-local Python and Node tests verify asset integrity, document structure, one-shot interaction, cache coverage, and the final payload.

**Tech Stack:** HTML5, CSS, browser JavaScript, Service Worker API, Web App Manifest, Python 3 with `pypdfium2` and Pillow for asset conversion, Node.js built-in test runner, and a real browser for 4:3/offline verification.

## Global Constraints

- Target ninth-generation iPad Safari in landscape at a 4:3 viewport; verify at 1080 x 810 and 1024 x 768.
- The runtime contains exactly `index.html`, `style.css`, `app.js`, `sw.js`, `manifest.json`, `README.md`, and local files under `assets/`.
- No framework, router, backend, analytics, external font, CDN, or runtime network dependency.
- Use the inspected content mapping: Asset 1 Start button, Asset 2 minister text, Asset 3 title, Asset 4 side ornaments, Asset 5 central medallion, and Asset 1022 statistics.
- Keep the Start target at least 300 CSS pixels wide at 1080 x 810.
- Transition duration is approximately 1.9 seconds and uses only transform and opacity.
- Disable repeated activation after the first accepted click.
- Precache every runtime file and serve same-origin GET requests cache-first.
- Include iOS standalone, translucent status bar, Apple touch icon, locked viewport, landscape manifest orientation, touch hardening, and bounce/selection/callout suppression.
- Keep the complete `launch-app/` directory below 10 MB.

## File Map

- `scripts/prepare_assets.py`: deterministic PDF-to-PNG rendering, trimming, icon generation, and PNG optimization.
- `tests/test_prepare_assets.py`: asset-pipeline unit and integration checks.
- `tests/test_static_app.py`: HTML, CSS, and manifest contract checks.
- `tests/test_app_js.mjs`: one-shot interaction controller test with a minimal DOM harness.
- `tests/test_sw.mjs`: service-worker precache coverage and lifecycle contract test.
- `tests/test_bundle.py`: final local-reference, PNG-integrity, dependency, and payload audit.
- `launch-app/index.html`: Arabic two-screen application shell and PWA metadata.
- `launch-app/style.css`: 4:3 layout, ceremony hardening, and transition animation.
- `launch-app/app.js`: asset readiness, launch-state control, ARIA updates, and service-worker registration.
- `launch-app/sw.js`: versioned installation, activation cleanup, and cache-first fetching.
- `launch-app/manifest.json`: Arabic standalone landscape PWA definition.
- `launch-app/README.md`: HTTPS serving, iPad installation, and offline rehearsal procedure.
- `launch-app/assets/*.png`: rendered artwork and 180/192/512 icons.

---

### Task 1: Deterministic Artwork Pipeline

**Files:**
- Create: `scripts/prepare_assets.py`
- Create: `tests/test_prepare_assets.py`
- Create: `launch-app/assets/title.png`
- Create: `launch-app/assets/minister.png`
- Create: `launch-app/assets/start-button.png`
- Create: `launch-app/assets/background-sides.png`
- Create: `launch-app/assets/background-medallion.png`
- Create: `launch-app/assets/statistics.png`
- Create: `launch-app/assets/icon-180.png`
- Create: `launch-app/assets/icon-192.png`
- Create: `launch-app/assets/icon-512.png`

**Interfaces:**
- Consumes: Source PDFs under the `--source-dir` path.
- Produces: `prepare_assets(source_dir: Path, output_dir: Path) -> None` and the nine exact runtime PNG filenames listed above.

- [ ] **Step 1: Write the failing asset-pipeline tests**

```python
# tests/test_prepare_assets.py
import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_assets import OUTPUT_NAMES, prepare_assets, trim_transparent


class PrepareAssetsTests(unittest.TestCase):
    def test_trim_transparent_preserves_padding(self):
        image = Image.new("RGBA", (40, 40), (255, 255, 255, 0))
        image.paste((20, 80, 40, 255), (15, 15, 25, 25))
        trimmed = trim_transparent(image, padding=3)
        self.assertEqual(trimmed.size, (16, 16))

    def test_generates_complete_optimized_asset_set(self):
        source_dir = Path(os.environ["SOURCE_PDF_DIR"])
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            prepare_assets(source_dir, output_dir)
            self.assertEqual(
                {path.name for path in output_dir.glob("*.png")},
                set(OUTPUT_NAMES),
            )
            minimum_sizes = {
                "title.png": (1100, 500),
                "minister.png": (1000, 450),
                "start-button.png": (900, 900),
                "background-sides.png": (2000, 1100),
                "background-medallion.png": (1200, 1200),
                "statistics.png": (1500, 1500),
            }
            for name, minimum in minimum_sizes.items():
                with Image.open(output_dir / name) as image:
                    self.assertGreaterEqual(image.width, minimum[0], name)
                    self.assertGreaterEqual(image.height, minimum[1], name)
                    self.assertIn(image.mode, {"RGB", "RGBA"}, name)
            for size in (180, 192, 512):
                with Image.open(output_dir / f"icon-{size}.png") as icon:
                    self.assertEqual(icon.size, (size, size))
            total = sum(path.stat().st_size for path in output_dir.glob("*.png"))
            self.assertLess(total, 10 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm the missing module failure**

Run:

```powershell
$env:SOURCE_PDF_DIR='C:\Users\Admin\Downloads\PDF'
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tests/test_prepare_assets.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'prepare_assets'`.

- [ ] **Step 3: Implement the asset renderer**

```python
# scripts/prepare_assets.py
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageOps


@dataclass(frozen=True)
class AssetSpec:
    source: str
    output: str
    scale: float
    trim: bool = True


ASSETS = (
    AssetSpec("Asset 3.pdf", "title.png", 4.0),
    AssetSpec("Asset 2.pdf", "minister.png", 4.0),
    AssetSpec("Asset 1.pdf", "start-button.png", 3.0),
    AssetSpec("Asset 4.pdf", "background-sides.png", 1.125, False),
    AssetSpec("Asset 5.pdf", "background-medallion.png", 1.5),
    AssetSpec("Asset 1022.pdf", "statistics.png", 2.5),
)

OUTPUT_NAMES = tuple(spec.output for spec in ASSETS) + (
    "icon-180.png",
    "icon-192.png",
    "icon-512.png",
)


def render_pdf(path: Path, scale: float, page_index: int = 0) -> Image.Image:
    document = pdfium.PdfDocument(str(path))
    page = document[page_index]
    bitmap = page.render(
        scale=scale,
        fill_color=(255, 255, 255, 0),
        rev_byteorder=True,
    )
    return bitmap.to_pil().convert("RGBA")


def trim_transparent(image: Image.Image, padding: int = 24) -> Image.Image:
    alpha = image.getchannel("A")
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError("Rendered artwork is fully transparent")
    left, top, right, bottom = bounds
    return image.crop(
        (
            max(0, left - padding),
            max(0, top - padding),
            min(image.width, right + padding),
            min(image.height, bottom + padding),
        )
    )


def save_png(image: Image.Image, path: Path) -> None:
    image.save(path, format="PNG", optimize=True, compress_level=9)


def create_icons(master_pdf: Path, output_dir: Path) -> None:
    master_page = render_pdf(master_pdf, scale=1.0, page_index=1).convert("RGB")
    logo_crop = master_page.crop((720, 245, 1200, 725))
    square = ImageOps.fit(
        logo_crop,
        (512, 512),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    for size in (180, 192, 512):
        icon = square.resize((size, size), Image.Resampling.LANCZOS)
        save_png(icon, output_dir / f"icon-{size}.png")


def prepare_assets(source_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for spec in ASSETS:
        source = source_dir / spec.source
        if not source.is_file():
            raise FileNotFoundError(source)
        image = render_pdf(source, spec.scale)
        if spec.trim:
            image = trim_transparent(image)
        save_png(image, output_dir / spec.output)
    create_icons(source_dir / "تطبيق التدشين.pdf", output_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "launch-app" / "assets",
    )
    arguments = parser.parse_args()
    prepare_assets(arguments.source_dir, arguments.output_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Generate the PNGs and run the passing tests**

Run:

```powershell
$python='C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python scripts/prepare_assets.py --source-dir 'C:\Users\Admin\Downloads\PDF'
$env:SOURCE_PDF_DIR='C:\Users\Admin\Downloads\PDF'
& $python tests/test_prepare_assets.py -v
```

Expected: two tests PASS and nine optimized PNGs exist in `launch-app/assets/`.

- [ ] **Step 5: Visually inspect all generated PNGs**

Use the local image viewer at original detail for every generated artwork PNG and the 512 icon. Confirm transparent margins, shadows, calligraphy, and statistics are intact; rerun the renderer only if the visual inspection shows clipping or an incorrect icon crop.

- [ ] **Step 6: Commit the asset pipeline and generated assets**

```powershell
git add -- scripts/prepare_assets.py tests/test_prepare_assets.py launch-app/assets
git commit -m "feat: prepare launch artwork assets"
```

Expected: one commit containing the deterministic source-to-runtime artwork pipeline and its outputs.

---

### Task 2: Static 4:3 Application Shell

**Files:**
- Create: `tests/test_static_app.py`
- Create: `launch-app/index.html`
- Create: `launch-app/style.css`
- Create: `launch-app/manifest.json`

**Interfaces:**
- Consumes: The exact PNG filenames produced by Task 1.
- Produces: DOM IDs `start-button`, `screen-start`, and `screen-statistics`; root state classes `app-loading`, `app-ready`, `is-launching`, and `is-launched`; and a manifest consumed by `index.html` and `sw.js`.

- [ ] **Step 1: Write the failing static-app contract tests**

```python
# tests/test_static_app.py
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "launch-app"


class StaticAppTests(unittest.TestCase):
    def test_manifest_is_arabic_standalone_landscape(self):
        manifest = json.loads((APP / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["orientation"], "landscape")
        self.assertEqual(manifest["theme_color"], "#1a4d2e")
        self.assertEqual(manifest["background_color"], "#ffffff")
        self.assertEqual([icon["sizes"] for icon in manifest["icons"]], ["192x192", "512x512"])

    def test_html_has_exactly_two_screens_and_one_start_button(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r'class="screen ', html)), 2)
        self.assertEqual(len(re.findall(r'<button\b', html)), 1)
        self.assertIn('id="start-button"', html)
        self.assertIn('id="screen-start"', html)
        self.assertIn('id="screen-statistics"', html)
        self.assertIn('apple-mobile-web-app-capable" content="yes', html)
        self.assertIn('apple-mobile-web-app-status-bar-style" content="black-translucent', html)
        self.assertIn('rel="apple-touch-icon" href="assets/icon-180.png"', html)
        self.assertIn('maximum-scale=1, user-scalable=no', html)

    def test_css_contains_hardening_and_gpu_transition_contracts(self):
        css = (APP / "style.css").read_text(encoding="utf-8")
        for contract in (
            "touch-action: manipulation",
            "overscroll-behavior: none",
            "-webkit-user-select: none",
            "-webkit-touch-callout: none",
            "overflow: hidden",
            "transform:",
            "opacity:",
            "prefers-reduced-motion: reduce",
            "width: clamp(300px",
        ):
            self.assertIn(contract, css)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm the missing-file failure**

Run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tests/test_static_app.py -v
```

Expected: FAIL because `launch-app/manifest.json`, `index.html`, and `style.css` do not exist.

- [ ] **Step 3: Create the web app manifest**

```json
{
  "name": "تطبيق تدشين مسابقة الملك عبدالعزيز الدولية",
  "short_name": "تطبيق التدشين",
  "lang": "ar",
  "dir": "rtl",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "orientation": "landscape",
  "theme_color": "#1a4d2e",
  "background_color": "#ffffff",
  "icons": [
    {
      "src": "assets/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "assets/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

- [ ] **Step 4: Create the semantic two-screen HTML shell**

```html
<!doctype html>
<html lang="ar" dir="rtl" class="app-loading">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
    <meta name="theme-color" content="#1a4d2e">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="تطبيق التدشين">
    <title>تطبيق تدشين مسابقة الملك عبدالعزيز الدولية</title>
    <link rel="manifest" href="manifest.json">
    <link rel="apple-touch-icon" href="assets/icon-180.png">
    <link rel="preload" as="image" href="assets/background-sides.png">
    <link rel="preload" as="image" href="assets/background-medallion.png">
    <link rel="preload" as="image" href="assets/title.png">
    <link rel="preload" as="image" href="assets/minister.png">
    <link rel="preload" as="image" href="assets/start-button.png">
    <link rel="preload" as="image" href="assets/statistics.png">
    <link rel="stylesheet" href="style.css">
    <script src="app.js" defer></script>
  </head>
  <body>
    <main class="stage" aria-label="تطبيق التدشين">
      <img class="background background-sides" src="assets/background-sides.png" alt="" draggable="false">
      <img class="background background-medallion" src="assets/background-medallion.png" alt="" draggable="false">

      <section id="screen-start" class="screen screen-start" aria-hidden="false">
        <img class="title-art" src="assets/title.png" alt="تدشين المرحلة الجديدة لمسابقة الملك عبدالعزيز الدولية لحفظ القرآن الكريم وتلاوته وتفسيره" draggable="false">
        <img class="minister-art" src="assets/minister.png" alt="بإشراف ومتابعة معالي الشيخ الدكتور عبداللطيف بن عبدالعزيز آل الشيخ" draggable="false">
        <button id="start-button" class="start-button" type="button" aria-label="ابدأ" disabled>
          <img src="assets/start-button.png" alt="" draggable="false">
        </button>
      </section>

      <section id="screen-statistics" class="screen screen-statistics" aria-hidden="true">
        <img class="statistics-art" src="assets/statistics.png" alt="إحصاءات الدورة السادسة والأربعين: 133 دولة و547 مشاركا ومشاركة" draggable="false">
      </section>

      <div class="gold-glow" aria-hidden="true"></div>
    </main>
  </body>
</html>
```

- [ ] **Step 5: Implement the fixed 4:3 layout and visual states**

```css
:root {
  color-scheme: light;
  --green: #1a4d2e;
  --gold: #c9a646;
  --transition-duration: 1900ms;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body {
  width: 100%;
  height: 100%;
  margin: 0;
  overflow: hidden;
  overscroll-behavior: none;
  background: #ffffff;
  touch-action: manipulation;
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
  cursor: none;
}

body {
  display: grid;
  place-items: center;
}

button,
img {
  -webkit-tap-highlight-color: transparent;
}

.stage {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  isolation: isolate;
  background: #ffffff;
}

@supports (height: 100dvh) {
  .stage {
    height: 100dvh;
  }
}

.background {
  position: absolute;
  z-index: -2;
  pointer-events: none;
}

.background-sides {
  top: 50%;
  left: 0;
  width: 100%;
  height: auto;
  transform: translateY(-50%);
  opacity: 0.88;
}

.background-medallion {
  top: 50%;
  left: 50%;
  width: min(64vmin, 620px);
  height: min(64vmin, 620px);
  transform: translate(-50%, -50%);
  opacity: 0.48;
}

.screen {
  position: absolute;
  inset: 0;
  padding:
    max(20px, env(safe-area-inset-top))
    max(36px, env(safe-area-inset-right))
    max(24px, env(safe-area-inset-bottom))
    max(36px, env(safe-area-inset-left));
}

.screen-start {
  z-index: 2;
  display: grid;
  grid-template-rows: 31% 25% 44%;
  justify-items: center;
  align-items: center;
}

.title-art,
.minister-art,
.statistics-art,
.start-button img {
  display: block;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  pointer-events: none;
}

.title-art {
  align-self: end;
  width: min(46vw, 470px);
  max-height: 215px;
}

.minister-art {
  width: min(41vw, 420px);
  max-height: 190px;
}

.start-button {
  align-self: start;
  width: clamp(300px, 30vw, 330px);
  aspect-ratio: 1;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  outline: 0;
  background: transparent;
  color: transparent;
  appearance: none;
  touch-action: manipulation;
  transform: translateZ(0) scale(1);
  transition: transform 100ms ease-out, opacity 180ms ease-out;
}

.start-button:active:not(:disabled) {
  transform: translateZ(0) scale(0.96);
}

.start-button:focus,
.start-button:focus-visible {
  outline: 0;
}

.start-button:disabled {
  opacity: 0.92;
}

.app-loading .start-button {
  pointer-events: none;
}

.app-ready .start-button:not(:disabled) {
  pointer-events: auto;
}

.screen-statistics {
  z-index: 1;
  display: grid;
  place-items: center;
  visibility: hidden;
  opacity: 0;
  transform: translate3d(0, 24px, 0);
}

.statistics-art {
  width: min(76vw, 690px);
  max-height: min(84vh, 680px);
}

.gold-glow {
  position: absolute;
  z-index: 4;
  left: 50%;
  top: 72%;
  width: 18vmin;
  aspect-ratio: 1;
  border-radius: 50%;
  pointer-events: none;
  background: radial-gradient(circle, rgba(255, 243, 183, 0.96) 0%, rgba(213, 171, 60, 0.68) 32%, rgba(213, 171, 60, 0) 72%);
  opacity: 0;
  transform: translate3d(-50%, -50%, 0) scale(0.2);
}

.is-launching .start-button {
  animation: button-press 140ms ease-out both;
}

.is-launching .gold-glow {
  animation: glow-expand 1400ms cubic-bezier(0.22, 0.8, 0.24, 1) both;
}

.is-launching .screen-start {
  animation: start-exit 900ms 180ms ease-in both;
}

.is-launching .screen-statistics {
  visibility: visible;
  animation: statistics-enter 850ms 820ms cubic-bezier(0.2, 0.8, 0.25, 1) both;
}

.is-launched .screen-start {
  visibility: hidden;
  opacity: 0;
  pointer-events: none;
}

.is-launched .screen-statistics {
  visibility: visible;
  opacity: 1;
  transform: translate3d(0, 0, 0);
}

@keyframes button-press {
  to { transform: translateZ(0) scale(0.96); }
}

@keyframes glow-expand {
  0% { opacity: 0; transform: translate3d(-50%, -50%, 0) scale(0.2); }
  20% { opacity: 1; }
  72% { opacity: 0.78; }
  100% { opacity: 0; transform: translate3d(-50%, -50%, 0) scale(14); }
}

@keyframes start-exit {
  to { opacity: 0; transform: translate3d(0, -12px, 0); }
}

@keyframes statistics-enter {
  from { opacity: 0; transform: translate3d(0, 24px, 0); }
  to { opacity: 1; transform: translate3d(0, 0, 0); }
}

@media (prefers-reduced-motion: reduce) {
  :root { --transition-duration: 350ms; }
  .is-launching .start-button,
  .is-launching .gold-glow { animation: none; }
  .is-launching .screen-start { animation: start-exit 250ms ease-out both; }
  .is-launching .screen-statistics { animation: statistics-enter 300ms 100ms ease-out both; }
}
```

- [ ] **Step 6: Run the static contract tests**

Run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tests/test_static_app.py -v
```

Expected: three tests PASS.

- [ ] **Step 7: Commit the static shell**

```powershell
git add -- tests/test_static_app.py launch-app/index.html launch-app/style.css launch-app/manifest.json
git commit -m "feat: build four-three launch screens"
```

---

### Task 3: One-Shot Launch Controller

**Files:**
- Create: `tests/test_app_js.mjs`
- Create: `launch-app/app.js`

**Interfaces:**
- Consumes: DOM IDs and root state classes from Task 2.
- Produces: image-ready enabling, a single accepted launch, `aria-hidden` state updates, transition completion after 1900 ms, and non-blocking `./sw.js` registration.

- [ ] **Step 1: Write the failing JavaScript behavior test**

```javascript
// tests/test_app_js.mjs
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
```

- [ ] **Step 2: Run the test and confirm the missing-file failure**

Run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests/test_app_js.mjs
```

Expected: FAIL with `ENOENT` for `launch-app/app.js`.

- [ ] **Step 3: Implement the controller**

```javascript
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
```

- [ ] **Step 4: Run the controller test**

Run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests/test_app_js.mjs
```

Expected: one test PASS.

- [ ] **Step 5: Commit the launch controller**

```powershell
git add -- tests/test_app_js.mjs launch-app/app.js
git commit -m "feat: add one-shot launch transition"
```

---

### Task 4: Complete Offline PWA Cache

**Files:**
- Create: `tests/test_sw.mjs`
- Create: `launch-app/sw.js`

**Interfaces:**
- Consumes: Every runtime path produced in Tasks 1-3.
- Produces: Cache `quran-launch-v1`, complete install-time precaching, old-cache cleanup scoped to `quran-launch-`, cached navigation fallback, and cache-first same-origin GET handling.

- [ ] **Step 1: Write the failing service-worker contract test**

```javascript
// tests/test_sw.mjs
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
```

- [ ] **Step 2: Run the test and confirm the missing-file failure**

Run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests/test_sw.mjs
```

Expected: FAIL with `ENOENT` for `launch-app/sw.js`.

- [ ] **Step 3: Implement the cache-first service worker**

```javascript
const CACHE_PREFIX = "quran-launch-";
const CACHE_NAME = `${CACHE_PREFIX}v1`;
const PRECACHE_URLS = Object.freeze([
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
]);

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") {
    return;
  }

  event.respondWith(
    caches.match(request, { ignoreSearch: true }).then((cached) => {
      if (cached) {
        return cached;
      }
      if (request.mode === "navigate") {
        return caches.match("./index.html");
      }
      return fetch(request);
    }),
  );
});
```

- [ ] **Step 4: Run the service-worker test**

Run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests/test_sw.mjs
```

Expected: one test PASS.

- [ ] **Step 5: Commit the offline implementation**

```powershell
git add -- tests/test_sw.mjs launch-app/sw.js
git commit -m "feat: precache launch app for offline use"
```

---

### Task 5: Ceremony Verification and Operator Handoff

**Files:**
- Create: `tests/test_bundle.py`
- Create: `launch-app/README.md`
- Remove after verification: `tmp/pdfs/`
- Create during verification only: `tmp/qa/screen-start-1080x810.png`
- Create during verification only: `tmp/qa/screen-statistics-1080x810.png`
- Create during verification only: `tmp/qa/screen-start-1024x768.png`
- Create during verification only: `tmp/qa/screen-statistics-1024x768.png`

**Interfaces:**
- Consumes: Complete `launch-app/` runtime from Tasks 1-4.
- Produces: A verified sub-10 MB offline bundle and operator instructions that distinguish desktop preview from the HTTPS installation path required for iPad service-worker use.

- [ ] **Step 1: Write the failing final bundle audit**

```python
# tests/test_bundle.py
import re
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "launch-app"


class BundleTests(unittest.TestCase):
    def test_all_local_document_references_exist(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        references = re.findall(r'(?:src|href)="([^"]+)"', html)
        for reference in references:
            self.assertNotIn("://", reference)
            self.assertTrue((APP / reference).is_file(), reference)

    def test_png_files_are_valid(self):
        pngs = sorted((APP / "assets").glob("*.png"))
        self.assertEqual(len(pngs), 9)
        for path in pngs:
            with Image.open(path) as image:
                image.verify()

    def test_runtime_has_no_remote_dependencies_and_is_under_budget(self):
        runtime_files = [
            APP / "index.html",
            APP / "style.css",
            APP / "app.js",
            APP / "sw.js",
            APP / "manifest.json",
        ]
        for path in runtime_files:
            content = path.read_text(encoding="utf-8")
            self.assertNotRegex(content, r'https?://')
        total = sum(path.stat().st_size for path in APP.rglob("*") if path.is_file())
        self.assertLess(total, 10 * 1024 * 1024)

    def test_operator_readme_contains_install_and_offline_rehearsal(self):
        readme = (APP / "README.md").read_text(encoding="utf-8")
        self.assertIn("HTTPS", readme)
        self.assertIn("إضافة إلى الشاشة الرئيسية", readme)
        self.assertIn("وضع الطيران", readme)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the audit and confirm the missing README/bundle gap**

Run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tests/test_bundle.py -v
```

Expected: the three runtime checks PASS and the README test FAILS because `launch-app/README.md` has not been created yet.

- [ ] **Step 3: Write the operator README**

````markdown
# تطبيق التدشين

تطبيق ثابت من شاشتين لتدشين المرحلة الجديدة من مسابقة الملك عبدالعزيز الدولية، مصمم لجهاز iPad من الجيل التاسع بالوضع الأفقي.

## المعاينة على الكمبيوتر

من مجلد المشروع شغّل:

```powershell
py -3 -m http.server 8080 --directory launch-app
```

ثم افتح `http://localhost:8080`. هذه الطريقة مناسبة للمعاينة على الكمبيوتر فقط.

## التثبيت على iPad

1. ارفع محتويات مجلد `launch-app` إلى استضافة ثابتة تعمل عبر HTTPS، أو استخدم خادما محليا موثوقا يعمل عبر HTTPS.
2. افتح الرابط في Safari والجهاز بالوضع الأفقي.
3. من زر المشاركة اختر **إضافة إلى الشاشة الرئيسية**.
4. افتح التطبيق من أيقونته مرة واحدة أثناء الاتصال بالإنترنت، وانتظر ظهور شاشة البداية كاملة.

## اختبار ما قبل الحفل

1. أغلق التطبيق بعد فتحه مرة واحدة بالاتصال بالإنترنت.
2. فعّل وضع الطيران وأوقف Wi-Fi.
3. افتح التطبيق من أيقونة الشاشة الرئيسية.
4. تأكد من ظهور شاشة البداية فورا.
5. اضغط **ابدأ** مرة واحدة وتأكد من ظهور شاشة الإحصاءات بعد الانتقال.
6. أغلق التطبيق وكرر الاختبار كاملا مرة ثانية وهو دون اتصال.

لا تمسح بيانات Safari، ولا تغير ملفات الاستضافة بعد نجاح الاختبار النهائي دون إعادة فتح التطبيق بالاتصال وإعادة اختبار وضع الطيران.
````

- [ ] **Step 4: Run all automated verification from a clean command prompt**

Run:

```powershell
$python='C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$node='C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$env:SOURCE_PDF_DIR='C:\Users\Admin\Downloads\PDF'
& $python -m unittest discover -s tests -p 'test_*.py' -v
& $node --test tests/test_app_js.mjs tests/test_sw.mjs
git diff --check
```

Expected: all Python and Node tests PASS and `git diff --check` prints no errors.

- [ ] **Step 5: Verify the live app at both 4:3 viewports**

Start a hidden local server:

```powershell
$python='C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$server=Start-Process -FilePath $python -ArgumentList '-m','http.server','4173','--directory','C:\Users\Admin\Documents\Tadsheen\launch-app' -WindowStyle Hidden -PassThru
$server.Id
```

Using a real browser, perform this exact sequence at 1080 x 810 and again at 1024 x 768:

1. Open `http://localhost:4173/` and wait until the Start button is enabled.
2. Capture Screen 1.
3. Confirm `document.documentElement.scrollWidth === innerWidth` and `document.documentElement.scrollHeight === innerHeight`.
4. Confirm the Start button's rendered width is at least 300 pixels at 1080 x 810.
5. Activate Start twice rapidly.
6. Wait 2100 ms and confirm the root has `is-launched`, not `is-launching`.
7. Confirm the statistics image is visible and fully inside the viewport.
8. Capture Screen 2.
9. Check the browser console for missing-resource, JavaScript, manifest, and service-worker errors.

Inspect all four screenshots at original detail. Reject clipping, overlap, unintended white rectangles, blurry calligraphy, cropped shadows, or statistics too small to read.

- [ ] **Step 6: Prove the installed cache works without the server**

With the browser still on the app, reload once so the active service worker controls the page. Confirm `navigator.serviceWorker.controller` is non-null and the cache contains all entries. Then stop only the recorded local server process:

```powershell
Stop-Process -Id $server.Id
```

Reload the existing app URL. Expected: Screen 1 renders completely, Start transitions to Screen 2, and the network panel shows the runtime resources served by the service worker rather than failed network requests.

- [ ] **Step 7: Remove intermediate PDF renders and rerun the final status checks**

Resolve the exact intermediate directory, confirm it is inside this repository, then remove only `C:\Users\Admin\Documents\Tadsheen\tmp\pdfs`. Keep `tmp/qa/` until visual review is complete.

Run:

```powershell
git status --short
git diff --check
```

Expected: no intermediate PDF renders remain and only the intended Task 5 files are uncommitted.

- [ ] **Step 8: Commit the verified handoff**

```powershell
git add -- tests/test_bundle.py launch-app/README.md
git commit -m "docs: add ceremony installation runbook"
```

- [ ] **Step 9: Run the completion gate once more**

Run:

```powershell
$python='C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$node='C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$env:SOURCE_PDF_DIR='C:\Users\Admin\Downloads\PDF'
& $python -m unittest discover -s tests -p 'test_*.py' -v
& $node --test tests/test_app_js.mjs tests/test_sw.mjs
git status --short --branch
```

Expected: all tests PASS. The working tree may contain only reviewed `tmp/qa/` screenshots; source and deliverable files are committed.
