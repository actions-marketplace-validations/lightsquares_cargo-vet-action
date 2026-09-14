# Toolchain only: the repository is mounted at /workspace when the build runs,
# and the build context is this directory, so nothing is copied in.
FROM rust:1.98-alpine@sha256:1716b3aa042d735f4566d14dc54e8037de9d69556e2d5dd58131d93a613d173d
RUN apk add --no-cache musl-dev
WORKDIR /workspace
CMD ["./build.sh"]
