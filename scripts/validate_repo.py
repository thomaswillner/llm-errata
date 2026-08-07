#!/usr/bin/env python3
"""Deterministic, dependency-free linting for the LLM Errata repository.

Scope: repository structure, encoding, Markdown well-formedness, link
resolution, licence, and release metadata. These are mechanical properties.

Out of scope: whether the documentation still states the bounded claim. Keyword
presence over the concatenated corpus cannot tell a hedge from its inversion,
so that question belongs to `claim_guard.py`, which anchors to exact sentences
in named files and is itself proved by negative tests in `tests/`.

Run both, plus the self-tests, with `make check`.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "IDEA.md",
    "RESEARCH.md",
    "PRIOR_ART.md",
    "SOURCES.md",
    "ROADMAP.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CITATION.cff",
    "CHANGELOG.md",
    "PUBLISHING.md",
    "VERSION",
    "LICENSE",
    "NOTICE",
    "Makefile",
    "scripts/validate_repo.py",
    "scripts/claim_guard.py",
    "scripts/check_links.py",
    "tests/test_validate_repo.py",
    "tests/test_claim_guard.py",
    ".github/workflows/validate.yml",
    "prototype/README.md",
    "prototype/controller.py",
    "prototype/adapters.py",
    "prototype/errata.py",
    "tests/test_controller.py",
    "tests/test_demo.py",
)

TEXT_SUFFIXES = {
    ".cff",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

TEXT_NAMES = {".gitignore", "LICENSE", "NOTICE", "VERSION"}

CANONICAL_LINKS = {
    "Karpathy LLM Wiki idea file": (
        "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f"
    ),
    "OpenAI Memory FAQ": "https://help.openai.com/en/articles/8590148-memory-faq",
    "vCon Lifecycle using SCITT": (
        "https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01"
    ),
    "W3C PROV-DM": "https://www.w3.org/TR/prov-dm/",
}

LOCAL_PATH_PATTERNS = (
    (
        "sandbox URI",
        re.compile(r"sandbox:/", re.IGNORECASE),
    ),
    (
        "file URI",
        re.compile(r"file://", re.IGNORECASE),
    ),
    (
        "local Unix path",
        re.compile(
            r"(?<![A-Za-z0-9._-])/(?:workspace|root|home|Users|tmp)(?:/|\b)"
        ),
    ),
    (
        "local Windows path",
        re.compile(r"\b[A-Za-z]:\\(?:Users|workspace|temp|tmp)(?:\\|\b)"),
    ),
)


class Reporter:
    """Collect checks and render stable, actionable output."""

    def __init__(self) -> None:
        self.passed = 0
        self.failures: list[str] = []

    def pass_check(self, name: str, detail: str) -> None:
        self.passed += 1
        print(f"[PASS] {name}: {detail}")

    def fail_check(self, name: str, detail: str, fix: str) -> None:
        self.failures.append(name)
        print(f"[FAIL] {name}: {detail}")
        print(f"       Fix: {fix}")

    def check(self, name: str, condition: bool, detail: str, fix: str) -> None:
        if condition:
            self.pass_check(name, detail)
        else:
            self.fail_check(name, "requirement was not satisfied", fix)

    def finish(self) -> int:
        total = self.passed + len(self.failures)
        if self.failures:
            names = ", ".join(self.failures)
            print(
                f"\nValidation failed: {len(self.failures)} of {total} checks failed "
                f"({names})."
            )
            return 1
        print(f"\nValidation passed: all {total} checks succeeded.")
        return 0


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_text_files() -> Iterable[Path]:
    for path in sorted(ROOT.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES:
            yield path


def markdown_fence_error(text: str) -> str | None:
    """Return an actionable error for an unclosed Markdown fence, if present."""

    opening: tuple[str, int, int] | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if match is None:
            continue
        marker = match.group(1)
        remainder = match.group(2)
        if opening is None:
            opening = (marker[0], len(marker), line_number)
            continue
        character, minimum_length, opening_line = opening
        if marker[0] == character and len(marker) >= minimum_length and not remainder.strip():
            opening = None

    if opening is None:
        return None
    character, minimum_length, opening_line = opening
    marker = character * minimum_length
    return f"fence opened on line {opening_line} has no closing {marker}"


def cff_scalar(text: str, field: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(field)}:\s*(.*?)\s*$", text)
    if match is None:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value or None


def check_required_files(reporter: Reporter) -> None:
    missing = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
    reporter.check(
        "required files",
        not missing,
        "all required public-repository files are present",
        "Create the missing files: " + ", ".join(missing),
    )


def check_version(reporter: Reporter) -> str | None:
    path = ROOT / "VERSION"
    if not path.is_file():
        return None
    raw = read_utf8(path)
    version = raw.strip()
    reporter.check(
        "VERSION",
        re.fullmatch(r"\d+\.\d+\.\d+", version) is not None and raw.endswith("\n"),
        f"VERSION is {version!r}",
        "Set VERSION to a bare MAJOR.MINOR.PATCH string followed by a newline.",
    )
    return version


def check_canonical_links(reporter: Reporter) -> None:
    markdown_paths = sorted(ROOT.rglob("*.md"), key=lambda item: item.as_posix())
    documents = {relative(path): read_utf8(path) for path in markdown_paths}

    for label, url in CANONICAL_LINKS.items():
        locations = sorted(name for name, text in documents.items() if url in text)
        reporter.check(
            f"canonical link — {label}",
            bool(locations),
            f"found in {', '.join(locations)}" if locations else "not found",
            f"Add the canonical primary link {url} to the appropriate research document.",
        )


def check_markdown_fences(reporter: Reporter) -> None:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.md"), key=lambda item: item.as_posix()):
        error = markdown_fence_error(read_utf8(path))
        if error is not None:
            errors.append(f"{relative(path)}: {error}")
    reporter.check(
        "Markdown fences",
        not errors,
        "all Markdown code fences are balanced",
        "Close each unmatched fence. " + "; ".join(errors),
    )


def check_trailing_whitespace(reporter: Reporter) -> None:
    violations: list[str] = []
    for path in iter_text_files():
        try:
            lines = read_utf8(path).splitlines()
        except UnicodeDecodeError:
            violations.append(f"{relative(path)}: not valid UTF-8")
            continue
        for line_number, line in enumerate(lines, start=1):
            if line.endswith((" ", "\t")):
                violations.append(f"{relative(path)}:{line_number}")

    preview = ", ".join(violations[:10])
    if len(violations) > 10:
        preview += f", and {len(violations) - 10} more"
    reporter.check(
        "trailing whitespace",
        not violations,
        "no trailing spaces or tabs in repository text files",
        "Remove trailing whitespace at: " + preview,
    )


def check_local_paths(reporter: Reporter) -> None:
    violations: list[str] = []
    document_paths = sorted(ROOT.rglob("*.md"), key=lambda item: item.as_posix())
    document_paths.append(ROOT / "CITATION.cff")
    for path in document_paths:
        if not path.is_file():
            continue
        for line_number, line in enumerate(read_utf8(path).splitlines(), start=1):
            for label, pattern in LOCAL_PATH_PATTERNS:
                if pattern.search(line):
                    violations.append(f"{relative(path)}:{line_number} ({label})")

    preview = ", ".join(violations[:10])
    if len(violations) > 10:
        preview += f", and {len(violations) - 10} more"
    reporter.check(
        "portable documentation paths",
        not violations,
        "documentation contains no absolute local paths or sandbox/file URIs",
        "Replace local paths with repository-relative paths at: " + preview,
    )


def check_local_links(reporter: Reporter) -> None:
    violations: list[str] = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in sorted(ROOT.rglob("*.md"), key=lambda item: item.as_posix()):
        for line_number, line in enumerate(read_utf8(path).splitlines(), start=1):
            for match in link_pattern.finditer(line):
                raw_target = match.group(1).strip().split(maxsplit=1)[0]
                if raw_target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = unquote(raw_target.split("#", maxsplit=1)[0])
                if not target:
                    continue
                candidate = (path.parent / target).resolve()
                if not candidate.is_relative_to(ROOT.resolve()):
                    violations.append(
                        f"{relative(path)}:{line_number} escapes repository ({raw_target})"
                    )
                elif not candidate.exists():
                    violations.append(
                        f"{relative(path)}:{line_number} missing target ({raw_target})"
                    )

    preview = ", ".join(violations[:10])
    if len(violations) > 10:
        preview += f", and {len(violations) - 10} more"
    reporter.check(
        "repository-relative links",
        not violations,
        "all repository-relative Markdown links resolve",
        "Repair broken or escaping links at: " + preview,
    )


def check_publication_metadata(reporter: Reporter) -> None:
    readme_path = ROOT / "README.md"
    license_path = ROOT / "LICENSE"
    notice_path = ROOT / "NOTICE"
    if not all(path.is_file() for path in (readme_path, license_path, notice_path)):
        return

    readme = read_utf8(readme_path).casefold()
    required_readme = (
        "thomas rainer willner",
        "request for comment",
        "independent proposal",
        "ai-assisted research",
    )
    reporter.check(
        "publication metadata",
        all(value in readme for value in required_readme),
        "README contains authorship, status, independence, and AI-assistance disclosure",
        "Add the author, RFC status, independent-publication disclaimer, and AI-assisted research disclosure to README.md.",
    )

    license_text = read_utf8(license_path)
    notice_text = read_utf8(notice_path)
    reporter.check(
        "license and notice",
        "Apache License" in license_text
        and "Version 2.0" in license_text
        and "Copyright 2026 Thomas Rainer Willner" in license_text
        and "Copyright 2026 Thomas Rainer Willner" in notice_text,
        "Apache-2.0 license and author notice are present",
        "Restore the Apache License 2.0 text and Thomas Rainer Willner copyright notice.",
    )


def check_citation(reporter: Reporter, repository_version: str | None) -> None:
    path = ROOT / "CITATION.cff"
    if not path.is_file():
        return
    text = read_utf8(path)

    required_scalars = (
        "cff-version",
        "message",
        "title",
        "type",
        "version",
        "date-released",
        "license",
    )
    values = {field: cff_scalar(text, field) for field in required_scalars}
    missing = [field for field, value in values.items() if value is None]
    reporter.check(
        "CITATION.cff required fields",
        not missing,
        "all basic scalar fields are populated",
        "Add non-empty top-level fields: " + ", ".join(missing),
    )

    has_authors = re.search(r"(?m)^authors:\s*$", text) is not None
    has_family = re.search(r"(?m)^\s*-\s+family-names:\s*\S", text) is not None
    has_given = re.search(r"(?m)^\s+given-names:\s*\S", text) is not None
    reporter.check(
        "CITATION.cff author",
        has_authors and has_family and has_given,
        "authors includes given-names and family-names",
        "Add an authors list with at least one entry containing family-names and given-names.",
    )

    cff_version = values.get("cff-version")
    reporter.check(
        "CITATION.cff schema version",
        cff_version == "1.2.0",
        f"cff-version is {cff_version!r}",
        "Set cff-version to 1.2.0.",
    )

    citation_version = values.get("version")
    reporter.check(
        "CITATION.cff release version",
        citation_version is not None and citation_version == repository_version,
        f"citation version {citation_version!r} matches VERSION {repository_version!r}",
        "Set CITATION.cff version to the same value as VERSION.",
    )

    released = values.get("date-released")
    valid_date = False
    if released is not None:
        try:
            date.fromisoformat(released)
            valid_date = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", released))
        except ValueError:
            valid_date = False
    reporter.check(
        "CITATION.cff release date",
        valid_date,
        f"date-released is {released!r}",
        "Use a valid ISO 8601 calendar date in YYYY-MM-DD form.",
    )

    title = values.get("title") or ""
    reporter.check(
        "CITATION.cff title",
        "llm errata" in title.casefold(),
        f"title is {title!r}",
        "Set the citation title to LLM Errata or a title containing that project name.",
    )


def main() -> int:
    reporter = Reporter()
    print(f"Validating LLM Errata repository: {ROOT.name}\n")

    check_required_files(reporter)
    repository_version = check_version(reporter)
    check_canonical_links(reporter)
    check_markdown_fences(reporter)
    check_trailing_whitespace(reporter)
    check_local_paths(reporter)
    check_local_links(reporter)
    check_publication_metadata(reporter)
    check_citation(reporter, repository_version)
    return reporter.finish()


if __name__ == "__main__":
    sys.exit(main())
