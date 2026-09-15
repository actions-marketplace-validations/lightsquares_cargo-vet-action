#!/usr/bin/env python3
"""Download the attested cargo-vet binary for CARGO_VET_VERSION and put it on PATH."""

import hashlib
import os
import platform
import sys
import time
import urllib.request
from pathlib import Path

# Each binary is built from crates.io with Light Squares Attestable Builds and
# attached to the release cargo-vet-v<version> of this repository (see README).
# Add an entry here when a new version is released.
SHA256 = {
    "0.10.2": "8dda5da79b83f42d971dc5802ccfa998d4cdd6d7c7b2de44b26f3c9eaacb9372",
    "0.10.0": "fa006d3e8561c5a8e45933da45c1f6e73ab9771be98baf15bc8996ef9424c76e",
}

RELEASES_URL = "https://github.com/lightsquares/cargo-vet-action/releases/download"
ASSET_NAME = "cargo-vet-x86_64-unknown-linux-musl"


def fail(message):
    sys.exit(f"::error::{message}")


def download(url, retries=3):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except OSError as error:
            last_error = error
            time.sleep(2**attempt)
    fail(f"failed to download {url}: {last_error}")


system, machine = platform.system(), platform.machine()
if (system, machine) != ("Linux", "x86_64"):
    fail(f"cargo-vet-action supports Linux x86_64 runners only (got {system}-{machine})")

version = os.environ["CARGO_VET_VERSION"]
if version not in SHA256:
    fail(f"unsupported cargo-vet-version '{version}' (supported: {', '.join(SHA256)})")
expected_sha256 = SHA256[version]

url = f"{RELEASES_URL}/cargo-vet-v{version}/{ASSET_NAME}"
binary = download(url)
actual_sha256 = hashlib.sha256(binary).hexdigest()
if actual_sha256 != expected_sha256:
    fail(f"sha256 mismatch for {url}: expected {expected_sha256}, got {actual_sha256}")

bin_dir = Path(os.environ["RUNNER_TEMP"], "cargo-vet-bin")
bin_dir.mkdir(exist_ok=True)
bin_path = bin_dir / "cargo-vet"
bin_path.write_bytes(binary)
bin_path.chmod(0o755)

with open(os.environ["GITHUB_PATH"], "a") as github_path:
    github_path.write(f"{bin_dir}\n")

print(f"Installed cargo-vet {version} (sha256 {expected_sha256})")
