"""Regression tests for tools/cad_measure.py (local route; the MCP route needs a server)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import cad_measure  # noqa: E402


class LocalMeasure(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.stl = str(Path(self.tmp.name) / "cube.stl")
        cad_measure.cube(self.stl, 20)

    def tearDown(self):
        self.tmp.cleanup()

    def measure(self, *extra):
        out = subprocess.run([sys.executable, str(ROOT / "tools" / "cad_measure.py"), "local", self.stl, *extra],
                             check=True, capture_output=True, text=True).stdout
        return json.loads(out)

    def test_closed_cube(self):
        r = self.measure("--build-volume", "256,256,256")
        self.assertTrue(r["topology"]["closed_consistently_oriented"])
        self.assertEqual(r["topology"]["boundary_edge_count"], 0)
        self.assertEqual(r["topology"]["genus_if_single_closed_shell"], 0)
        self.assertAlmostEqual(r["enclosed_volume_mm3"], 8000, places=6)
        self.assertEqual(r["bounding_box_mm"]["extent"], [20, 20, 20])
        self.assertEqual(r["units"]["source"], "sidecar .stl.meta.json")
        self.assertTrue(r["checks"]["fits_build_volume"]["fits_some_axis_aligned_orientation"])

    def test_units_scale_the_same_file(self):
        r = self.measure("--units", "cm", "--build-volume", "150,150,150")
        self.assertEqual(r["bounding_box_mm"]["extent"], [200, 200, 200])
        self.assertFalse(r["checks"]["fits_build_volume"]["fits_some_axis_aligned_orientation"])

    def test_open_mesh_has_no_volume(self):
        tris = cad_measure.parse_stl(Path(self.stl).read_bytes())[:-1]
        r = cad_measure.measure_triangles(tris)
        self.assertFalse(r["topology"]["closed_consistently_oriented"])
        self.assertEqual(r["topology"]["boundary_edge_count"], 3)
        self.assertIsNone(r["enclosed_volume_mm3"])

    def test_wall_is_never_guessed(self):
        r = self.measure("--min-wall-mm", "0.8")
        self.assertEqual(r["checks"]["min_wall_mm"]["measured"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
