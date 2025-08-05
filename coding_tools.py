from libcst import parse_module, MetadataWrapper
import subprocess
import difflib
import pathlib
from typing import List

class CodeTools:
    @staticmethod
    def ast_check(file: str) -> str:
        """Return 'OK' or syntax error."""
        try:
            parse_module(pathlib.Path(file).read_text())
            return "OK"
        except Exception as e:
            return str(e)

    @staticmethod
    def run_tests(path: str | pathlib.Path = ".") -> str:
        """Run pytest and capture output."""
        return subprocess.check_output([
            "pytest",
            str(path),
            "-q",
        ], text=True, stderr=subprocess.STDOUT)

    @staticmethod
    def diff(old: str, new: str) -> str:
        """Return unified diff string."""
        return "\n".join(
            difflib.unified_diff(
                old.splitlines(), new.splitlines(), lineterm=""
            )
        )
