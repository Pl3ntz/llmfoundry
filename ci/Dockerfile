# Imagem da CI local do llmfoundry.
# python 3.12 + bun (compila plugins TS no eval-runner) + deps determinísticas.
# Build uma vez na VPS; cada run e um `docker run --rm` barato.

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip ca-certificates \
    && curl -fsSL https://bun.sh/install | bash \
    && apt-get purge -y --auto-remove curl unzip \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.bun/bin:${PATH}"

RUN pip install --no-cache-dir numpy pyyaml

WORKDIR /workspace
CMD ["/workspace/scripts/ci-local.sh"]
