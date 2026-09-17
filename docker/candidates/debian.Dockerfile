# Candidate A: Debian 12 Slim Baseline
# Evaluates baseline unpatched Debian OS package CVE exposure and test compatibility
FROM python:3.11.8-slim@sha256:90f8795536170fd08236d2ceb74fe7065dbf74f738d8b84bfbf263656654dc9b

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create dedicated non-root user and group (UID/GID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M -d /workspace appuser

# Remove pip, wheel, setuptools to eliminate language-level CVEs
RUN rm -rf /usr/local/lib/python3.11/site-packages/setuptools* \
           /usr/local/lib/python3.11/site-packages/wheel* \
           /usr/local/lib/python3.11/site-packages/pip* \
           /usr/local/bin/pip* \
           /usr/local/bin/wheel \
           /var/lib/apt/lists/* /var/cache/apt/* /var/cache/debconf/* /usr/share/man /usr/share/doc

# Prepare workspace directory with strict non-root ownership
RUN mkdir -p /workspace /tmp && \
    chown -R 10001:10001 /workspace /tmp && \
    chmod 0700 /workspace /tmp

USER 10001:10001
WORKDIR /workspace
CMD ["python", "-u"]
