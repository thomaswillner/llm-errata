"""Shared helpers for the repository's self-tests.

Every test mutates a throwaway copy of the repository and asserts on the exit
code of a checker run against that copy. Nothing here writes to the working
tree.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_INCONCLUSIVE = 2

_IGNORED = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".venv")


@contextmanager
def repo_copy() -> Iterator[Path]:
    """Yield a disposable copy of the repository."""

    with tempfile.TemporaryDirectory(prefix="llm-errata-test-") as tmp:
        destination = Path(tmp) / "llm-errata"
        shutil.copytree(REPO_ROOT, destination, ignore=_IGNORED)
        yield destination


def run_checker(root: Path, script: str) -> subprocess.CompletedProcess[str]:
    """Run a checker from ``scripts/`` inside ``root`` and capture its output."""

    return subprocess.run(
        [sys.executable, str(root / "scripts" / script)],
        capture_output=True,
        text=True,
        check=False,
    )


def rewrite(path: Path, old: str, new: str) -> None:
    """Replace ``old`` with ``new``, failing loudly if ``old`` is absent.

    A mutation that silently does nothing would turn a negative test into a
    test that only proves the checker passes on unmodified input.
    """

    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"mutation target not found in {path.name}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def check_after(
    script: str, mutate: Callable[[Path], None]
) -> subprocess.CompletedProcess[str]:
    """Apply ``mutate`` to a repository copy, then run ``script`` against it."""

    with repo_copy() as root:
        mutate(root)
        return run_checker(root, script)
