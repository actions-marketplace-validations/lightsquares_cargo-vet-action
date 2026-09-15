# Maintainer notes

## How the binaries are built

Every `cargo-vet` binary is compiled from crates.io with
`cargo install --locked` in a Light Squares Attestable Build using the files
in this repository:

- `lightsquares.toml` – build definition read by the platform
- `docker/Dockerfile` – toolchain image, pinned by digest
- `build.sh` – the build itself, with the version to build set at the top

The platform hashes the resulting binary, signs a provenance statement, and
logs it publicly. Each binary is attached to the GitHub Release
`cargo-vet-v<version>` of this repository, and `scripts/install_cargo_vet.py`
refuses to run it unless its sha256 matches the one recorded for that version.

`main` builds the newest supported version. Every other version lives on a
branch `build/cargo-vet-<version>` that carries its own `lightsquares.toml`
(with `head` pointing at the branch) and its own `build.sh` (with that
version), so each binary has its own source ref and its own attestation.
The artifact path is the same on every branch on purpose: the run form at
app.lightsquares.dev prefills its fields from the `lightsquares.toml` on the
default branch and does not re-read it when you pick another branch, so a
branch-specific artifact path would silently be skipped.

| Version | Release | Built from | Notes |
|---|---|---|---|
| `0.10.2` | `cargo-vet-v0.10.2` | `main` | Current upstream release. |
| `0.10.0` | `cargo-vet-v0.10.0` | branch `build/cargo-vet-0.10.0` | Skips audits that use `trusted-publisher` with a warning (80 of them in the `bytecodealliance` registry at the time of writing). |

Both are `0.10` store versions, so switching between them needs no changes
to a committed `supply-chain/`.

Reproduce a build locally with podman (or docker):

```bash
podman build -t ab-builder -f Dockerfile docker/
podman run --rm -v "$PWD:/workspace" -w /workspace ab-builder ./build.sh
dist/cargo-vet-x86_64-unknown-linux-musl --version
```

## Adding or updating a cargo-vet version

1. For the newest version, set `VERSION` in `build.sh` on `main`. For any
   other version, create a branch from `main` that changes only `VERSION`
   and `head`:

   ```bash
   git switch -c build/cargo-vet-X.Y.Z main
   sed -i 's/^VERSION=.*/VERSION=X.Y.Z/' build.sh
   sed -i 's/^head = "main"/head = "build\/cargo-vet-X.Y.Z"/' lightsquares.toml
   git commit -am "Build cargo-vet X.Y.Z"
   git push -u origin build/cargo-vet-X.Y.Z
   git switch main
   ```

2. Test the build locally as above, then run the Attestable Build at
   <https://app.lightsquares.dev/builds/run> with public visibility. The
   form is prefilled from `main`; set the Branch field to the build branch
   and leave everything else as is.
3. Download the attested artifact and verify it at
   <https://app.lightsquares.dev/verify>.
4. Create the release and attach the artifact:

   ```bash
   gh release create cargo-vet-vX.Y.Z dist/cargo-vet-x86_64-unknown-linux-musl
   ```

5. On `main`, add the version and its sha256 to the `SHA256` table in
   `scripts/install_cargo_vet.py`, list it in the README input table and in
   the input description in `action.yml`, and move the `v1` tag once CI is
   green.

## Tests

`.github/workflows/ci.yml` runs the action against the fixtures in `tests/`
in a single job: a committed store whose only dependency is covered by an
imported registry, checked with `--locked` using both cargo-vet versions,
a dependency-free project bootstrapped from the default registries, and
the same `anyhow` dependency with no registries, which must fail. It
needs the release assets referenced in `scripts/install_cargo_vet.py` to be
downloadable.
