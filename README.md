# cargo-vet-action

[![CI](https://github.com/lightsquares/cargo-vet-action/actions/workflows/ci.yml/badge.svg)](https://github.com/lightsquares/cargo-vet-action/actions/workflows/ci.yml)
[![Light Squares Attestable Builds](https://app.lightsquares.dev/api/badge/lightsquares/cargo-vet-action.svg)](https://app.lightsquares.dev/builds/dashboard?show=lightsquares/cargo-vet-action)

A small, security-focused GitHub Action that installs
[cargo-vet](https://mozilla.github.io/cargo-vet/) and runs `cargo vet` on a
Rust project. Projects with a committed `supply-chain/` directory are checked
with `cargo vet --locked`. Projects without one get a temporary store that
imports well-known audit registries, so the run reports exactly which
dependencies nobody has vetted yet.

## Usage

Pin the action by commit SHA, not by tag:

```yaml
jobs:
  vet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: lightsquares/cargo-vet-action@<commit-sha> # v1
```

To get the current commit SHA of `main`:

```bash
git ls-remote https://github.com/lightsquares/cargo-vet-action main | cut -f1
```

Runs on Linux x86_64 runners with `cargo` on `PATH`, which GitHub's hosted
Ubuntu runners provide.

### Inputs

| Input | Description | Default | Example |
|---|---|---|---|
| `working-directory` | Directory containing the project's `Cargo.toml`. | `.` | `crates/my-service` |
| `registries` | Registries to import when the project has no `supply-chain/` directory. Comma-separated known names or `name=url`. Ignored when `supply-chain/` exists. | `google, mozilla, bytecodealliance, lightsquares-canary` | `mozilla,acme=https://acme.example/audits.toml` |
| `cargo-vet-version` | Which cargo-vet binary to run: `0.10.2` or `0.10.0`. | `0.10.2` | `0.10.0` |
| `unsafe-only-report-warnings` | Turn a failing `cargo vet` into a workflow warning instead of a failed job. Unvetted code then reaches CI unnoticed unless someone reads the warnings, hence the name. | `false` | `true` |

### Known registries

| Name | Audits file |
|---|---|
| `google` | https://raw.githubusercontent.com/google/supply-chain/main/audits.toml |
| `mozilla` | https://raw.githubusercontent.com/mozilla/supply-chain/main/audits.toml |
| `bytecodealliance` | https://raw.githubusercontent.com/bytecodealliance/wasmtime/main/supply-chain/audits.toml |
| `lightsquares-canary` | https://app.lightsquares.dev/api/canary/audit-toml ([Dependency Canary](https://lightsquares.dev/products/dependency-canary)) |

## Verifiable binaries

The `cargo-vet` binaries this action runs are compiled from crates.io with
[Light Squares Attestable Builds](https://lightsquares.dev/products/attestable-builds),
which produce a signed, publicly logged proof that each binary was built from
the source in this repository. The binaries are attached to this repository's
releases, and the action refuses to run one unless its sha256 matches the
value recorded in `scripts/install_cargo_vet.py`. Anyone can check a release
asset at
<https://app.lightsquares.dev/verify>. How the builds are set up is
described in [MAINTAINER.md](MAINTAINER.md).

## License

MIT
