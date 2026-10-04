# Images locales à partir des binaires des releases GitHub officielles.
# Vérifier SHA-256 ET signature Minisign avant d'exécuter chaque binaire.
FROM debian:bookworm-slim AS binaries
ARG TARGETARCH
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl minisign \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /out
RUN set -eu; \
    version='RELEASE.2025-04-22T22-12-26Z'; \
    asset="minio.linux-${TARGETARCH}.${version}"; \
    base="https://github.com/minio/minio/releases/download/${version}"; \
    curl -fLsS --retry 5 --retry-all-errors --connect-timeout 30 "$base/$asset" -o minio; \
    curl -fLsS --retry 5 --retry-all-errors --connect-timeout 30 "$base/$asset.sha256sum" -o /tmp/minio.sha256sum; \
    printf '%s  minio\n' "$(cut -d ' ' -f 1 /tmp/minio.sha256sum)" | sha256sum -c -; \
    curl -fLsS --retry 5 --retry-all-errors --connect-timeout 30 "$base/$asset.minisig" -o /tmp/minio.minisig; \
    minisign -Vqm minio -x /tmp/minio.minisig -P RWTx5Zr1tiHQLwG9keckT0c45M3AGeHD6IvimQHpyRywVWGbP1aVSGav; \
    chmod 755 minio
RUN set -eu; \
    version='RELEASE.2025-04-16T18-13-26Z'; \
    asset="mc.linux-${TARGETARCH}.${version}"; \
    base="https://github.com/minio/mc/releases/download/${version}"; \
    curl -fLsS --retry 5 --retry-all-errors --connect-timeout 30 "$base/$asset" -o mc; \
    curl -fLsS --retry 5 --retry-all-errors --connect-timeout 30 "$base/$asset.sha256sum" -o /tmp/mc.sha256sum; \
    printf '%s  mc\n' "$(cut -d ' ' -f 1 /tmp/mc.sha256sum)" | sha256sum -c -; \
    curl -fLsS --retry 5 --retry-all-errors --connect-timeout 30 "$base/$asset.minisig" -o /tmp/mc.minisig; \
    minisign -Vqm mc -x /tmp/mc.minisig -P RWTx5Zr1tiHQLwG9keckT0c45M3AGeHD6IvimQHpyRywVWGbP1aVSGav; \
    chmod 755 mc
ADD https://raw.githubusercontent.com/minio/minio/RELEASE.2025-04-22T22-12-26Z/LICENSE /out/minio.LICENSE
ADD https://raw.githubusercontent.com/minio/mc/RELEASE.2025-04-16T18-13-26Z/LICENSE /out/mc.LICENSE

FROM debian:bookworm-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home minio \
    && mkdir -p /data /licenses && chown minio:minio /data
COPY --from=binaries /out/minio /out/mc /usr/local/bin/
COPY --from=binaries /out/minio.LICENSE /out/mc.LICENSE /licenses/
RUN chmod 644 /licenses/*
ENV HOME=/home/minio
USER minio

FROM runtime AS minio
EXPOSE 9000 9001
ENTRYPOINT ["/usr/local/bin/minio"]
CMD ["server", "/data", "--console-address", ":9001"]

FROM runtime AS mc
ENTRYPOINT ["/usr/local/bin/mc"]
