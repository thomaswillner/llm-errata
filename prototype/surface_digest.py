"""Canonical Phase 2 surface manifest and byte-preserving digest helpers."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


REQUIRED_TESTS = (
    "tests/test_adapters.py",
    "tests/test_checkpoints.py",
    "tests/test_cli.py",
    "tests/test_conformance.py",
    "tests/test_controller.py",
    "tests/test_ed25519.py",
    "tests/test_errata_feed.py",
    "tests/test_schema.py",
    "tests/test_semantic.py",
    "tests/test_sqlite_store.py",
)
REQUIRED_EVIDENCE_CONTRACT = "docs/READINESS_EVIDENCE_SCHEMAS.md"
CORPUS_PATH = "spec/adapter-conformance.json"
GIT_TIMEOUT_SECONDS = 10.0


class SurfaceDigestError(OSError):
    """Source bytes cannot support a canonical surface digest."""


def surface_digest_from_bytes(entries: list[tuple[str, bytes]]) -> str:
    """Hash ordered path and content pairs without changing their bytes."""

    digest = hashlib.sha256()
    for relative, content in entries:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _object_end(text: str, start: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        token = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif token == "\\":
                escaped = True
            elif token == '"':
                in_string = False
            continue
        if token == '"':
            in_string = True
        elif token == "{":
            depth += 1
        elif token == "}":
            depth -= 1
            if depth == 0:
                return index
    raise SurfaceDigestError("conformance corpus target metadata is malformed")


def normalize_corpus_target(content: bytes) -> bytes:
    """Zero only target scalar values while preserving every other UTF-8 byte."""

    try:
        text = content.decode("utf-8")
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
        target = payload["normative_target"]
        if not isinstance(payload, dict) or not isinstance(target, dict):
            raise TypeError
        if set(target) != {"commit", "surface_digest"}:
            raise TypeError
        if re.fullmatch(r"[0-9a-f]{40}", target["commit"]) is None:
            raise TypeError
        if re.fullmatch(r"[0-9a-f]{64}", target["surface_digest"]) is None:
            raise TypeError
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise SurfaceDigestError("conformance corpus target metadata is malformed") from error

    target_markers = list(re.finditer(r'"normative_target"\s*:\s*\{', text))
    if len(target_markers) != 1:
        raise SurfaceDigestError("conformance corpus target metadata is malformed")
    start = target_markers[0].end() - 1
    end = _object_end(text, start)
    block = text[start : end + 1]
    replacements: list[tuple[int, int, str]] = []
    for key, width in (("commit", 40), ("surface_digest", 64)):
        matches = list(re.finditer(
            rf'"{key}"\s*:\s*"([0-9a-f]{{{width}}})"', block
        ))
        if len(matches) != 1:
            raise SurfaceDigestError("conformance corpus target metadata is malformed")
        replacements.append((
            start + matches[0].start(1),
            start + matches[0].end(1),
            "0" * width,
        ))
    for value_start, value_end, replacement in sorted(replacements, reverse=True):
        text = text[:value_start] + replacement + text[value_end:]
    return text.encode("utf-8")


def review_surface_content(relative: str, content: bytes) -> bytes:
    """Normalize the canonical corpus target and leave every other file verbatim."""

    return normalize_corpus_target(content) if relative == CORPUS_PATH else content


def _paths_from_files(files: set[str]) -> tuple[str, ...]:
    groups = (
        tuple(sorted(path for path in files if re.fullmatch(r"prototype/[^/]+\.py", path))),
        ("prototype/README.md", "spec/README.md"),
        (CORPUS_PATH,),
        tuple(sorted(path for path in files if re.fullmatch(r"spec/[^/]+\.schema\.json", path))),
        tuple(sorted(path for path in files if re.fullmatch(r"spec/vectors/[^/]+\.json", path))),
        tuple(sorted(path for path in files if re.fullmatch(r"spec/semantic/[^/]+\.json", path))),
        (
            "ROADMAP.md", "THREAT_MODEL.md", "SECURITY.md",
            "INDEPENDENT_IMPLEMENTATION.md", "REVIEW_REQUEST.md",
            REQUIRED_EVIDENCE_CONTRACT,
        ),
        REQUIRED_TESTS,
    )
    if any(not group for group in groups):
        raise SurfaceDigestError("canonical G2 surface is incomplete")
    paths = tuple(sorted(item for group in groups for item in group))
    if CORPUS_PATH not in files:
        raise SurfaceDigestError("reviewed commit predates the conformance corpus")
    if any(path not in files for path in paths):
        raise SurfaceDigestError("canonical G2 surface is incomplete")
    return paths


def g2_surface_files(root: Path) -> tuple[str, ...]:
    files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }
    return _paths_from_files(files)


def _git(root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise SurfaceDigestError("Git source verification timed out") from error
    if result.returncode != 0:
        raise SurfaceDigestError("reviewed commit is unavailable")
    return result.stdout


def g2_surface_files_at_commit(root: Path, commit: str) -> tuple[str, ...]:
    files = set(
        _git(root, "ls-tree", "-r", "--name-only", commit).decode("utf-8").splitlines()
    )
    return _paths_from_files(files)


def g2_surface_digest(root: Path) -> str:
    return surface_digest_from_bytes([
        (relative, review_surface_content(relative, (root / relative).read_bytes()))
        for relative in g2_surface_files(root)
    ])


def g2_surface_digest_at_commit(root: Path, commit: str) -> str:
    return surface_digest_from_bytes([
        (
            relative,
            review_surface_content(relative, _git(root, "show", f"{commit}:{relative}")),
        )
        for relative in g2_surface_files_at_commit(root, commit)
    ])
