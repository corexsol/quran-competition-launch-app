import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_assets import OUTPUT_NAMES, prepare_assets

MASTER_PDF = Path(os.environ["SOURCE_MASTER_PDF"])


class PrepareAssetsTests(unittest.TestCase):
    def test_generates_pdf_faithful_pages_and_icons(self):
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
                    near_white = sum(
                        1
                        for y in range(page.height)
                        if min(page.getpixel((0, y))) >= 235
                    )
                    self.assertLess(near_white, page.height // 4)
            for size in (180, 192, 512):
                with Image.open(output_dir / f"icon-{size}.png") as icon:
                    self.assertEqual(icon.size, (size, size))
            total = sum(path.stat().st_size for path in output_dir.glob("*.png"))
            self.assertLess(total, 9 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
