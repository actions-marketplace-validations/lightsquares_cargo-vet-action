#!/usr/bin/env python3
"""Run `cargo vet` in the current directory.

A committed supply-chain/ directory is checked with --locked. Otherwise a
temporary store importing the registries listed in REGISTRIES is written first.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

KNOWN_REGISTRIES = {
    "google": "https://raw.githubusercontent.com/google/supply-chain/main/audits.toml",
    "mozilla": "https://raw.githubusercontent.com/mozilla/supply-chain/main/audits.toml",
    "bytecodealliance": "https://raw.githubusercontent.com/bytecodealliance/wasmtime/main/supply-chain/audits.toml",
    "lightsquares-canary": "https://app.lightsquares.dev/api/canary/audit-toml",
}


def fail(message):
    sys.exit(f"::error::{message}")


def parse_registries(spec):
    """Turn 'google, acme=https://acme.example/audits.toml' into [(name, url), ...]."""
    registries = []
    for entry in spec.split(","):
        entry = entry.strip()
        if not entry:
            continue

        name, _, url = entry.partition("=")
        if not url:
            url = KNOWN_REGISTRIES.get(name)
        if url is None:
            fail(f"unknown registry '{name}' (use name=https://... for custom registries)")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            fail(f"invalid registry name '{name}'")
        if not re.fullmatch(r'https://[^\s"]+', url):
            fail(f"registry '{name}' must have an https:// URL")

        registries.append((name, url))
    return registries


def bootstrap_store(store_dir, registries):
    config = '[cargo-vet]\nversion = "0.10"\n'
    for name, url in registries:
        config += f'\n[imports.{name}]\nurl = "{url}"\n'

    store_dir.mkdir()
    (store_dir / "config.toml").write_text(config)
    (store_dir / "audits.toml").write_text("[audits]\n")
    (store_dir / "imports.lock").touch()

    names = " ".join(name for name, _ in registries) or "(none)"
    print(
        f"::notice::No supply-chain/ directory found; bootstrapped a temporary store "
        f"importing: {names}. Run 'cargo vet init' locally to commit a real store.",
        flush=True,
    )


store_dir = Path("supply-chain")
if store_dir.is_dir():
    vet_args = ["--locked"]
else:
    registries = parse_registries(os.environ.get("REGISTRIES", ""))
    bootstrap_store(store_dir, registries)
    vet_args = []

result = subprocess.run(["cargo", "vet", *vet_args])
if result.returncode == 0:
    sys.exit(0)

warn_only = os.environ.get("WARN_ONLY") == "true"
if not warn_only:
    sys.exit(1)
print("::warning::cargo vet failed (see log); continuing because unsafe-only-report-warnings is enabled")
