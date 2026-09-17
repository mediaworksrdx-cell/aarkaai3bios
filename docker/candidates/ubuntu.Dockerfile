# Candidate D: Ubuntu 24.04 LTS Minimal Python
FROM ubuntu:24.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-minimal && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M -d /workspace appuser

RUN ln -s /usr/bin/python3 /usr/bin/python || true

RUN mkdir -p /workspace /tmp && \
    chown -R 10001:10001 /workspace /tmp && \
    chmod 0700 /workspace /tmp

USER 10001:10001
WORKDIR /workspace
CMD ["python", "-u"]
