# AARKAAI Hardened Sandbox Dockerfile
# Based on Ubuntu 24.04 LTS Minimal Python (Empirical Selection Winner: Candidate D)
# Pinned official base digest for reproducible, verifiable builds
FROM ubuntu:24.04@sha256:69cecf4bbf72d2d44a9eef1b71fb98c7fb973d78af11399deccef19beb008ad9 AS base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-minimal && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/man /usr/share/doc

# Create dedicated non-root user and group (UID/GID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M -d /workspace appuser

# Symlink python -> python3 for standard command entrypoint
RUN ln -s /usr/bin/python3 /usr/bin/python || true

# Prepare workspace directory with strict non-root ownership
RUN mkdir -p /workspace /tmp && \
    chown -R 10001:10001 /workspace /tmp && \
    chmod 0700 /workspace /tmp

# Drop to unprivileged user
USER 10001:10001
WORKDIR /workspace

# Default command: interactive unbuffered Python
CMD ["python", "-u"]

