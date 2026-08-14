#!/usr/bin/env python3
"""Regenerates Casks/my-apps-library.rb's version/sha256 fields in place —
run by .github/workflows/release.yml's update-homebrew-tap job after every
release. Targeted regex substitution, not a full re-render, so the
formula's hand-written comments/formatting survive untouched (the same
approach the marketplace's mal-plugin CLI uses for plugin.toml, and for
the same reason).

Fails loudly (non-zero exit) if a pattern doesn't match exactly once,
rather than silently leaving the file unchanged or corrupting it — a
CI script editing a file in place should never fail quietly.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="e.g. 0.6.0 (no leading v)")
    parser.add_argument("--arm-sha256", required=True)
    parser.add_argument("--intel-sha256", required=True)
    parser.add_argument(
        "--cask-path",
        default=str(Path(__file__).resolve().parents[2] / "Casks" / "my-apps-library.rb"),
    )
    args = parser.parse_args()

    for name, sha in (("--arm-sha256", args.arm_sha256), ("--intel-sha256", args.intel_sha256)):
        if not re.fullmatch(r"[0-9a-fA-F]{64}", sha):
            sys.exit(f"{name} doesn't look like a sha256 hex digest: {sha!r}")

    path = Path(args.cask_path)
    text = path.read_text()

    text, n_version = re.subn(r'version "[^"]*"', f'version "{args.version}"', text, count=1)
    text, n_arm = re.subn(
        r'arm:\s+"[0-9a-fA-F]{64}"', f'arm:   "{args.arm_sha256}"', text, count=1
    )
    text, n_intel = re.subn(
        r'intel: "[0-9a-fA-F]{64}"', f'intel: "{args.intel_sha256}"', text, count=1
    )

    if (n_version, n_arm, n_intel) != (1, 1, 1):
        sys.exit(
            f"Expected exactly one match each for version/arm/intel, got "
            f"{n_version}/{n_arm}/{n_intel} — did the Cask's formatting change? "
            f"Update this script's regexes to match."
        )

    path.write_text(text)
    print(f"Updated {path}: version={args.version}")


if __name__ == "__main__":
    main()
