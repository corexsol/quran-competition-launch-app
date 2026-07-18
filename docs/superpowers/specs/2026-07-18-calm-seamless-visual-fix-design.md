# Calm Seamless Ceremony Visual Fix

## Objective

Correct the visible white strip at the left edge, make the 16:9 source artwork feel integrated into the iPad's 4:3 landscape viewport, and replace the distracting launch motion with the approved quiet treatment.

The supplied two-page PDF remains the visual source of truth. The sharp page renders must remain fully legible, keep their original 16:9 aspect ratio, and retain all portraits, logos, Arabic text, statistics, ornament, and borders. No recomposition, generated replacement artwork, or text reconstruction is permitted.

## Approved Direction

This specification implements the approved **Option A: seamless extension with quiet live motion**.

- The sharp PDF page stays centered, full-width, and undistorted.
- The extra 4:3 space above and below is filled by a restrained extension derived from the same page.
- There is no visible frame, drop shadow, hard seam, or white strip.
- The Start artwork itself remains stationary.
- The only idle movement is a thin outline whose opacity breathes slowly.
- Screen changes use pure crossfades with no yellow flash, radial veil, zoom, slide, rotation, or shimmer.

## Layout and Edge Treatment

Each screen continues to contain two visual layers derived from the same optimized page render:

1. A full-viewport ambient duplicate fills the stage with `object-fit: cover`. It uses the approved preview treatment: an approximately 9-percent negative inset, 118-percent width and height, `blur(12px) brightness(0.72) saturate(0.94)`, and `scale(1.05)`. This blends the top and bottom extensions into the sharp page without competing with it.
2. A sharp 16:9 foreground page is centered vertically and spans the viewport width.

The foreground frame has no shadow. It horizontally overscans the viewport by one CSS pixel on each side while preserving its 16:9 aspect ratio. This clips only the defective outermost raster columns responsible for the source PDF's white left seam. It may remove approximately two and at most three source-image pixels per side at the target iPad scale, and it must not crop any meaningful artwork.

The sharp foreground is never stretched independently in either axis. At 1080 x 810 it is 1082 x 608.625 CSS pixels before viewport clipping; at 1024 x 768 it is 1026 x 577.125 CSS pixels. The remaining height is the seamless ambient extension. All four viewport corners and every pixel outside the sharp page are painted dark green or page-derived green—never browser white.

The ambient layer remains background-only and must satisfy all of these observable constraints:

- no readable duplicate text or obvious duplicate portrait edges in the extension;
- no dark rectangular frame around the sharp page;
- no visible horizontal boundary caused by a shadow or overlay;
- no bright or yellow cast that distracts from the source artwork.

## Start Control Motion

The transparent Start hit area stays aligned over the printed `ابدأ` control and remains at least 300 x 300 CSS pixels.

The current rotating conic ring and expanding halo are removed. They are replaced by one circular outline aligned around the printed control. During idle, the outline is stationary. It:

- is two CSS pixels thick;
- uses a restrained, semi-transparent warm gold sampled from the artwork;
- changes opacity only, with a 3.2-second ease-in-out breathing cycle;
- does not rotate, expand, translate, glow across the page, or move the printed button.

Pressing Start gives immediate feedback by scaling only the transparent feedback wrapper to `0.98` for 100 milliseconds. The sharp PDF page and printed `ابدأ` artwork do not move.

When reduced motion is requested, the outline is stationary at a moderate opacity. The two opacity-only crossfades retain their normal 700- and 600-millisecond durations so CSS and JavaScript state timing remain synchronized.

## Screen Transitions

The forward transition is a simultaneous, pure crossfade lasting 700 milliseconds:

- Screen 1 fades from fully visible to transparent.
- Screen 2 fades from transparent to fully visible over the same interval.
- Neither screen scales, slides, rotates, changes color, or receives a flash overlay.

The reverse transition triggered by the hidden three-tap gesture remains a quieter 600-millisecond pure crossfade. Transition durations in CSS and JavaScript must match so state finalization cannot occur before the visual animation ends.

The existing gold shimmer overlays, source-derived shimmer masks, radial launch glow, and their preload/runtime references are removed from the shipped bundle. Their animation keyframes must not remain active or reachable.

## Interaction and Ceremony Hardening

The existing interaction model is preserved:

1. Images decode before Start becomes active.
2. The first accepted activation disables Start synchronously to reject double taps.
3. Three pointer releases on Screen 2 within the existing 900-millisecond rolling window return to Screen 1.
4. Start is re-enabled only after the reverse transition completes so the ceremony can be replayed safely.
5. Input during either transition is ignored.

All current kiosk hardening remains in force: no text selection, image dragging, long-press callout, context menu, pinch zoom, double-tap zoom, scrolling, rubber-band bounce, tap highlight, visible cursor, focus outline, or scrollbars.

## Offline and Bundle Behavior

The app remains a plain local PWA with no external runtime dependency. Removing the shimmer masks reduces the bundle rather than adding payload.

The service-worker cache identifier is incremented for this release, and every remaining physical runtime file is precached. The HTML preloads only the two page images used at runtime. Relative paths, standalone display mode, landscape orientation, icons, and the existing cache-first offline behavior are preserved.

## Failure Handling

The existing image-readiness fallback remains: a rejected `decode()` attempt cannot permanently disable Start when an already-complete or cached image is otherwise usable. A missing runtime asset is caught by the bundle/precache inventory tests before publication.

Service-worker registration failures remain non-blocking and logged. Transition timers continue to verify the current state before finalizing, and return-to-start clears stale launch state so a delayed callback cannot switch screens unexpectedly.

## Verification

Implementation is test-first. Static and behavioral tests must initially fail for the old treatment and then prove the approved treatment:

- no runtime markup, preload, stylesheet rule, or service-worker entry references the shimmer masks, gold shimmer, rotating orbit, expanding halo, or radial gold glow;
- no `ring-rotate`, `halo-pulse`, `shimmer-sweep`, or `glow-expand` animation remains reachable;
- forward duration is 700 milliseconds and reverse duration is 600 milliseconds in both CSS and JavaScript;
- the quiet outline uses opacity-only idle animation and the printed page artwork has no animated transform;
- exactly two screens, one Start control, the synchronous activation guard, the three-tap return contract, replay, hardening, local-only dependencies, and the sub-10-MiB bundle limit continue to pass;
- the service-worker precache inventory exactly matches the physical shipped bundle and uses the new cache identifier.

Real-browser acceptance runs at 1080 x 810 and 1024 x 768 and verifies:

- the stage exactly fills the viewport with no scrolling or unpainted corner;
- the sharp foreground keeps a 16:9 ratio, spans slightly beyond both horizontal viewport edges, and is centered vertically;
- the complete source page is visible apart from the explicitly allowed defective outermost raster columns;
- at each target viewport, neither edge column (`x = 0` or `x = viewport width - 1`) contains a contiguous run longer than 25 percent of the rendered height in which every pixel has red, green, and blue values of at least 235, preventing recurrence of a visible white strip;
- no frame shadow or hard top/bottom boundary is visible in screenshots;
- the Start hit area is at least 300 x 300 CSS pixels and enables only after image readiness;
- the quiet outline breathes without rotation or expansion, while the page image remains stationary;
- the forward and reverse crossfades finish in their specified states with no flash layer or stale animation class;
- the three-tap return and second launch work;
- there are no console errors or failed runtime requests;
- a service-worker-controlled reload works after the local server is stopped.

After publication, the GitHub Pages URL receives a clean-profile online smoke check and an offline reload check. If no physical iPad is available to the implementation agent, the user's final post-publication operational gate is an iPad landscape rehearsal covering press-and-hold, pinch, double-tap, Start, three-tap return, replay, and Airplane Mode.

## Success Criteria

- No white strip is visible on the left edge at either target iPad viewport.
- The app paints the entire 4:3 screen while keeping the supplied 16:9 PDF artwork undistorted and effectively complete.
- The surrounding extension looks like a continuation of the page rather than a separate blurred frame.
- Start feels subtly alive, but the printed `ابدأ` control and source artwork remain stationary.
- The launch contains no yellow flash, shimmer sweep, rotating ring, expanding halo, slide, or zoom.
- Both directions crossfade cleanly, and the preserved three-tap replay flow remains reliable.
- The hardened installed PWA works fully offline from the public GitHub Pages deployment.
