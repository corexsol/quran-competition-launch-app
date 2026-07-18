import re
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "launch-app"
EXPECTED_TOP_LEVEL = {
    "README.md",
    "app.js",
    "assets",
    "index.html",
    "manifest.json",
    "style.css",
    "sw.js",
}
EXPECTED_ASSETS = {
    "icon-180.png",
    "icon-192.png",
    "icon-512.png",
    "page-1.png",
    "page-2.png",
}


class BundleTests(unittest.TestCase):
    def test_bundle_inventory_is_exact(self):
        self.assertEqual({path.name for path in APP.iterdir()}, EXPECTED_TOP_LEVEL)
        self.assertEqual(
            {path.name for path in (APP / "assets").iterdir()},
            EXPECTED_ASSETS,
        )

    def test_all_local_document_references_exist(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        references = re.findall(r'(?:src|href)="([^"]+)"', html)
        for reference in references:
            self.assertNotIn("://", reference)
            self.assertTrue((APP / reference).is_file(), reference)

    def test_png_files_are_valid(self):
        pngs = sorted((APP / "assets").glob("*.png"))
        self.assertEqual({path.name for path in pngs}, EXPECTED_ASSETS)
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
        self.assertIn("ثلاث نقرات", readme)
        self.assertNotIn("شاشة الإحصاءات", readme)

    def test_operator_readme_prioritizes_github_pages_subpath(self):
        readme = (APP / "README.md").read_text(encoding="utf-8")
        self.assertIn("GitHub Pages", readme)
        self.assertIn("main", readme)
        self.assertIn(
            "https://corexsol.github.io/quran-competition-launch-app/launch-app/",
            readme,
        )
        self.assertNotIn("USERNAME", readme)
        self.assertNotIn("REPOSITORY", readme)
        self.assertIn("المسارات النسبية", readme)
        self.assertIn("manifest.json", readme)
        self.assertIn("sw.js", readme)


if __name__ == "__main__":
    unittest.main()
