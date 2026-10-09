"""Pure generation checks. No HDevelop or GUI dependencies are needed."""
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from halcon1811_mcp.core import Parameters, build_source, halcon_string, prepare_job, write_hdev


class GenerationTests(unittest.TestCase):
    def test_invalid_parameters_are_rejected(self):
        for p in (Parameters(lower=200, upper=100), Parameters(min_area=float("nan")),
                  Parameters(min_area=-1), Parameters(mean_size=2)):
            with self.subTest(p=p), self.assertRaises(ValueError):
                p.validate()

    def test_xml_and_string_escaping_are_independent(self):
        source = build_source(Path("C:/images/O'Brien & <test>.png"), Path("C:/jobs/demo"), "abc", Parameters())
        self.assertIn("O\\'Brien", source)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.hdev"
            write_hdev(source, path)
            lines = ET.parse(path).findall("./procedure/body/l")
            reconstructed = "\n".join(item.text or "" for item in lines)
            self.assertIn("O\\'Brien & <test>.png", reconstructed)

    def test_completion_marker_follows_results(self):
        source = build_source(Path("C:/x.png"), Path("C:/jobs/run"), "token", Parameters())
        self.assertLess(source.index("write_image"), source.index("complete.txt"))
        self.assertLess(source.index("close_file (MetricsHandle)"), source.index("complete.txt"))
        self.assertIn("if (Number > 0)", source)

    def test_new_jobs_cannot_reuse_old_completion_files(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "input.png"
            image.write_bytes(b"fixture")  # Generation checks paths, not image decoding.
            a = prepare_job(str(image), Path(directory) / "jobs", Parameters())
            b = prepare_job(str(image), Path(directory) / "jobs", Parameters())
            self.assertNotEqual(a["token"], b["token"])
            self.assertNotEqual(a["job_dir"], b["job_dir"])
            self.assertFalse(Path(b["job_dir"], "complete.txt").exists())

    def test_control_characters_are_rejected(self):
        with self.assertRaises(ValueError):
            halcon_string("file\nname")


if __name__ == "__main__":
    unittest.main()
