---
name: lightsquares-cargo-vet-action
description: Run cargo-vet in GitHub Actions with lightsquares/cargo-vet-action, and set up cargo-vet in a Rust project that does not use it yet. Covers the workflow snippet, the inputs (working-directory, registries, cargo-vet-version, unsafe-only-report-warnings), what happens with and without a committed supply-chain/ directory, and the path from "no cargo-vet" to a committed store. Use when someone wants dependency audits enforced in CI for a Rust repo, asks how to add cargo vet or cargo-vet-action, or sees the action fail with unvetted dependencies. Triggers — cargo vet, cargo-vet, cargo-vet-action, supply-chain audit, unvetted dependencies, audit registries.
license: MIT
compatibility: Linux x86_64 GitHub runners with cargo on PATH (hosted Ubuntu runners qualify). Adding cargo-vet locally needs `cargo install cargo-vet`.
metadata:
  version: "0.1.0"
  author: "Light Squares"
---

# cargo-vet-action

`lightsquares/cargo-vet-action` installs a cargo-vet binary built with
Light Squares Attestable Builds (sha256-checked in the action) and runs
`cargo vet`. Repository and README:
<https://github.com/lightsquares/cargo-vet-action>.

## Add the action to a workflow

Pin by commit SHA. Get the current SHA of `main` with
`git ls-remote https://github.com/lightsquares/cargo-vet-action main | cut -f1`.

```yaml
jobs:
  vet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: lightsquares/cargo-vet-action@<commit-sha> # v1
        with:
          working-directory: crates/my-service   # only if Cargo.toml is not at the root
```

Inputs (all optional):

| Input | Default | Use |
|---|---|---|
| `working-directory` | `.` | Directory with the project's `Cargo.toml`. |
| `registries` | `google,mozilla,bytecodealliance,lightsquares-canary` | Registries to import when there is no `supply-chain/`. Known names or `name=https://…/audits.toml`. |
| `cargo-vet-version` | `0.10.2` | `0.10.2` or `0.10.0`. |
| `unsafe-only-report-warnings` | `false` | `true` turns a failed vet into a workflow warning. Only for a transition period. |

## What the action does

- **`supply-chain/` exists:** runs `cargo vet --locked` against the committed
  `imports.lock`. This is the intended steady state; the result is
  reproducible and the job fails on any unvetted dependency.
- **No `supply-chain/`:** writes a temporary store importing the registries
  above and runs `cargo vet`. The job fails with cargo-vet's report of what
  is not covered. Nothing is committed. This is a way to see the gap before
  adopting cargo-vet, not a substitute for a committed store.

## Add cargo-vet to a project

Do this once, locally, then commit `supply-chain/`. The action switches to
the locked mode automatically.

```bash
cargo install --locked cargo-vet
cargo vet init                     # creates supply-chain/ with exemptions for every current dependency
cargo vet import google
cargo vet import mozilla
cargo vet import bytecode-alliance
cargo vet import lightsquares-canary https://app.lightsquares.dev/api/canary/audit-toml
cargo vet                          # fetches imports, prunes exemptions now covered by them
cargo vet suggest                  # what is still exempted and would need a real audit
git add supply-chain && git commit -m "Add cargo-vet"
```

Notes:

- `cargo vet init` makes the check pass immediately by exempting everything
  present; the imports then shrink that list. Work down the rest with
  `cargo vet certify` over time, and keep new dependencies from being
  exempted: with the store committed, CI fails until they are audited or
  imported.
- After changing dependencies, run `cargo vet` locally and commit the
  updated `imports.lock`; CI runs with `--locked` and will not fetch.
- The Dependency Canary registry is described in the
  `lightsquares-dependency-canary-user` skill.

## When the action fails

The log lists each unvetted crate and the cheapest fix: an import that would
cover it, or `cargo vet certify` for a manual audit. Act on that locally and
commit; do not reach for `unsafe-only-report-warnings` except to stage a
rollout.
