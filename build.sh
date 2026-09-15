#!/bin/sh
# Builds cargo-vet from crates.io inside the builder container (cwd = /workspace).
# Usage: ./build.sh <cargo-vet version>   (set via build_cmd in lightsquares.toml)
set -eu
VERSION="${1:?usage: ./build.sh <cargo-vet version>}"
OUT="dist/cargo-vet-${VERSION}-x86_64-unknown-linux-musl"

cargo install --locked --version "$VERSION" --root /workspace/dist/install cargo-vet
mkdir -p dist
mv dist/install/bin/cargo-vet "$OUT"
rm -rf dist/install
"$OUT" --version
sha256sum "$OUT"
