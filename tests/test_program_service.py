from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from halcon1811_mcp.program_service import ProgramService, normalized_code, program_name


class ProgramServiceTests(unittest.TestCase):
    def test_names_cannot_escape_save_directory(self):
        for name in ("../outside", "C:/outside", "a/b", "a\\b", ""):
            with self.subTest(name=name), self.assertRaises(ValueError):
                program_name(name)

    def test_reject_markdown_and_xml(self):
        for code in ("```halcon\nread_image(Image,'x')\n```", "<hdevelop/>", ""):
            with self.subTest(code=code), self.assertRaises(ValueError):
                normalized_code(code)

    def test_saved_versions_preserve_code_and_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            service = ProgramService(Path(directory))
            source = "* 中文需求\nthreshold (Image, Region, 128, 255)\n"
            a = service.save("阈值分割", source, "分割亮区域", "采用固定阈值", open_window=False)
            b = service.save("阈值分割", source, open_window=False)
            self.assertNotEqual(a["script"], b["script"])
            self.assertTrue(a["saved"])
            self.assertFalse(a["opened"])
            self.assertEqual(Path(a["source"]).read_text(encoding="utf-8"), source)
            self.assertIn("采用固定阈值", Path(a["analysis_file"]).read_text(encoding="utf-8"))
            body = ET.parse(a["script"]).find("./procedure/body")
            self.assertEqual("\n".join(item.text or "" for item in body) + "\n", source)
            self.assertEqual(len(service.list_programs()), 2)

    def test_invalid_operator_path_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                ProgramService(Path(directory)).operator_help("../license")


if __name__ == "__main__":
    unittest.main()
