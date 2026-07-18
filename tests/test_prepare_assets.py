import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_assets import OUTPUT_NAMES, prepare_assets, trim_transparent


class PrepareAssetsTests(unittest.TestCase):
    def test_trim_transparent_preserves_padding(self):
        image = Image.new("RGBA", (40, 40), (255, 255, 255, 0))
        image.paste((20, 80, 40, 255), (15, 15, 25, 25))
        trimmed = trim_transparent(image, padding=3)
        self.assertEqual(trimmed.size, (16, 16))

    def test_generates_complete_optimized_asset_set(self):
        source_dir = Path(os.environ["SOURCE_PDF_DIR"])
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            prepare_assets(source_dir, output_dir)
            self.assertEqual(
                {path.name for path in output_dir.glob("*.png")},
                set(OUTPUT_NAMES),
            )
            minimum_sizes = {
                "title.png": (1100, 500),
                "minister.png": (1000, 450),
                "start-button.png": (900, 900),
                "background-sides.png": (2000, 1100),
                "background-medallion.png": (1200, 1200),
                "statistics.png": (1500, 1500),
            }
            for name, minimum in minimum_sizes.items():
                with Image.open(output_dir / name) as image:
                    self.assertGreaterEqual(image.width, minimum[0], name)
                    self.assertGreaterEqual(image.height, minimum[1], name)
                    self.assertIn(image.mode, {"RGB", "RGBA"}, name)
            for size in (180, 192, 512):
                with Image.open(output_dir / f"icon-{size}.png") as icon:
                    self.assertEqual(icon.size, (size, size))
            total = sum(path.stat().st_size for path in output_dir.glob("*.png"))
            self.assertLess(total, 10 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
