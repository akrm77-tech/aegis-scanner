from pathlib import Path
import py_compile
import unittest


class SourceSyntaxTests(unittest.TestCase):
    def test_main_source_compiles(self):
        source = Path(__file__).parents[1] / "src" / "aegis-scanner.py"
        py_compile.compile(str(source), doraise=True)


if __name__ == "__main__":
    unittest.main()
