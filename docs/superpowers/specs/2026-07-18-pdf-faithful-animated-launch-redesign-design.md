# PDF-Faithful Animated Launch Redesign

## Objective

Replace the current reconstructed layouts with two ceremony screens that preserve the supplied two-page PDF exactly while adapting its 16:9 pages to the iPad's 4:3 landscape viewport without cropping. Add restrained ceremonial motion, stronger kiosk-style interaction hardening, and a hidden three-tap return gesture.

The visual source of truth is `C:\Users\Admin\Downloads\تطبيق التدشين (2).pdf`, an Adobe Illustrator PDF with two 1920 x 1080 point pages. No generated or invented artwork, text, portraits, logos, statistics, or claims may replace the source content.

## Visual Composition

Each PDF page is rendered as one sharp, optimized local image. The sharp image is centered, fully visible, and scaled with `object-fit: contain`, preserving every source coordinate and preventing edge cropping.

Behind it, the same page image is duplicated, enlarged with `object-fit: cover`, blurred, slightly darkened, and scaled beyond the viewport so the iPad's extra 4:3 area feels intentional. The blurred layer fills only the visual gap; it must never reduce the legibility or geometric fidelity of the sharp page. A dark green base matching the PDF prevents flashes during loading.

Screen 1 uses PDF page 1 in full, including the portraits, ministry and competition logos, competition title, supervision copy, calligraphy, ornamental border, and the printed Start control. Screen 2 uses PDF page 2 in full, including the portraits, Vision 2030 mark, central competition emblem, palm emblems, calligraphy, background ornament, and lower border.

The sharp page remains the authoritative artwork. CSS effects are overlays and may not move, rewrite, recolor, or obscure its content.

## Motion Treatment

The printed `ابدأ` word remains stationary because it belongs to the sharp page image. A transparent interactive hit area is aligned over the printed button and is at least 300 CSS pixels in both dimensions, even when the visible control renders smaller.

Two decorative layers animate around the printed control:

- a thin gold conic-gradient ring rotates continuously at a slow, dignified speed;
- a soft radial halo expands and fades on a longer pulse cycle.

The ring and halo stop being interactive immediately after the first activation. Press feedback scales only the overlay by approximately 4 percent for about 100 milliseconds; the PDF artwork does not shift.

One or two carefully aligned shimmer masks may sweep across selected gold title areas. Each pass is narrow, low-opacity, and separated by a long pause. The shimmer must be clipped to source-derived masks so it does not wash across the green background, portraits, or white logos. Screen 2 may use a similarly restrained glint on the central gold ring. All motion uses `transform` and `opacity` only.

The forward transition keeps the approved ceremonial pattern: immediate press feedback, an expanding gold glow, Screen 1 fade, and Screen 2 fade/scale arrival. Total duration remains between 1.5 and 2.5 seconds. The reverse transition is shorter and quieter, fading Screen 2 back to Screen 1 in approximately 600 milliseconds.

## Interaction Model

The app still has exactly two screens and no routing.

1. On load, all critical images decode before the Start hit area is enabled.
2. The first accepted Start activation disables the hit area synchronously and begins the forward transition.
3. Screen 2 counts pointer releases anywhere on the stage. Three releases within a rolling 900 millisecond window trigger the reverse transition.
4. Fewer than three releases, or releases separated by more than 900 milliseconds, have no effect.
5. When Screen 1 is restored, the Start hit area is enabled again so the full ceremony flow can be replayed.
6. Activations during either forward or reverse transition are ignored.

The three-tap return gesture is intentionally invisible and has no on-screen control.

## Ceremony Hardening

The document and stage prohibit viewport manipulation with `touch-action: none`; the Start control uses a normal pointer/click path and does not depend on browser gestures. The viewport meta retains its zoom restrictions as a secondary hint.

The app applies all of the following locally:

- `overflow: hidden` and `overscroll-behavior: none` on the root and body;
- `-webkit-user-select: none`, `user-select: none`, and `-webkit-touch-callout: none` on every rendered element;
- transparent tap highlight, hidden cursor, and non-draggable images;
- cancellation of `contextmenu`, `dragstart`, `selectstart`, `gesturestart`, `gesturechange`, and `gestureend` defaults;
- no visible scrollbars, selection highlights, focus outlines, or browser text/image callouts.

The JavaScript cancellation listeners are non-passive only where `preventDefault()` is required. They do not block the Start click or the triple-tap pointer counting.

## Assets and Offline Behavior

The two optimized page images and any source-derived shimmer masks replace the old reconstruction-only artwork. Existing local icons may be regenerated from the new competition emblem if the PDF extraction is cleaner. The deliverable remains under 10 MiB.

All runtime references remain relative so the app works at `https://corexsol.github.io/quran-competition-launch-app/launch-app/`. The service-worker cache name is versioned again so already-installed iPads receive the redesigned bundle instead of continuing to serve the old ceremony artwork. Installation precaches every physical file in `launch-app/` plus the directory navigation alias, and fetch handling remains same-origin and cache-first.

## Failure Handling

If image decoding rejects, the app still enables after the decode attempt settles because a cached or already-complete image may remain usable. A missing critical asset is prevented by bundle-inventory tests and live network verification before publication. Service-worker registration errors remain logged but do not block the ceremony interaction.

If the return-tap timer expires, its count resets cleanly. Returning cancels pending launch/finalization timers so stale callbacks cannot switch the app back to Screen 2.

## Verification

Automated tests must cover:

- exactly two screens and one Start control;
- exact new asset inventory and complete service-worker precache inventory;
- document hardening declarations and event cancellation contracts;
- synchronous double-activation guard;
- three taps within 900 milliseconds return to Screen 1;
- slow or incomplete tap sequences do not return;
- a restored Screen 1 can launch again;
- bundle size below 10 MiB and no remote runtime dependencies.

Real-browser acceptance must run at both 1080 x 810 and 1024 x 768. It must verify no scroll, no clipping of the sharp PDF page, a minimum 300-pixel Start hit target, forward and reverse transitions, animation-state cleanup, zero console/network errors, active service-worker control, and stopped-server offline reload. Final screenshots are compared visually with both rendered source PDF pages at original detail.

The final operational gate remains a physical iPad Safari rehearsal: install from the public GitHub Pages URL, confirm press-and-hold produces no selection or callout, confirm pinch and double-tap do not zoom, exercise the forward and three-tap reverse flows, then repeat in Airplane Mode.

## Success Criteria

- Both screens visibly match the supplied PDF pages because the PDF renders themselves are the sharp foreground artwork.
- No source edge, portrait, logo, text, or lower border is cropped on the 4:3 iPad viewport.
- The surrounding blurred duplicate fills the 4:3 gap without distracting from the sharp page.
- Start motion feels alive while `ابدأ` itself remains stationary and legible.
- Three quick taps on Screen 2 reliably restore Screen 1; ordinary single or double taps do nothing.
- Press-and-hold, selection, dragging, pinch zoom, double-tap zoom, scrolling, and rubber-band bounce are suppressed.
- The installed app works fully offline and updates from the previously published version.
