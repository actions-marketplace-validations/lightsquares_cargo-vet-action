# cargo-vet-action

[![Light Squares Attestable Builds](https://app.lightsquares.dev/api/badge/lightsquares/cargo-vet-action.svg)](https://app.lightsquares.dev/builds/dashboard?show=lightsquares/cargo-vet-action)

A small, security-focused GitHub Action that installs
[cargo-vet](https://mozilla.github.io/cargo-vet/) and runs `cargo vet` on a
Rust project.

- The `cargo-vet` binary is built from crates.io inside a Light Squares
  [Attestable Build](https://lightsquares.dev/products/attestable-builds) and
  verified against a sha256 hardcoded in `action.yml`.
- Projects that already have a `supply-chain/` directory are checked with
  `cargo vet --locked`.
- Projects without one get a temporary store that imports well-known audit
  registries, so `cargo vet` reports exactly which dependencies nobody has
  vetted yet.

## Usage

Pin the action by commit SHA, not by tag:

```yaml
jobs:
  vet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: lightsquares/cargo-vet-action@<commit-sha> # v1
        with:
          working-directory: crates/my-service   # optional, default "."
```

### Inputs

| Input | Default | Description |
|---|---|---|
| `working-directory` | `.` | Directory containing the project's `Cargo.toml`. |
| `registries` | `google,mozilla,bytecodealliance,lightsquares-canary` | Registries to import when the project has no `supply-chain/` directory. Comma-separated; each entry is a known name or `name=https://…/audits.toml`. Ignored when `supply-chain/` exists. |
| `cargo-vet-version` | `0.10.2` | Which cargo-vet binary to run. See [supported versions](#supported-cargo-vet-versions). |
| `unsafe-only-report-warnings` | `false` | When `true`, a failing `cargo vet` produces a workflow warning instead of failing the job. Unvetted code then reaches CI unnoticed unless someone reads the warnings, hence the name. |

### Known registries

| Name | Audits file |
|---|---|
| `google` | https://raw.githubusercontent.com/google/supply-chain/main/audits.toml |
| `mozilla` | https://raw.githubusercontent.com/mozilla/supply-chain/main/audits.toml |
| `bytecodealliance` | https://raw.githubusercontent.com/bytecodealliance/wasmtime/main/supply-chain/audits.toml |
| `lightsquares-canary` | https://app.lightsquares.dev/api/canary/audit-toml ([Dependency Canary](https://lightsquares.dev/products/dependency-canary)) |

### Behaviour

**With `supply-chain/`:** runs `cargo vet --locked`. Imports come from the
committed `imports.lock`, so the result is reproducible and needs no network
access beyond the crates.io index. Update the store locally with `cargo vet`
and commit the changes.

**Without `supply-chain/`:** writes a minimal store into the working
directory with `[imports.<name>]` entries for the chosen registries and runs
`cargo vet`, which fetches those audits and checks every dependency against
them. Anything not covered fails the job with cargo-vet's usual report. The
generated store is not committed; run `cargo vet init` locally when you are
ready to adopt cargo-vet properly.

### Requirements

- Linux x86_64 runner (the attested binary is built for
  `x86_64-unknown-linux-musl` and is statically linked).
- `cargo` on `PATH`. GitHub's hosted Ubuntu runners ship a stable Rust
  toolchain via rustup; a project `rust-toolchain.toml` is honoured
  automatically.

### Supported cargo-vet versions

| Version | Release asset | Built from | Notes |
|---|---|---|---|
| `0.10.2` (default) | `cargo-vet-v0.10.2` | `main` | Current upstream release. |
| `0.10.0` | `cargo-vet-v0.10.0` | branch `build/cargo-vet-0.10.0` | Skips audits that use `trusted-publisher` with a warning (80 of them in the `bytecodealliance` registry at the time of writing), so it covers fewer crates than 0.10.2. |

Both are `0.10` store versions, so switching between them needs no changes
to a committed `supply-chain/`.

## How the binaries are built

Every `cargo-vet` binary is compiled from crates.io with
`cargo install --locked` inside a hardware-attested enclave (AMD SEV-SNP)
using the files in this repository:

- `lightsquares.toml` – build definition read by the platform
- `docker/Dockerfile` – toolchain image, pinned by digest
- `build.sh` – the build itself, with the version to build set at the top

The platform hashes the resulting binary, signs a SLSA provenance statement
with the CPU's attestation report, and logs it publicly. Each binary is
attached to the GitHub Release `cargo-vet-v<version>` of this repository and
`action.yml` refuses to run it unless its sha256 matches the one recorded for
that version. Anyone can drop a release asset on
<https://app.lightsquares.dev/verify> to confirm it came from this source.

`main` builds the newest supported version. Every other version lives on a
branch `build/cargo-vet-<version>` that carries its own `lightsquares.toml`
(with `head` pointing at the branch) and its own `build.sh` (with that
version), so each binary has its own source ref and its own attestation. The
attestation records the exact commit that was built.

Reproduce a build locally with podman (or docker):

```bash
podman build -t ab-builder -f Dockerfile docker/
podman run --rm -v "$PWD:/workspace" -w /workspace ab-builder ./build.sh
dist/cargo-vet-0.10.2-x86_64-unknown-linux-musl --version
```

### Adding or updating a cargo-vet version (maintainers)

1. For the newest version, set `VERSION` in `build.sh` and the artifact
   name in `lightsquares.toml` on `main`. For any other version, create a
   branch from `main` that changes only those two files:

   ```bash
   git switch -c build/cargo-vet-X.Y.Z main
   sed -i 's/^VERSION=.*/VERSION=X.Y.Z/' build.sh
   sed -i -e 's/^head = "main"/head = "build\/cargo-vet-X.Y.Z"/' \
          -e 's/cargo-vet-0\.10\.2-/cargo-vet-X.Y.Z-/' lightsquares.toml
   git commit -am "Build cargo-vet X.Y.Z"
   git push -u origin build/cargo-vet-X.Y.Z
   git switch main
   ```

2. Test the build locally as above, then run the Attestable Build at
   <https://app.lightsquares.dev/builds/run> for that branch with public
   visibility.
3. Download the attested artifact and verify it at
   <https://app.lightsquares.dev/verify>.
4. Create the release and attach the artifact:

   ```bash
   gh release create cargo-vet-vX.Y.Z dist/cargo-vet-X.Y.Z-x86_64-unknown-linux-musl
   ```

5. On `main`, add the version and its sha256 to the `case` table in
   `action.yml`, list it in this README and in the input description, and
   move the `v1` tag once CI is green.

## License

MIT
