#!/bin/sh
# Builds cargo-vet from crates.io inside the builder container (cwd = /workspace).
# Keep CARGO_VET_VERSION in sync with action.yml.
set -eu
CARGO_VET_VERSION=0.10.2
OUT=dist/cargo-vet-x86_64-unknown-linux-musl

cargo install --locked --version "$CARGO_VET_VERSION" --root /workspace/dist/install cargo-vet
mkdir -p dist
mv dist/install/bin/cargo-vet "$OUT"
rm -rf dist/install
"$OUT" --version
sha256sum "$OUT"
