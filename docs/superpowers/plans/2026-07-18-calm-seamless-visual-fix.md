# Calm Seamless Ceremony Visual Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the white edge and distracting gold effects, integrate the exact 16:9 PDF pages into the 4:3 iPad viewport, and publish the approved quiet crossfade treatment.

**Architecture:** Keep the existing dependency-free two-screen PWA and four-state JavaScript controller. CSS owns the one-pixel foreground overscan, page-derived ambient extension, quiet Start outline, and opacity-only transitions; the asset pipeline and service worker remove the obsolete shimmer masks.

**Tech Stack:** HTML5, CSS, vanilla JavaScript, service workers, Python `unittest`/Pillow, Node.js built-in test runner.

## Global Constraints

- The supplied two-page PDF remains the visual source of truth; do not recompose or generate replacement artwork.
- Target iPad landscape viewports are exactly 1080 x 810 and 1024 x 768.
- The sharp page remains 16:9 and clips only approximately two, at most three, source pixels per side.
- Forward crossfade is 700ms; reverse crossfade is 600ms.
- Start hit area remains at least 300 x 300 CSS pixels.
- Preserve the hidden three-tap return window of 900ms and all kiosk hardening.
- No external runtime dependencies; total shipped bundle remains below 10 MiB and works offline.

---

### Task 1: Replace the Old Visual Contracts with Failing Tests

**Files:**
- Modify: `tests/test_static_app.py`
- Modify: `tests/test_app_js.mjs`
- Modify: `tests/test_bundle.py`
- Modify: `tests/test_prepare_assets.py`
- Modify: `tests/test_sw.mjs`

**Interfaces:**
- Consumes: the current static bundle under `launch-app/`.
- Produces: executable contracts for the approved markup, CSS motion, 700ms state timing, mask-free inventory, and cache `v3`.

- [ ] **Step 1: Update the static markup and CSS assertions**

Replace mask/orbit/halo/glow expectations with these contracts:

```python
self.assertNotIn("gold-mask", html)
self.assertNotIn("gold-shimmer", html)
self.assertNotIn("start-orbit", html)
self.assertNotIn("start-halo", html)
self.assertNotIn("gold-glow", html)
self.assertRegex(
    button.group("body"),
    r'^\s*<span class="start-feedback">\s*'
    r'<span class="start-outline" aria-hidden="true"></span>\s*'
    r'</span>\s*$',
)
for contract in (
    "--transition-duration: 700ms",
    "--return-duration: 600ms",
    "left: -1px",
    "width: calc(100vw + 2px)",
    "filter: blur(12px) brightness(0.72) saturate(0.94)",
    "animation: outline-breathe 3.2s ease-in-out infinite",
):
    self.assertIn(contract, css)
for removed in (
    "gold-mask", "gold-shimmer", "start-orbit", "start-halo",
    "gold-glow", "ring-rotate", "halo-pulse", "shimmer-sweep",
    "glow-expand", "box-shadow:",
):
    self.assertNotIn(removed, css)
self.assertNotIn("transform:", css_block(css, "@keyframes outline-breathe"))
```

Change the press assertion to `transform: scale(0.98);` and retain the checks proving that only `.start-feedback` scales.

- [ ] **Step 2: Update JavaScript timing expectations**

Replace every active `1900`-millisecond timer expectation in `tests/test_app_js.mjs` with `700`, including `loadLaunchedAppHarness()` and replay assertions. Keep every readiness, double-activation, three-tap, slow-tap, and event-blocking assertion unchanged.

- [ ] **Step 3: Update bundle, generator, and service-worker expectations**

Set the exact asset inventory to:

```python
EXPECTED_ASSETS = {
    "icon-180.png",
    "icon-192.png",
    "icon-512.png",
    "page-1.png",
    "page-2.png",
}
```

Rename the generator test to `test_generates_pdf_faithful_pages_and_icons`, remove all mask assertions, and assert `set(OUTPUT_NAMES)` equals those five files. In `tests/test_sw.mjs`, require ``CACHE_NAME = `${CACHE_PREFIX}v3` `` while retaining exact physical-inventory and forced-fresh-request checks.

- [ ] **Step 4: Run the tests and confirm the old implementation fails**

Run:

```powershell
$env:SOURCE_MASTER_PDF='C:\Users\Admin\Downloads\تطبيق التدشين (2).pdf'
py -3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_app_js.mjs tests/test_sw.mjs
```

Expected: failures mention old shimmer/mask markup, 1900ms timing, mask assets, old generator outputs, and cache `v2`.

---

### Task 2: Implement the Mask-Free Seamless Runtime

**Files:**
- Modify: `scripts/prepare_assets.py`
- Delete: `launch-app/assets/page-1-gold-mask.png`
- Delete: `launch-app/assets/page-2-gold-mask.png`
- Modify: `launch-app/index.html`
- Modify: `launch-app/style.css`
- Modify: `launch-app/app.js`

**Interfaces:**
- Consumes: `assets/page-1.png` and `assets/page-2.png` at 2160 x 1215.
- Produces: two screens using `.page-backdrop`, `.page-frame`, `.page-art`, `.start-feedback`, and `.start-outline`; JavaScript finalizes the forward state after 700ms.

- [ ] **Step 1: Simplify the deterministic asset generator**

Use only `Image` and `ImageOps` from Pillow, remove `GOLD_REGIONS` and `create_gold_mask()`, and set:

```python
OUTPUT_NAMES = (
    "page-1.png",
    "page-2.png",
    "icon-180.png",
    "icon-192.png",
    "icon-512.png",
)

def prepare_assets(master_pdf: Path, output_dir: Path) -> None:
    if not master_pdf.is_file():
        raise FileNotFoundError(master_pdf)
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = [render_pdf(master_pdf, PAGE_SCALE, index) for index in (0, 1)]
    for number, page in enumerate(pages, start=1):
        save_png(page, output_dir / f"page-{number}.png")
    create_icons(pages[1], output_dir)
```

Delete the two obsolete mask PNGs from `launch-app/assets/`.

- [ ] **Step 2: Simplify runtime markup**

Remove both mask preload links, both `.gold-shimmer` elements, and `.gold-glow`. The Start button body becomes:

```html
<span class="start-feedback">
  <span class="start-outline" aria-hidden="true"></span>
</span>
```

Keep the two backdrop/page image pairs, disabled Start button, accessibility labels, image preload links, PWA metadata, and relative paths unchanged.

- [ ] **Step 3: Implement the approved layout and quiet motion**

Set `--transition-duration: 700ms` and retain `--return-duration: 600ms`. Replace the ambient and sharp-frame rules with:

```css
.page-backdrop {
  position: absolute;
  inset: -9%;
  width: 118%;
  height: 118%;
  object-fit: cover;
  filter: blur(12px) brightness(0.72) saturate(0.94);
  transform: translateZ(0) scale(1.05);
  opacity: 1;
  pointer-events: none;
}

.page-frame {
  position: absolute;
  left: -1px;
  top: 50%;
  width: calc(100vw + 2px);
  aspect-ratio: 16 / 9;
  overflow: hidden;
  transform: translate3d(0, -50%, 0);
}
```

Keep `.page-art` unanimated and filling the 16:9 frame. Replace decorative motion with:

```css
.start-outline {
  position: absolute;
  left: 50%;
  top: 50%;
  width: clamp(176px, 17.8vw, 208px);
  aspect-ratio: 1;
  border: 2px solid rgba(234, 207, 119, 0.68);
  border-radius: 50%;
  transform: translate3d(-50%, -50%, 0);
  opacity: 0.28;
  animation: outline-breathe 3.2s ease-in-out infinite;
}

.start-button:active:not(:disabled) .start-feedback {
  transform: scale(0.98);
}

@keyframes outline-breathe {
  0%, 100% { opacity: 0.28; }
  50% { opacity: 0.74; }
}
```

Use concurrent opacity-only `start-exit` and `ceremony-enter` animations for the full `var(--transition-duration)`, with no delays. Keep reverse animations at `var(--return-duration)`. Under reduced motion, disable only `outline-breathe` and set outline opacity to `0.5`; do not alter transition durations.

- [ ] **Step 4: Synchronize the state controller**

Change only:

```javascript
const FORWARD_DURATION = 700;
```

Keep `RETURN_DURATION = 600`, `RETURN_WINDOW = 900`, readiness, state guards, replay, event blockers, and service-worker registration unchanged.

- [ ] **Step 5: Run focused tests**

Run the same Python and Node commands from Task 1.

Expected: all Python and Node tests pass.

---

### Task 3: Ship Cache v3 and Validate the Published Experience

**Files:**
- Modify: `launch-app/sw.js`
- Modify: `launch-app/README.md`

**Interfaces:**
- Consumes: the exact final physical bundle inventory.
- Produces: cache `quran-launch-v3`, updated operator instructions, verified local/offline and public behavior.

- [ ] **Step 1: Update the offline inventory**

Set:

```javascript
const CACHE_NAME = `${CACHE_PREFIX}v3`;
```

Remove the two gold-mask URLs from `PRECACHE_URLS`. Keep forced-fresh `Request` objects, `skipWaiting()`, old-prefix cleanup, `clients.claim()`, same-origin cache-first fetches, and navigation fallback unchanged.

- [ ] **Step 2: Update the operator note**

Change the README release warning from `v2`/`v1` to `v3`/`v2`, telling the operator to open the app once online before the offline rehearsal. Do not change the public URL or iPad installation steps.

- [ ] **Step 3: Run the complete automated suite**

Run:

```powershell
$env:SOURCE_MASTER_PDF='C:\Users\Admin\Downloads\تطبيق التدشين (2).pdf'
py -3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_app_js.mjs tests/test_sw.mjs
git diff --check
```

Expected: all tests pass and `git diff --check` produces no output.

- [ ] **Step 4: Validate both target browser viewports**

Serve `launch-app/` locally and verify at 1080 x 810 and 1024 x 768:

- stage dimensions equal viewport dimensions and `scrollWidth === innerWidth`, `scrollHeight === innerHeight`;
- page frame left is `-1px`, width is viewport width plus 2px, and width/height ratio is 16:9;
- Start hit box is at least 300 x 300px;
- `.page-art` bounding box does not move during idle or transition;
- edge-column screenshots contain no contiguous RGB >= 235 run longer than 25% of height;
- Start reaches Screen 2 after 700ms, three fast taps return after 600ms, and replay works;
- no console errors or failed runtime requests occur.

Stop the server after the page is service-worker controlled and verify an offline reload still renders Screen 1 and completes the full forward/return/replay flow.

- [ ] **Step 5: Commit, push, and verify GitHub Pages**

Commit the tested runtime and plan, push `codex/launch-app`, update public `main`, and verify:

```text
https://corexsol.github.io/quran-competition-launch-app/launch-app/
```

Expected: a clean browser profile loads cache `quran-launch-v3`, all runtime requests return successfully, and the stopped-network/offline reload works after the first online load.
