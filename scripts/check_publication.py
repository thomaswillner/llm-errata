#!/usr/bin/env python3
"""Validate the tracked active-publication-surface manifest offline."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "publication" / "active-surfaces.json"

CANONICAL_COMMIT = "ac4468faf73c2cc7949dd29b2a2a151f5bd23116"
CANONICAL_DIGEST = (
    "7e0d6c88c1ca3a87743ac70ba2a3dfea0b350d112d2d3c59a3c6cbb537568f12"
)
REPOSITORY_URL = "https://github.com/thomaswillner/llm-errata"
ALLOWED_GATES = {"G2", "G3", "G4", "G5", "G6"}
REQUIRED_ATTRIBUTION = {"LLM Errata", "Thomas Willner", REPOSITORY_URL}
REQUIRED_SURFACES = {
    "g4-inspeximus-current-target-reply": {
        "kind": "issue-comment",
        "url": f"{REPOSITORY_URL}/issues/4#issuecomment-5282207719",
        "gates": ["G2", "G4"],
        "roles": ["inspeximus-adapter-author"],
        "mentions": ["DanceNitra"],
        "evidence_boundary": "recruitment-only",
    },
}

ROOT_KEYS = {"schema_version", "review_target", "license", "surfaces"}
TARGET_KEYS = {"commit", "surface_digest"}
LICENSE_KEYS = {
    "specification_implementation",
    "required_attribution",
    "reference_code",
    "case_by_case_permission_required",
}
SURFACE_KEYS = {
    "id",
    "kind",
    "url",
    "published",
    "commit",
    "surface_digest",
    "gates",
    "roles",
    "mentions",
    "supersedes",
    "evidence_boundary",
}


def load_manifest(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(payload: object) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict) or set(payload) != ROOT_KEYS:
        return ["manifest schema: root must contain the exact required fields"]

    if payload.get("schema_version") != 1:
        failures.append("manifest schema: schema_version must be 1")

    target = payload.get("review_target")
    target_valid = (
        isinstance(target, dict)
        and set(target) == TARGET_KEYS
        and target.get("commit") == CANONICAL_COMMIT
        and target.get("surface_digest") == CANONICAL_DIGEST
    )
    if not target_valid:
        failures.append(
            "review target: commit and digest must equal the corrected canonical target"
        )

    license_data = payload.get("license")
    if not isinstance(license_data, dict) or set(license_data) != LICENSE_KEYS:
        failures.append("licence posture: exact licence fields are required")
    else:
        posture = license_data.get("specification_implementation")
        posture_terms = {
            "irrevocable",
            "worldwide",
            "royalty-free",
            "commercial",
            "non-commercial",
        }
        posture_valid = (
            isinstance(posture, str)
            and all(term in posture.casefold() for term in posture_terms)
            and license_data.get("case_by_case_permission_required") is False
            and "written" not in posture.casefold()
            and "permission" not in posture.casefold()
        )
        if not posture_valid:
            failures.append(
                "licence posture: attributed independent implementation grant must not require case-by-case permission"
            )

        attribution = license_data.get("required_attribution")
        if (
            not isinstance(attribution, list)
            or any(not isinstance(item, str) for item in attribution)
            or set(attribution) != REQUIRED_ATTRIBUTION
            or len(attribution) != len(REQUIRED_ATTRIBUTION)
        ):
            failures.append(
                "licence attribution: LLM Errata, Thomas Willner, and repository URL are required exactly once"
            )

        reference_code = license_data.get("reference_code")
        if not (
            isinstance(reference_code, str)
            and "personal-use" in reference_code.casefold()
            and all(
                path in reference_code
                for path in ("prototype/", "scripts/", "tests/")
            )
        ):
            failures.append(
                "reference code boundary: personal-use prototype/, scripts/, and tests/ scope is required"
            )

    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, list):
        failures.append("required active surfaces: surfaces must be a list")
        return failures

    surface_ids: list[str] = []
    surface_urls: list[str] = []
    roles: list[str] = []
    mentions: list[str] = []
    for index, surface in enumerate(surfaces):
        label = f"surface fields: entry {index + 1}"
        if not isinstance(surface, dict) or set(surface) != SURFACE_KEYS:
            failures.append(f"{label} must contain the exact required fields")
            continue

        surface_id = surface.get("id")
        kind = surface.get("kind")
        url = surface.get("url")
        published = surface.get("published")
        gates = surface.get("gates")
        entry_roles = surface.get("roles")
        entry_mentions = surface.get("mentions")
        supersedes = surface.get("supersedes")
        boundary = surface.get("evidence_boundary")

        expected = REQUIRED_SURFACES.get(surface_id) if isinstance(surface_id, str) else None
        valid_date = False
        if isinstance(published, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", published):
            try:
                valid_date = date.fromisoformat(published) <= date.today()
            except ValueError:
                valid_date = False
        valid_url = isinstance(url, str) and _is_repository_url(url)
        valid_string_list_fields = all(
            isinstance(value, list)
            and all(isinstance(item, str) and item for item in value)
            for value in (gates, entry_roles, entry_mentions, supersedes)
        )
        valid_gates = (
            isinstance(gates, list)
            and bool(gates)
            and len(gates) == len(set(gates))
            and set(gates).issubset(ALLOWED_GATES)
        )
        valid_supersedes = (
            isinstance(supersedes, list)
            and bool(supersedes)
            and len(supersedes) == len(set(supersedes))
            and all(_is_repository_url(item) for item in supersedes)
        )
        expected_fields_match = expected is not None and all(
            surface.get(field) == value for field, value in expected.items()
        )
        if not (
            isinstance(surface_id, str)
            and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", surface_id)
            and kind in {"issue-comment", "pull-request-comment", "discussion-comment"}
            and valid_url
            and valid_date
            and valid_string_list_fields
            and valid_gates
            and valid_supersedes
            and boundary in {"recruitment-only", "publication-only"}
            and expected_fields_match
        ):
            failures.append(
                f"{label} has invalid or non-canonical ID, kind, URL, date, gates, roles, mentions, supersession, or boundary"
            )

        if (
            surface.get("commit") != CANONICAL_COMMIT
            or surface.get("surface_digest") != CANONICAL_DIGEST
        ):
            failures.append(
                f"surface target binding: {surface_id!r} must bind canonical commit and digest"
            )

        if boundary == "recruitment-only" and not entry_roles:
            failures.append(
                f"evidence boundary: recruitment surface {surface_id!r} requires roles"
            )
        if boundary == "publication-only" and (entry_roles or entry_mentions):
            failures.append(
                f"evidence boundary: publication surface {surface_id!r} cannot recruit or mention users"
            )
        if boundary not in {"recruitment-only", "publication-only"}:
            failures.append(
                f"evidence boundary: {surface_id!r} cannot represent invitation or publication as independent evidence"
            )

        if isinstance(surface_id, str):
            surface_ids.append(surface_id)
        if isinstance(url, str):
            surface_urls.append(url)
        if isinstance(entry_roles, list):
            roles.extend(item for item in entry_roles if isinstance(item, str))
        if isinstance(entry_mentions, list):
            mentions.extend(item.casefold() for item in entry_mentions if isinstance(item, str))

    if set(surface_ids) != set(REQUIRED_SURFACES) or len(surface_ids) != len(REQUIRED_SURFACES):
        failures.append(
            "required active surfaces: manifest must contain each canonical active surface exactly once"
        )
    if len(surface_urls) != len(set(surface_urls)):
        failures.append("unique surface URLs: active surface URLs must not repeat")
    if len(roles) != len(set(roles)):
        failures.append("unique evidence roles: each evidence role needs one owner")
    if len(mentions) != len(set(mentions)):
        failures.append("unique GitHub mentions: each identity may be notified only once")

    active_url_set = set(surface_urls)
    for surface in surfaces:
        if isinstance(surface, dict) and isinstance(surface.get("supersedes"), list):
            if active_url_set.intersection(surface["supersedes"]):
                failures.append(
                    "surface fields: active surface URL cannot also be superseded"
                )
                break

    return failures


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


def main() -> int:
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

    print("[PASS] manifest schema: exact versioned fields")
    print("[PASS] review target: corrected immutable commit and digest")
    print("[PASS] licence posture: implementation rights and attribution aligned")
    print("[PASS] active surfaces: required URLs, roles, mentions, and boundaries")
    print("\nPublication validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
