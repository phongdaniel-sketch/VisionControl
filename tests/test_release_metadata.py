import re
import tomllib
import unittest
from pathlib import Path

from vision_control import __version__


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "1.0.0"


class ReleaseMetadataTests(unittest.TestCase):
    def test_python_and_package_versions_match(self):
        with (ROOT / "pyproject.toml").open("rb") as stream:
            package_version = tomllib.load(stream)["project"]["version"]
        self.assertEqual(package_version, EXPECTED_VERSION)
        self.assertEqual(__version__, EXPECTED_VERSION)

    def test_windows_resource_contains_file_and_product_versions(self):
        resource = (ROOT / "packaging" / "windows-version.txt").read_text(
            encoding="utf-8"
        )
        self.assertRegex(resource, re.compile(r"FileVersion'.*1\.0\.0\.0"))
        self.assertRegex(resource, re.compile(r"ProductVersion'.*1\.0\.0"))


if __name__ == "__main__":
    unittest.main()
