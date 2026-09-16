# AARKAAI Hardened Sandbox Dockerfile
# Pinned official base digest for reproducible, verifiable builds
FROM python:3.11.8-slim@sha256:72c448d6174a72d1767073238e833446820524419cb7d48354db1a7191136b80 AS base

# Create dedicated non-root user and group (UID/GID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M -d /workspace appuser

# Remove package managers and clean system caches to minimize attack surface
RUN rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/cache/debconf/* /usr/share/man /usr/share/doc

# Prepare workspace directory with strict non-root ownership
RUN mkdir -p /workspace /tmp && \
    chown -R 10001:10001 /workspace /tmp && \
    chmod 0700 /workspace /tmp

# Drop to unprivileged user
USER 10001:10001
WORKDIR /workspace

# Default command: interactive unbuffered Python
CMD ["python", "-u"]
