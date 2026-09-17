# Candidate B: Chainguard / Wolfi Minimal Python Runtime
# Wolfi is engineered specifically for minimal attack surface and zero known CVEs
FROM cgr.dev/chainguard/python:latest-dev AS setup
USER root
RUN mkdir -p /workspace /tmp && \
    chmod 1777 /tmp && \
    chmod 0777 /workspace

FROM cgr.dev/chainguard/python:latest
COPY --from=setup /workspace /workspace
USER 10001:10001
WORKDIR /workspace
CMD ["python", "-u"]
