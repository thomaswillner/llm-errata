#!/usr/bin/env python3
"""Liveness check for the external sources cited in the documentation.

The prior-art claim is a dated statement about public sources. If a cited
source disappears or moves, the claim becomes unreproducible, so link rot is a
research-integrity fault rather than a cosmetic one.

Some publishers answer automated clients with 403, 405, or 429 while serving
the page normally to a browser. Those responses prove the host and path still
resolve, so they are reported as `blocked` rather than treated as failures.
A host that answers 404 or 410, or that fails to resolve, is a failure.

Exit codes
    0  every cited URL resolved (or was reachable but bot-blocked)
    1  at least one cited URL is dead
    2  inconclusive: no URL could be reached at all, which means the network or
       DNS is unavailable and this run proves nothing either way
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TIMEOUT_SECONDS = 30
MAX_WORKERS = 8

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

# Status codes that prove the resource exists but the client was filtered.
BLOCKED_STATUSES = frozenset({401, 403, 405, 406, 429, 503})

URL_PATTERN = re.compile(r"https?://[^\s)>\"'\]]+")


def cited_urls() -> dict[str, list[str]]:
    """Map each cited URL to the documents that cite it."""

    found: dict[str, set[str]] = {}
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for match in URL_PATTERN.finditer(text):
            url = match.group(0).rstrip(".,;:")
            found.setdefault(url, set()).add(path.relative_to(ROOT).as_posix())
    return {url: sorted(sources) for url, sources in sorted(found.items())}


def probe(url: str) -> tuple[str, str]:
    """Return ``(state, detail)`` where state is ok, blocked, dead, or error."""

    for method in ("HEAD", "GET"):
        request = urllib.request.Request(
            url, method=method, headers={"User-Agent": USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return "ok", f"{response.status} {method}"
        except urllib.error.HTTPError as error:
            if error.code in BLOCKED_STATUSES:
                return "blocked", f"{error.code} {method} (client filtered)"
            if method == "GET":
                return "dead", f"{error.code} {method}"
        except urllib.error.URLError as error:
            if method == "GET":
                return "error", f"{type(error).__name__}: {error.reason}"
        except (TimeoutError, OSError) as error:
            if method == "GET":
                return "error", f"{type(error).__name__}: {error}"
    return "error", "no conclusive response"


def main() -> int:
    targets = cited_urls()
    if not targets:
        print("No external URLs found in the documentation.")
        return 2

    print(f"Checking {len(targets)} cited URLs\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        results = dict(zip(targets, pool.map(probe, targets)))

    dead: list[str] = []
    errors: list[str] = []
    reached = 0

    for url, (state, detail) in results.items():
        label = {"ok": "OK", "blocked": "BLOCKED", "dead": "DEAD", "error": "ERROR"}[state]
        print(f"[{label:>7}] {url}  ({detail})")
        if state in {"ok", "blocked"}:
            reached += 1
        elif state == "dead":
            dead.append(f"{url} — cited in {', '.join(targets[url])} — {detail}")
        else:
            errors.append(f"{url} — {detail}")

    print()
    if reached == 0:
        print(
            "Inconclusive: not a single URL was reachable. Treat this as a network "
            "or DNS failure, not as evidence about the sources."
        )
        return 2

    if dead:
        print(f"Dead links: {len(dead)} of {len(targets)}")
        for entry in dead:
            print(f"  - {entry}")
        print(
            "\nUpdate the citation, or record the loss in SOURCES.md with an archive "
            "snapshot. A dated prior-art claim cannot rest on a URL that no longer "
            "resolves."
        )
        return 1

    if errors:
        print(f"Unreachable (network-level) for {len(errors)} of {len(targets)}:")
        for entry in errors:
            print(f"  - {entry}")
        print("\nRe-run before drawing any conclusion about these sources.")
        return 1

    print(f"All {len(targets)} cited URLs resolved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
