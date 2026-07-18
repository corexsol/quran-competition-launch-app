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
