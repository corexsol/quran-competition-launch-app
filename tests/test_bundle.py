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
