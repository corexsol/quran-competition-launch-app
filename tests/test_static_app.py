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
            "width: clamp(300px",
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


if __name__ == "__main__":
    unittest.main()
