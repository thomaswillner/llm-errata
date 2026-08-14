#!/usr/bin/env python3
"""Validate local publication metadata without pretending to verify GitHub."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from check_readiness import g2_surface_digest, g2_surface_digest_at_commit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "publication" / "active-surfaces.json"
CORPUS = ROOT / "spec" / "adapter-conformance.json"
REPOSITORY_URL = "https://github.com/thomaswillner/llm-errata"
ALLOWED_GATES = {"G2", "G3", "G4", "G5", "G6"}
REQUIRED_ATTRIBUTION = {"LLM Errata", "Thomas Willner", REPOSITORY_URL}
ALLOWED_PACKAGING_PATHS = {
    "publication/active-surfaces.json",
    "spec/adapter-conformance.json",
}

ROOT_KEYS = {
    "schema_version", "review_target", "release_binding", "license",
    "historical_surfaces", "surfaces",
}
TARGET_KEYS = {"commit", "surface_digest"}
RELEASE_KEYS = {"version", "tag", "allowed_packaging_paths", "commit_model"}
LICENSE_KEYS = {
    "specification_implementation", "required_attribution", "reference_code",
    "case_by_case_permission_required",
}
SURFACE_KEYS = {
    "id", "kind", "url", "published", "commit", "surface_digest", "gates",
    "roles", "mentions", "supersedes", "evidence_boundary",
}
HISTORICAL_SURFACE_KEYS = SURFACE_KEYS | {"superseded_by"}


def load_manifest(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_repository_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and parsed.path.startswith("/thomaswillner/llm-errata/")
        and not parsed.username
        and not parsed.password
    )


def _valid_date(value: object) -> bool:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        return date.fromisoformat(value) <= date.today()
    except ValueError:
        return False


def _valid_target(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == TARGET_KEYS
        and isinstance(value.get("commit"), str)
        and re.fullmatch(r"[0-9a-f]{40}", value["commit"]) is not None
        and isinstance(value.get("surface_digest"), str)
        and re.fullmatch(r"[0-9a-f]{64}", value["surface_digest"]) is not None
    )


def _validate_surface(
    surface: object,
    *,
    target: dict[str, str],
    historical: bool,
) -> list[str]:
    failures: list[str] = []
    expected_keys = HISTORICAL_SURFACE_KEYS if historical else SURFACE_KEYS
    if not isinstance(surface, dict) or set(surface) != expected_keys:
        return ["surface fields: exact versioned fields are required"]
    values = (surface.get("gates"), surface.get("roles"), surface.get("mentions"), surface.get("supersedes"))
    valid_lists = all(
        isinstance(value, list)
        and all(isinstance(item, str) and bool(item) for item in value)
        for value in values
    )
    boundary = surface.get("evidence_boundary")
    if not (
        isinstance(surface.get("id"), str)
        and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", surface["id"]) is not None
        and surface.get("kind") in {"issue-comment", "pull-request-comment", "discussion-comment"}
        and _is_repository_url(surface.get("url"))
        and _valid_date(surface.get("published"))
        and isinstance(surface.get("commit"), str)
        and re.fullmatch(r"[0-9a-f]{40}", surface["commit"]) is not None
        and isinstance(surface.get("surface_digest"), str)
        and re.fullmatch(r"[0-9a-f]{64}", surface["surface_digest"]) is not None
        and valid_lists
        and bool(surface["gates"])
        and len(surface["gates"]) == len(set(surface["gates"]))
        and set(surface["gates"]).issubset(ALLOWED_GATES)
        and len(surface["supersedes"]) == len(set(surface["supersedes"]))
        and all(_is_repository_url(item) for item in surface["supersedes"])
        and boundary in {"recruitment-only", "publication-only"}
    ):
        failures.append("surface fields: invalid ID, URL, date, target, gates, supersession, or boundary")
    if not historical and (
        surface.get("commit") != target["commit"]
        or surface.get("surface_digest") != target["surface_digest"]
    ):
        failures.append("surface target binding: active surfaces must bind the review target")
    if boundary == "recruitment-only" and not surface.get("roles"):
        failures.append("evidence boundary: recruitment surfaces require roles")
    if boundary == "publication-only" and (surface.get("roles") or surface.get("mentions")):
        failures.append("evidence boundary: publication surfaces cannot recruit or mention users")
    if historical and not _is_repository_url(surface.get("superseded_by")):
        failures.append("historical surfaces: superseded_by must be a repository URL")
    return failures


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


def validate_manifest(payload: object) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict) or set(payload) != ROOT_KEYS:
        return ["manifest schema: root must contain the exact required fields"]
    if payload.get("schema_version") != 3:
        failures.append("manifest schema: schema_version must be 3")

    target = payload.get("review_target")
    if not _valid_target(target):
        failures.append("review target: full commit and SHA-256 surface digest are required")
        target = {"commit": "", "surface_digest": ""}

    release = payload.get("release_binding")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not (
        isinstance(release, dict)
        and set(release) == RELEASE_KEYS
        and release.get("version") == version
        and release.get("tag") == f"v{version}"
        and release.get("allowed_packaging_paths") == sorted(ALLOWED_PACKAGING_PATHS)
        and release.get("commit_model")
        == "review target plus metadata-only packaging commit; tag binds release commit"
    ):
        failures.append("release binding: version, tag, commit model, and packaging paths must align")

    try:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        corpus_target = corpus["normative_target"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError):
        corpus_target = None
    if target != corpus_target:
        failures.append("review target: publication and conformance targets must be identical")

    license_data = payload.get("license")
    if not isinstance(license_data, dict) or set(license_data) != LICENSE_KEYS:
        failures.append("licence posture: exact licence fields are required")
    else:
        posture = license_data.get("specification_implementation")
        terms = {"irrevocable", "worldwide", "royalty-free", "commercial", "non-commercial"}
        if not (
            isinstance(posture, str)
            and all(term in posture.casefold() for term in terms)
            and license_data.get("case_by_case_permission_required") is False
            and "written" not in posture.casefold()
            and "permission" not in posture.casefold()
        ):
            failures.append("licence posture: implementation grant must not require case-by-case permission")
        attribution = license_data.get("required_attribution")
        if not (
            isinstance(attribution, list)
            and all(isinstance(item, str) for item in attribution)
            and set(attribution) == REQUIRED_ATTRIBUTION
            and len(attribution) == len(REQUIRED_ATTRIBUTION)
        ):
            failures.append("licence attribution: project, author, and repository are required exactly once")
        reference_code = license_data.get("reference_code")
        if not (
            isinstance(reference_code, str)
            and "personal-use" in reference_code.casefold()
            and all(path in reference_code for path in ("prototype/", "scripts/", "tests/"))
        ):
            failures.append("reference code boundary: personal-use code scope is required")

    surfaces = payload.get("surfaces")
    historical = payload.get("historical_surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        failures.append("required active surfaces: at least one current surface is required")
        surfaces = []
    if not isinstance(historical, list) or not historical:
        failures.append("historical surfaces: append-only superseded records are required")
        historical = []
    for surface in surfaces:
        failures.extend(_validate_surface(surface, target=target, historical=False))
    for surface in historical:
        failures.extend(_validate_surface(surface, target=target, historical=True))

    active_ids = [surface.get("id") for surface in surfaces if isinstance(surface, dict)]
    active_urls = [surface.get("url") for surface in surfaces if isinstance(surface, dict)]
    roles = [role for surface in surfaces if isinstance(surface, dict) for role in surface.get("roles", [])]
    mentions = [mention.casefold() for surface in surfaces if isinstance(surface, dict) for mention in surface.get("mentions", [])]
    if len(active_ids) != len(set(active_ids)) or len(active_urls) != len(set(active_urls)):
        failures.append("unique surface URLs: active IDs and URLs must not repeat")
    if len(roles) != len(set(roles)):
        failures.append("unique evidence roles: each active role needs one owner")
    if len(mentions) != len(set(mentions)):
        failures.append("unique GitHub mentions: each identity may be notified only once")

    if (ROOT / ".git").exists() and _valid_target(target):
        commit = target["commit"]
        ancestor = _git("merge-base", "--is-ancestor", commit, "HEAD")
        if ancestor.returncode != 0:
            failures.append("review target: commit must be an ancestor of runtime HEAD")
        try:
            if target["surface_digest"] != g2_surface_digest_at_commit(commit, ROOT):
                failures.append("review target: committed surface digest does not match")
            if target["surface_digest"] != g2_surface_digest(ROOT):
                failures.append("review target: runtime surface differs from reviewed source")
        except OSError as error:
            failures.append(f"review target: {error}")
        changed = _git("diff", "--name-only", f"{commit}..HEAD")
        if changed.returncode != 0:
            failures.append("release binding: packaging delta cannot be inspected")
        elif set(changed.stdout.splitlines()) - ALLOWED_PACKAGING_PATHS:
            failures.append("release binding: runtime contains non-packaging changes after review target")
    return failures


def _validate_tag(tag: str) -> tuple[int, str]:
    if not (ROOT / ".git").exists():
        return 2, "[INCONCLUSIVE] release tag: Git metadata is unavailable"
    resolved = _git("rev-parse", f"refs/tags/{tag}^{{commit}}")
    if resolved.returncode != 0:
        return 2, f"[INCONCLUSIVE] release tag: {tag} does not exist"
    head = _git("rev-parse", "HEAD")
    if resolved.stdout.strip() != head.stdout.strip():
        return 1, f"[FAIL] release tag: {tag} does not resolve to HEAD"
    return 0, f"[PASS] release tag: {tag} resolves to current release commit"


def main() -> int:
    args = sys.argv[1:]
    require_remote = "--require-remote" in args
    tag = None
    if "--tag" in args:
        index = args.index("--tag")
        if index + 1 >= len(args):
            print("[FAIL] release tag: --tag requires a value")
            return 1
        tag = args[index + 1]
    try:
        payload = load_manifest(MANIFEST)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"[INCONCLUSIVE] active publication manifest: {exc}")
        return 2

    failures = validate_manifest(payload)
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        print(f"\nPublication validation failed: {len(failures)} issue(s).")
        return 1

    print("[PASS] offline manifest consistency: local schema, target, licence, and evidence boundaries align")
    print("[UNVERIFIED] remote GitHub surfaces were not verified by this offline checker")
    if tag is not None:
        status, message = _validate_tag(tag)
        print(message)
        if status:
            return status
    if require_remote:
        print("[INCONCLUSIVE] remote publication state requires a fresh GitHub inventory receipt")
        return 2
    print("\nOffline publication metadata validation passed; remote state remains unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
