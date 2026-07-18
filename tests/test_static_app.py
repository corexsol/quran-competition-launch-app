# tests/test_static_app.py
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "launch-app"


def css_block(css, marker):
    marker_start = css.index(marker)
    opening_brace = css.index("{", marker_start)
    depth = 0
    for index in range(opening_brace, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[opening_brace + 1 : index]
    raise AssertionError(f"unterminated CSS block: {marker}")


class StaticAppTests(unittest.TestCase):
    def test_manifest_is_arabic_standalone_landscape(self):
        manifest = json.loads((APP / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["orientation"], "landscape")
        self.assertEqual(manifest["theme_color"], "#1a4d2e")
        self.assertEqual(manifest["background_color"], "#ffffff")
        self.assertEqual([icon["sizes"] for icon in manifest["icons"]], ["192x192", "512x512"])

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

    def test_html_preserves_pwa_and_start_button_contracts(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="start-button"', html)
        self.assertIn('apple-mobile-web-app-capable" content="yes', html)
        self.assertIn('apple-mobile-web-app-status-bar-style" content="black-translucent', html)
        self.assertIn('rel="apple-touch-icon" href="assets/icon-180.png"', html)
        self.assertIn('maximum-scale=1, user-scalable=no', html)

    def test_html_wraps_only_start_overlays_for_press_feedback(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        button = re.search(
            r'<button\b[^>]*id="start-button"[^>]*>(?P<body>.*?)</button>',
            html,
            re.DOTALL,
        )

        self.assertIsNotNone(button)
        feedback = re.fullmatch(
            r'\s*<span class="start-feedback">\s*'
            r'<span class="start-orbit" aria-hidden="true"></span>\s*'
            r'<span class="start-halo" aria-hidden="true"></span>\s*'
            r'</span>\s*',
            button.group("body"),
            re.DOTALL,
        )
        self.assertIsNotNone(feedback)

    def test_html_uses_precached_local_favicon(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            '<link rel="icon" type="image/png" href="assets/icon-192.png">',
            html,
        )

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
            "min-width: 300px",
        ):
            self.assertIn(contract, css)

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

    def test_css_blocks_viewport_gestures_while_preserving_button_taps(self):
        css = (APP / "style.css").read_text(encoding="utf-8")
        document_rule = re.search(r"html,\s*body\s*\{(?P<body>[^}]*)\}", css, re.DOTALL)
        button_rule = re.search(r"\.start-button\s*\{(?P<body>[^}]*)\}", css, re.DOTALL)

        self.assertIsNotNone(document_rule)
        self.assertRegex(document_rule.group("body"), r"touch-action:\s*none\s*;")
        self.assertIsNotNone(button_rule)
        self.assertRegex(button_rule.group("body"), r"touch-action:\s*manipulation\s*;")

    def test_css_globally_blocks_selection_and_callouts(self):
        css = (APP / "style.css").read_text(encoding="utf-8")
        global_rule = re.search(
            r"\*,\s*\*::before,\s*\*::after\s*\{(?P<body>[^}]*)\}",
            css,
            re.DOTALL,
        )

        self.assertIsNotNone(global_rule)
        for contract in (
            r"-webkit-user-select:\s*none\s*;",
            r"user-select:\s*none\s*;",
            r"-webkit-touch-callout:\s*none\s*;",
        ):
            self.assertRegex(global_rule.group("body"), contract)

    def test_css_has_forward_and_reverse_screen_state_hooks(self):
        css = (APP / "style.css").read_text(encoding="utf-8")
        for contract in (
            "--transition-duration: 1900ms",
            "--return-duration: 600ms",
            ".is-launching .screen-start",
            ".is-launching .screen-ceremony",
            ".is-launched .screen-ceremony",
            ".is-returning .screen-start",
            ".is-returning .screen-ceremony",
        ):
            self.assertIn(contract, css)

    def test_css_scales_only_start_feedback_on_press(self):
        css = (APP / "style.css").read_text(encoding="utf-8")
        feedback_rule = re.search(
            r"\.start-feedback\s*\{(?P<body>[^}]*)\}", css, re.DOTALL
        )
        active_rule = re.search(
            r"\.start-button:active:not\(:disabled\)\s+\.start-feedback\s*"
            r"\{(?P<body>[^}]*)\}",
            css,
            re.DOTALL,
        )

        self.assertIsNotNone(feedback_rule)
        self.assertRegex(
            feedback_rule.group("body"), r"transition:\s*transform\s+100ms\b"
        )
        self.assertIsNotNone(active_rule)
        self.assertRegex(active_rule.group("body"), r"transform:\s*scale\(0?\.96\)\s*;")
        self.assertNotRegex(
            css,
            r"\.start-button:active:not\(:disabled\)\s*\{[^}]*scale\(",
        )

    def test_screen_states_and_transition_keyframes_are_opacity_only(self):
        css = (APP / "style.css").read_text(encoding="utf-8")
        for selector in (
            ".screen-start {",
            ".screen-ceremony {",
            ".is-launched .screen-ceremony {",
        ):
            with self.subTest(selector=selector):
                self.assertNotIn("transform:", css_block(css, selector))

        for name in (
            "start-exit",
            "ceremony-enter",
            "start-return",
            "ceremony-exit",
        ):
            with self.subTest(keyframes=name):
                self.assertNotIn("transform:", css_block(css, f"@keyframes {name}"))


if __name__ == "__main__":
    unittest.main()
