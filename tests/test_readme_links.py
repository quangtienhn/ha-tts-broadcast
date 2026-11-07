"""Tests that image links in the README files point to existing files."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READMES = [ROOT / "README.md", ROOT / "README.vi.md"]

_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def _readme_image_targets() -> list[tuple[Path, str, str]]:
    """Return (readme, link_target, line) for every image link in the READMEs."""
    targets: list[tuple[Path, str, str]] = []
    for readme in READMES:
        text = readme.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in _IMAGE_RE.finditer(line):
                target = match.group(1)
                # Ignore absolute URLs (external images).
                if target.startswith("http://") or target.startswith("https://"):
                    continue
                targets.append((readme, target, f"{readme.name}:{lineno}"))
    return targets


def test_readme_image_links_point_to_existing_files() -> None:
    """Every relative image link in the READMEs must point to an existing file."""
    missing: list[str] = []
    for readme, target, where in _readme_image_targets():
        resolved = (readme.parent / target).resolve()
        if not resolved.exists():
            missing.append(f"{where}: {target} -> {resolved}")
    assert not missing, "\n".join(sorted(missing))
