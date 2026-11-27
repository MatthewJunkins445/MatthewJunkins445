"""Patch the bundled github-profile-3d-contrib action so it can draw one month.

The action (pinned in .github/workflows/profile-3d.yml) only knows two ranges:
the last 12 months, or one calendar year via YEAR. It also draws every bar at
1/64 of the image width, so a 5-week month would be a tiny cluster in a corner.

This script edits dist/index.js in place and adds optional env vars:
  CONTRIB_FROM / CONTRIB_TO   date range, YYYY-MM-DD (UTC), e.g. the current month
  CONTRIB_CELLS               image width / CONTRIB_CELLS = bar size (default 64)
  CONTRIB_OFFSET_X / _Y       where the first bar is drawn (default: the action's own)

With none of them set, the action behaves exactly as before. Every edit must
match exactly once, so if the pinned version ever changes the script fails
loudly instead of producing a wrong graph.

Usage: python3 patch_3d_contrib.py path/to/dist/index.js
"""

import sys
from pathlib import Path

PATCHES = [
    (
        "const yearArgs = year\n",
        "const yearArgs = process.env.CONTRIB_FROM\n"
        "        ? `(from:\"${process.env.CONTRIB_FROM}T00:00:00.000Z\", "
        "to:\"${process.env.CONTRIB_TO}T23:59:59.000Z\")`\n"
        "        : year\n",
    ),
    (
        "const dx = width / 64;",
        "const dx = width / Number(process.env.CONTRIB_CELLS || 64);",
    ),
    (
        "const offsetX = dx * 7;",
        "const offsetX = process.env.CONTRIB_OFFSET_X"
        " ? Number(process.env.CONTRIB_OFFSET_X) : dx * 7;",
    ),
    (
        "const offsetY = height - (weekcount + 7) * dy;",
        "const offsetY = process.env.CONTRIB_OFFSET_Y"
        " ? Number(process.env.CONTRIB_OFFSET_Y) : height - (weekcount + 7) * dy;",
    ),
]


def main() -> None:
    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    for old, new in PATCHES:
        count = source.count(old)
        if count != 1:
            sys.exit(f"patch_3d_contrib: expected 1 match for {old!r}, found {count}")
        source = source.replace(old, new)
    path.write_text(source, encoding="utf-8")
    print(f"patch_3d_contrib: patched {path}")


if __name__ == "__main__":
    main()
