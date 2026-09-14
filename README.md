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

## How the binary is built

`cargo-vet` is compiled from crates.io with `cargo install --locked` inside a
hardware-attested enclave (AMD SEV-SNP) using the files in this repository:

- `lightsquares.toml` – build definition read by the platform
- `docker/Dockerfile` – toolchain image, pinned by digest
- `build.sh` – the build itself

The platform hashes the resulting binary, signs a SLSA provenance statement
with the CPU's attestation report, and logs it publicly. The binary is
attached to a GitHub Release of this repository and `action.yml` refuses to
run it unless its sha256 matches. Anyone can drop the release asset on
<https://app.lightsquares.dev/verify> to confirm it came from this source.

Reproduce the build locally with podman (or docker):

```bash
podman build -t ab-builder -f Dockerfile docker/
podman run --rm -v "$PWD:/workspace" -w /workspace ab-builder ./build.sh
dist/cargo-vet-x86_64-unknown-linux-musl --version
```

### Releasing a new cargo-vet version (maintainers)

1. Bump `CARGO_VET_VERSION` in `build.sh` and in `action.yml`, and update the
   `CARGO_VET_URL` release tag. Test the build locally as above.
2. Commit, push, and run the Attestable Build for this repository at
   <https://app.lightsquares.dev/builds/run> with public visibility.
3. Download the attested artifact from the build page and verify it at
   <https://app.lightsquares.dev/verify>.
4. Create the release and attach the artifact:

   ```bash
   gh release create cargo-vet-vX.Y.Z dist/cargo-vet-x86_64-unknown-linux-musl
   ```

5. Put the artifact's sha256 into `CARGO_VET_SHA256` in `action.yml`, commit,
   and move the `v1` tag once CI is green.

## License

MIT
