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


if __name__ == "__main__":
    unittest.main()
