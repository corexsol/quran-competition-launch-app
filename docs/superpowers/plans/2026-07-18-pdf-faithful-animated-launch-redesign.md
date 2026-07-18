# PDF-Faithful Animated Launch Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the reconstructed ceremony screens with exact optimized renders of the supplied two-page PDF, presented on a blurred full-bleed duplicate background, with a living Start overlay, hardened iPad interaction, three-tap return, and reliable offline updating.

**Architecture:** Keep the app as a two-screen, dependency-free static PWA. A deterministic Python/Pillow pipeline renders the Illustrator PDF into two 2160 x 1215 foreground pages, two lightweight source-derived shimmer masks, and three icons. HTML and CSS layer each exact page over a blurred `cover` duplicate; JavaScript owns a four-state interaction controller (`start`, `launching`, `ceremony`, `returning`) and the service worker owns a versioned, complete cache.

**Tech Stack:** HTML5, CSS3, vanilla JavaScript, Service Worker API, Python 3, pypdfium2, Pillow, Node's built-in test runner, Python unittest, headless Chrome/CDP for acceptance.

## Global Constraints

- The visual source of truth is `C:\Users\Admin\Downloads\تطبيق التدشين (2).pdf`, exactly two 1920 x 1080 point pages.
- Preserve every supplied portrait, logo, word, border, color, and relative position; invent no content or claims.
- Target iPad 9th generation Safari in landscape at 4:3, verifying 1080 x 810 and 1024 x 768 CSS viewports.
- Keep each sharp 16:9 page fully visible with no cropping; fill the 4:3 remainder with a blurred, darkened `cover` duplicate of the same page.
- Keep exactly two screens, one visible Start control, no routing, no backend, no framework, no analytics, and no external runtime dependency.
- Keep `ابدأ` stationary; animate only source-aligned overlay rings, halo, glow, and shimmer.
- Three pointer releases within 900 milliseconds on Screen 2 return to Screen 1; one or two taps do nothing.
- Disable scrolling, overscroll, selection, callouts, dragging, context menus, pinch zoom, and double-tap zoom while preserving Start activation.
- Keep the complete `launch-app/` payload below 10 MiB and precache every physical file plus `./`.
- Continue to work at `https://corexsol.github.io/quran-competition-launch-app/launch-app/` and fully offline after one online update.
- Use test-first RED -> GREEN cycles for every production behavior change.

---

### Task 1: Deterministic PDF Page and Mask Asset Pipeline

**Files:**
- Modify: `scripts/prepare_assets.py`
- Modify: `tests/test_prepare_assets.py`
- Replace: `launch-app/assets/title.png`
- Replace: `launch-app/assets/minister.png`
- Replace: `launch-app/assets/start-button.png`
- Replace: `launch-app/assets/background-sides.png`
- Replace: `launch-app/assets/background-medallion.png`
- Replace: `launch-app/assets/statistics.png`
- Create: `launch-app/assets/page-1.png`
- Create: `launch-app/assets/page-2.png`
- Create: `launch-app/assets/page-1-gold-mask.png`
- Create: `launch-app/assets/page-2-gold-mask.png`
- Regenerate: `launch-app/assets/icon-180.png`
- Regenerate: `launch-app/assets/icon-192.png`
- Regenerate: `launch-app/assets/icon-512.png`

**Interfaces:**
- Consumes: `prepare_assets(master_pdf: Path, output_dir: Path) -> None`
- Produces: `OUTPUT_NAMES = ("page-1.png", "page-2.png", "page-1-gold-mask.png", "page-2-gold-mask.png", "icon-180.png", "icon-192.png", "icon-512.png")`
- Produces: sharp RGB page images of exactly 2160 x 1215 pixels and transparent RGBA masks with matching dimensions.

- [ ] **Step 1: Write the failing asset contract**

Replace the old source-directory assertions in `tests/test_prepare_assets.py` with a master-PDF contract:

```python
MASTER_PDF = Path(os.environ["SOURCE_MASTER_PDF"])

def test_generates_pdf_faithful_pages_masks_and_icons(self):
    with tempfile.TemporaryDirectory() as temporary:
        output_dir = Path(temporary)
        prepare_assets(MASTER_PDF, output_dir)
        self.assertEqual(
            {path.name for path in output_dir.glob("*.png")},
            set(OUTPUT_NAMES),
        )
        for name in ("page-1.png", "page-2.png"):
            with Image.open(output_dir / name) as page:
                self.assertEqual(page.size, (2160, 1215))
                self.assertEqual(page.mode, "RGB")
        for name in ("page-1-gold-mask.png", "page-2-gold-mask.png"):
            with Image.open(output_dir / name) as mask:
                self.assertEqual(mask.size, (2160, 1215))
                self.assertEqual(mask.mode, "RGBA")
                alpha_bounds = mask.getchannel("A").getbbox()
                self.assertIsNotNone(alpha_bounds)
                self.assertLess(alpha_bounds[0], alpha_bounds[2])
        for size in (180, 192, 512):
            with Image.open(output_dir / f"icon-{size}.png") as icon:
                self.assertEqual(icon.size, (size, size))
        total = sum(path.stat().st_size for path in output_dir.glob("*.png"))
        self.assertLess(total, 9 * 1024 * 1024)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
$env:SOURCE_MASTER_PDF='C:\Users\Admin\Downloads\تطبيق التدشين (2).pdf'
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_prepare_assets -v
```

Expected: FAIL because `prepare_assets` still expects a source directory and the old asset names.

- [ ] **Step 3: Implement exact page rendering and gold-mask extraction**

Refactor `scripts/prepare_assets.py` around these constants and functions:

```python
PAGE_SCALE = 1.125
PAGE_SIZE = (2160, 1215)
OUTPUT_NAMES = (
    "page-1.png",
    "page-2.png",
    "page-1-gold-mask.png",
    "page-2-gold-mask.png",
    "icon-180.png",
    "icon-192.png",
    "icon-512.png",
)
GOLD_REGIONS = {
    0: ((650, 280, 1510, 590),),
    1: ((610, 250, 1550, 900),),
}

def render_pdf(path: Path, scale: float, page_index: int) -> Image.Image:
    document = pdfium.PdfDocument(str(path))
    page = document[page_index]
    bitmap = page.render(
        scale=scale,
        fill_color=(12, 70, 38, 255),
        rev_byteorder=True,
    )
    image = bitmap.to_pil().convert("RGB")
    if image.size != PAGE_SIZE:
        raise ValueError(f"Unexpected rendered page size: {image.size}")
    return image

def create_gold_mask(image: Image.Image, regions: tuple[tuple[int, int, int, int], ...]) -> Image.Image:
    alpha = Image.new("L", image.size, 0)
    for bounds in regions:
        crop = image.crop(bounds).convert("HSV")
        hue, saturation, value = crop.split()
        hue_band = hue.point(lambda pixel: 255 if 8 <= pixel <= 45 else 0)
        saturation_band = saturation.point(lambda pixel: 255 if pixel >= 45 else 0)
        value_band = value.point(lambda pixel: pixel if pixel >= 115 else 0)
        mask = ImageChops.multiply(
            ImageChops.multiply(hue_band, saturation_band),
            value_band,
        ).filter(ImageFilter.GaussianBlur(0.6))
        alpha.paste(mask, bounds[:2])
    result = Image.new("RGBA", image.size, (255, 255, 255, 0))
    result.putalpha(alpha)
    return result

def create_icons(page_two: Image.Image, output_dir: Path) -> None:
    emblem = page_two.crop((675, 235, 1485, 1045))
    square = ImageOps.fit(
        emblem,
        (512, 512),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.48),
    )
    for size in (180, 192, 512):
        save_png(square.resize((size, size), Image.Resampling.LANCZOS), output_dir / f"icon-{size}.png")

def prepare_assets(master_pdf: Path, output_dir: Path) -> None:
    if not master_pdf.is_file():
        raise FileNotFoundError(master_pdf)
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = [render_pdf(master_pdf, PAGE_SCALE, index) for index in (0, 1)]
    for number, page in enumerate(pages, start=1):
        save_png(page, output_dir / f"page-{number}.png")
        save_png(
            create_gold_mask(page, GOLD_REGIONS[number - 1]),
            output_dir / f"page-{number}-gold-mask.png",
        )
    create_icons(pages[1], output_dir)
```

Import `ImageChops` and `ImageFilter`, change the CLI option to `--master-pdf`, and remove the old `AssetSpec`, `ASSETS`, transparent trimming, source-directory behavior, `test_trim_transparent_preserves_padding`, and its obsolete import.

- [ ] **Step 4: Regenerate the production asset directory and remove only the six obsolete artwork files**

Verify the exact obsolete paths are inside `launch-app/assets`, remove those six tracked files, and run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/prepare_assets.py --master-pdf 'C:\Users\Admin\Downloads\تطبيق التدشين (2).pdf' --output-dir launch-app/assets
```

Expected: seven PNG files matching `OUTPUT_NAMES`; no old reconstructed artwork remains.

- [ ] **Step 5: Run focused GREEN and visually compare the two generated pages**

Run the focused Python test again. Open both `page-1.png` and `page-2.png` at original detail and compare them against `tmp/pdfs/tadsheen-v2/page-1.png` and `page-2.png`. Expected: same source composition, no clipping, black pixels, white rectangles, or altered text.

- [ ] **Step 6: Commit Task 1**

```powershell
git add -- scripts/prepare_assets.py tests/test_prepare_assets.py launch-app/assets
git diff --cached --check
git commit -m "feat: render exact ceremony PDF pages"
```

---

### Task 2: Exact-Page Screen Composition and Living Overlay Motion

**Files:**
- Modify: `launch-app/index.html`
- Modify: `launch-app/style.css`
- Modify: `tests/test_static_app.py`
- Modify: `tests/test_bundle.py`

**Interfaces:**
- Consumes: the seven Task 1 PNG filenames.
- Produces: `#screen-start`, `#screen-ceremony`, `#start-button`, `.page-backdrop`, `.page-frame`, `.page-art`, `.gold-shimmer`, and `.gold-glow`.
- Produces: source-coordinate Start center `left: 50%`, `top: 66.4%`; invisible hit area at least 300 x 300 CSS pixels.

- [ ] **Step 1: Write failing static composition and motion contracts**

Update `tests/test_static_app.py` so the two-screen test requires the new structure and rejects the old statistics reconstruction:

```python
def test_html_uses_exact_pdf_pages_for_two_screens(self):
    html = (APP / "index.html").read_text(encoding="utf-8")
    self.assertEqual(len(re.findall(r'class="screen ', html)), 2)
    self.assertEqual(len(re.findall(r'<button\b', html)), 1)
    self.assertIn('id="screen-start"', html)
    self.assertIn('id="screen-ceremony"', html)
    self.assertEqual(html.count('src="assets/page-1.png"'), 2)
    self.assertEqual(html.count('src="assets/page-2.png"'), 2)
    self.assertIn('assets/page-1-gold-mask.png', html)
    self.assertIn('assets/page-2-gold-mask.png', html)
    self.assertNotIn('statistics.png', html)

def test_css_contains_contained_page_blurred_duplicate_and_overlay_motion(self):
    css = (APP / "style.css").read_text(encoding="utf-8")
    for contract in (
        "aspect-ratio: 16 / 9",
        "object-fit: cover",
        "filter: blur(",
        "min-width: 300px",
        "min-height: 300px",
        "top: 66.4%",
        "page-1-gold-mask.png",
        "page-2-gold-mask.png",
        "@keyframes ring-rotate",
        "@keyframes halo-pulse",
        "@keyframes shimmer-sweep",
    ):
        self.assertIn(contract, css)
```

Update `tests/test_bundle.py` so `EXPECTED_ASSETS` is exactly the seven Task 1 names.

- [ ] **Step 2: Run the focused static tests and verify RED**

Run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_static_app tests.test_bundle -v
```

Expected: FAIL because the HTML/CSS and inventory still describe the reconstructed screens.

- [ ] **Step 3: Replace the screen markup with exact-page layers**

Use this structure in `launch-app/index.html` while retaining the existing PWA meta, icon, stylesheet, and deferred script tags:

```html
<main id="stage" class="stage" aria-label="تطبيق التدشين">
  <section id="screen-start" class="screen screen-start" aria-hidden="false">
    <img class="page-backdrop" src="assets/page-1.png" alt="" draggable="false">
    <div class="page-frame">
      <img class="page-art" src="assets/page-1.png" alt="صفحة تدشين مسابقة الملك عبدالعزيز الدولية" draggable="false">
      <div class="gold-shimmer shimmer-page-one" aria-hidden="true"></div>
      <button id="start-button" class="start-button" type="button" aria-label="ابدأ" disabled>
        <span class="start-orbit" aria-hidden="true"></span>
        <span class="start-halo" aria-hidden="true"></span>
      </button>
    </div>
  </section>
  <section id="screen-ceremony" class="screen screen-ceremony" aria-hidden="true">
    <img class="page-backdrop" src="assets/page-2.png" alt="" draggable="false">
    <div class="page-frame">
      <img class="page-art" src="assets/page-2.png" alt="هوية مسابقة الملك عبدالعزيز الدولية" draggable="false">
      <div class="gold-shimmer shimmer-page-two" aria-hidden="true"></div>
    </div>
  </section>
  <div class="gold-glow" aria-hidden="true"></div>
</main>
```

Preload both pages and both masks. Keep all asset URLs relative.

- [ ] **Step 4: Implement the 16:9 frame, blurred duplicate, and motion overlays**

Replace the reconstructed layout rules with these stable geometry contracts:

```css
.screen { position: absolute; inset: 0; overflow: hidden; background: #0c4626; }
.page-backdrop {
  position: absolute; inset: -7%; width: 114%; height: 114%;
  object-fit: cover; filter: blur(34px) brightness(.48) saturate(.92);
  transform: translateZ(0) scale(1.08); opacity: .96;
}
.page-frame {
  position: absolute; left: 50%; top: 50%;
  width: min(100vw, 177.7778vh); aspect-ratio: 16 / 9;
  transform: translate3d(-50%, -50%, 0); overflow: hidden;
  box-shadow: 0 0 48px rgba(4, 32, 17, .42);
}
.page-art { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: fill; }
.start-button {
  position: absolute; left: 50%; top: 66.4%;
  min-width: 300px; min-height: 300px; width: 300px; height: 300px;
  transform: translate3d(-50%, -50%, 0); border: 0; border-radius: 50%;
  padding: 0; background: transparent; outline: 0; touch-action: manipulation;
}
.start-orbit, .start-halo { position: absolute; left: 50%; top: 50%; border-radius: 50%; pointer-events: none; }
.start-orbit {
  width: clamp(176px, 17.8vw, 208px); aspect-ratio: 1;
  background: conic-gradient(from 0deg, transparent, rgba(255,238,163,.92), transparent 30%, rgba(207,163,61,.72), transparent 64%);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 5px), #000 calc(100% - 4px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 5px), #000 calc(100% - 4px));
  animation: ring-rotate 9s linear infinite;
}
.start-halo {
  width: clamp(184px, 18.6vw, 216px); aspect-ratio: 1;
  border: 2px solid rgba(246,216,126,.5); box-shadow: 0 0 24px rgba(237,197,91,.36);
  animation: halo-pulse 3.8s ease-out infinite;
}
.gold-shimmer { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.gold-shimmer::before {
  content: ""; position: absolute; top: -20%; bottom: -20%; left: 0; width: 16%;
  background: linear-gradient(90deg, transparent, rgba(255,255,225,.7), transparent);
  transform: translate3d(-180%, 0, 0) skewX(-14deg); opacity: 0;
  animation: shimmer-sweep 7.5s ease-in-out infinite;
}
.shimmer-page-one {
  -webkit-mask: url("assets/page-1-gold-mask.png") center / 100% 100% no-repeat;
  mask: url("assets/page-1-gold-mask.png") center / 100% 100% no-repeat;
}
.shimmer-page-two {
  -webkit-mask: url("assets/page-2-gold-mask.png") center / 100% 100% no-repeat;
  mask: url("assets/page-2-gold-mask.png") center / 100% 100% no-repeat;
}
```

Define `ring-rotate`, `halo-pulse`, and `shimmer-sweep` with only `transform` and `opacity`; preserve the 1.9-second forward transition and add a 600-millisecond reverse transition. In reduced-motion mode, disable orbit, halo, and shimmer loops while keeping short screen fades.

- [ ] **Step 5: Run focused GREEN and inspect both 4:3 layouts**

Run the focused static and bundle tests. Serve `launch-app/`, capture Screen 1 and Screen 2 at 1080 x 810 and 1024 x 768, and confirm the sharp `.page-frame` is 1080 x 607.5 or 1024 x 576, centered with no cropping; the blurred layer fills the remaining top and bottom area.

- [ ] **Step 6: Commit Task 2**

```powershell
git add -- launch-app/index.html launch-app/style.css tests/test_static_app.py tests/test_bundle.py
git diff --cached --check
git commit -m "feat: match the two-page ceremony artwork"
```

---

### Task 3: Replayable State Machine, Three-Tap Return, and Event Hardening

**Files:**
- Modify: `launch-app/app.js`
- Modify: `tests/test_app_js.mjs`

**Interfaces:**
- Consumes: DOM IDs `start-button`, `screen-start`, and `screen-ceremony`.
- Produces: controller states `loading`, `start`, `launching`, `ceremony`, and `returning` represented by root classes.
- Produces: `launch()` accepting once per start state and `recordReturnTap()` accepting three pointer releases inside 900 milliseconds.

- [ ] **Step 1: Replace the single-use controller test with failing replay and hardening tests**

Build a fake DOM harness that records button, ceremony `pointerup`, document hardening listeners, timers, class names, and `performance.now()`:

```javascript
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
    setAttribute(name, value) { this.attributes.set(name, value); },
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
      querySelectorAll() { return [{ decode: () => Promise.resolve() }]; },
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
    const match = [...timers.values()].find((timer) => timer.active && timer.delay === delay);
    assert.ok(match, `missing active ${delay}ms timer`);
    match.active = false;
    match.listener();
  };

  return {
    classes,
    button: {
      get disabled() { return button.disabled; },
      click: () => button.listeners.get("click").listener(),
    },
    ceremony: {
      pointerup: () => screenCeremony.listeners.get("pointerup").listener(),
    },
    documentListeners,
    setNow: (value) => { now = value; },
    pendingTimers: (delay) => [...timers.values()].filter((timer) => timer.active && timer.delay === delay).length,
    runTimer,
  };
}

async function loadLaunchedAppHarness() {
  const app = await loadAppHarness();
  app.button.click();
  app.runTimer(1900);
  return app;
}
```

Add these assertions:

```javascript
test("guards launch, returns on three fast taps, and launches again", async () => {
  const app = await loadAppHarness();
  app.button.click();
  app.button.click();
  assert.equal(app.pendingTimers(1900), 1);
  app.runTimer(1900);
  assert.equal(app.classes.has("is-launched"), true);

  app.setNow(100);
  app.ceremony.pointerup();
  app.setNow(450);
  app.ceremony.pointerup();
  app.setNow(850);
  app.ceremony.pointerup();
  assert.equal(app.classes.has("is-returning"), true);
  app.runTimer(600);
  assert.equal(app.button.disabled, false);

  app.button.click();
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
});

test("registers non-passive blockers for callout selection drag and gestures", async () => {
  const app = await loadAppHarness();
  for (const type of ["contextmenu", "dragstart", "selectstart", "touchmove", "gesturestart", "gesturechange", "gestureend"]) {
    assert.equal(app.documentListeners.get(type).options.passive, false);
    const event = { prevented: false, preventDefault() { this.prevented = true; } };
    app.documentListeners.get(type).listener(event);
    assert.equal(event.prevented, true);
  }
});
```

- [ ] **Step 2: Run Node tests and verify RED**

Run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests/test_app_js.mjs
```

Expected: FAIL because the current listener is `{ once: true }`, Screen 2 has the old ID, no return state exists, and no event blockers are registered.

- [ ] **Step 3: Implement the replayable controller and event blockers**

Refactor `launch-app/app.js` to this state shape:

```javascript
const FORWARD_DURATION = 1900;
const RETURN_DURATION = 600;
const RETURN_WINDOW = 900;
const BLOCKED_EVENTS = [
  "contextmenu", "dragstart", "selectstart", "touchmove",
  "gesturestart", "gesturechange", "gestureend",
];
let state = "loading";
let transitionTimer = 0;
let returnTapTimes = [];

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
  returnTapTimes = returnTapTimes.filter((recorded) => time - recorded <= RETURN_WINDOW);
  returnTapTimes.push(time);
  if (returnTapTimes.length >= 3) returnToStart();
};
```

Use `Promise.allSettled(criticalImages.map(decodeImage)).then(finishStartReadiness)`. Register the button click without `{ once: true }`, register `pointerup` on `screenCeremony`, and register every blocked event on `document` with `{ passive: false }` and a listener that calls `preventDefault()`. Keep service-worker registration, changing its target only if Task 4 requires an update option.

- [ ] **Step 4: Run focused GREEN, then all JavaScript tests**

Run the Node command from Step 2, followed by:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests/test_app_js.mjs tests/test_sw.mjs
```

Expected: all tests pass; no cancelled or skipped tests.

- [ ] **Step 5: Commit Task 3**

```powershell
git add -- launch-app/app.js tests/test_app_js.mjs
git diff --cached --check
git commit -m "feat: add hardened three-tap ceremony replay"
```

---

### Task 4: Versioned Offline Update and Operator Runbook

**Files:**
- Modify: `launch-app/sw.js`
- Modify: `launch-app/manifest.json`
- Modify: `launch-app/README.md`
- Modify: `tests/test_sw.mjs`
- Modify: `tests/test_static_app.py`
- Modify: `tests/test_bundle.py`

**Interfaces:**
- Consumes: the final physical `launch-app/` inventory.
- Produces: cache `quran-launch-v2`, complete inventory precache, same-origin cache-first fetch, and actual public installation instructions.

- [ ] **Step 1: Write failing version and runbook contracts**

Add to `tests/test_sw.mjs`:

```javascript
assert.match(source, /quran-launch-/);
assert.match(source, /CACHE_NAME = `\$\{CACHE_PREFIX\}v2`/);
```

Update manifest assertions to require `background_color == "#0c4626"`. Update the README contract to require the exact public URL, `ثلاث نقرات`, and removal of the old Screen 2 statistics instruction:

```python
self.assertIn(
    "https://corexsol.github.io/quran-competition-launch-app/launch-app/",
    readme,
)
self.assertIn("ثلاث نقرات", readme)
self.assertNotIn("شاشة الإحصاءات", readme)
```

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests/test_sw.mjs
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_static_app tests.test_bundle -v
```

Expected: FAIL for cache v1, white manifest background, generic `USERNAME/REPOSITORY` URLs, and the old statistics wording.

- [ ] **Step 3: Implement the versioned cache and updated metadata**

Change only the service-worker cache name to:

```javascript
const CACHE_NAME = `${CACHE_PREFIX}v2`;
```

Rebuild `PRECACHE_URLS` from the exact final inventory, retaining both `./` and `./index.html`. Keep cache deletion, `skipWaiting`, `clients.claim`, same-origin filtering, ignored query strings, and navigation fallback unchanged. Change manifest `background_color` to `#0c4626`.

- [ ] **Step 4: Update the Arabic README for the real deployment and replay gesture**

Replace the generic `USERNAME/REPOSITORY` URLs with `https://corexsol.github.io/quran-competition-launch-app/launch-app/`. The rehearsal must instruct the operator to verify Screen 1, press `ابدأ`, verify the exact second PDF page, tap Screen 2 three times quickly to return, launch again, and repeat the entire sequence in Airplane Mode. Add a warning that the app must be opened online after this v2 publication so the old service-worker cache is replaced.

- [ ] **Step 5: Run focused GREEN and exact inventory verification**

Run both focused commands from Step 2. Expected: the worker-derived set equals every physical `launch-app/` file plus `./`, has no duplicates, and every runbook/manifest assertion passes.

- [ ] **Step 6: Commit Task 4**

```powershell
git add -- launch-app/sw.js launch-app/manifest.json launch-app/README.md tests/test_sw.mjs tests/test_static_app.py tests/test_bundle.py
git diff --cached --check
git commit -m "feat: ship the redesigned offline ceremony bundle"
```

---

### Task 5: Full Ceremony Verification, Publication, and Live Update Proof

**Files:**
- Create ignored evidence: `.superpowers/sdd/pdf-redesign-qa-report.md`
- Create ignored evidence: `tmp/qa-redesign/*.png`
- Modify tracked files only if a failing test or verified browser defect requires a focused RED -> GREEN fix.

**Interfaces:**
- Consumes: final Tasks 1-4 commits.
- Produces: validated local/offline/browser evidence, pushed `origin/main`, a successful GitHub Pages build, and a verified public URL.

- [ ] **Step 1: Run the complete automated verification gate**

Run:

```powershell
$python='C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$node='C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$env:SOURCE_MASTER_PDF='C:\Users\Admin\Downloads\تطبيق التدشين (2).pdf'
& $python -m unittest discover -s tests -p 'test_*.py' -v
& $node --test tests/test_app_js.mjs tests/test_sw.mjs
git diff --check
```

Expected: all Python and Node tests pass, no whitespace errors, seven valid PNG assets, and total `launch-app/` size below 10 MiB.

- [ ] **Step 2: Verify 4:3 layout and interaction in a clean real browser**

Serve the repository so the app is accessed under a nested path equivalent to `/REPOSITORY/launch-app/`. At 1080 x 810 and 1024 x 768, record:

- viewport equals document scroll dimensions;
- `.page-frame` is centered and has a 16:9 bounding box fully inside the viewport;
- every `.page-art` is complete and uncropped;
- Start hit area is at least 300 x 300;
- two rapid Start activations yield only one 1900-millisecond transition;
- Screen 2 becomes visible with no lingering launch class;
- one and two taps do nothing;
- the third tap inside 900 milliseconds begins return;
- after 600 milliseconds Screen 1 is ready and can launch again;
- no exceptions, console errors, failed requests, selection text, scrolling, or context-menu default.

Capture sharp screenshots for both screens at both viewports plus the returned Screen 1.

- [ ] **Step 3: Inspect every screenshot at original detail against the rendered PDF**

Compare each foreground page with the corresponding PDF render. Reject and fix any cropped border, shifted logo, missing portrait, unreadable calligraphy, white flash, harsh blur seam, shimmer outside gold artwork, misaligned Start orbit, or clipped shadow. Confirm `ابدأ` itself does not rotate or pulse.

- [ ] **Step 4: Prove clean-profile cache v2 and stopped-server offline replay**

In a new browser profile, wait for an active controlling worker named `quran-launch-v2`, enumerate the cache, and compare it exactly with the final physical inventory plus `./`. Record the exact local server PID, verify its command, stop only that PID, disable the browser HTTP cache, and reload normally. Offline, verify Screen 1, forward launch, three-tap return, replay, complete images, and zero network failures.

- [ ] **Step 5: Record evidence and run the completion gate again**

Write `.superpowers/sdd/pdf-redesign-qa-report.md` with test counts, viewport measurements, screenshot paths, cache entries, exact stopped PID, offline observations, and any physical-iPad-only limitation. Remove disposable scripts, profiles, and Python cache directories after resolving and checking that every deletion target is inside the worktree.

- [ ] **Step 6: Push the reviewed commits to the public `main` branch**

```powershell
git status -sb
git push origin HEAD:main
```

Expected: fast-forward push succeeds and remote `main` equals local HEAD. Do not publish `tmp/` or ignored evidence.

- [ ] **Step 7: Wait for GitHub Pages and verify the live app**

Use GitHub CLI to wait until the Pages build for the pushed commit reports `built`. Verify HTTP 200 and correct content types for:

- `https://corexsol.github.io/quran-competition-launch-app/launch-app/`
- `manifest.json`
- `sw.js`
- `assets/page-1.png`
- `assets/page-2.png`

Open the public app in a clean browser, confirm the page-2 and three-tap behavior, and confirm the active service worker uses `quran-launch-v2`.

- [ ] **Step 8: Hand off the required physical iPad rehearsal**

Provide the live URL and the exact operator sequence: open online, wait for Screen 1, add to Home Screen, close and reopen, verify long-press/pinch/double-tap suppression, launch, three-tap return, replay, enable Airplane Mode, and repeat. Do not claim physical Safari gesture verification until the user completes it on the target iPad.
