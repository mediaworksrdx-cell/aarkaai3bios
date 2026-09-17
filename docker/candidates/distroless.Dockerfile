# Candidate C: Distroless Python 3 (Debian 12)
# Shell-less, package-manager-less, minimal glibc Python runtime
FROM debian:bookworm-slim AS setup
RUN mkdir -p /workspace /tmp && \
    chmod 1777 /tmp && \
    chmod 0777 /workspace

FROM gcr.io/distroless/python3-debian12:latest
COPY --from=setup /workspace /workspace
USER 10001:10001
WORKDIR /workspace
CMD ["/usr/bin/python3", "-u"]
