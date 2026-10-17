ARG BASE_IMAGE=registry.linuxone.cloud.marist.edu/l1cc/jupyterlab-image-s390x@sha256:d2da8a7b0c88c3b468e29014b2ada9ef8274f98c976ec456904c5e2bae5aa54c
FROM ${BASE_IMAGE}
LABEL org.opencontainers.image.title="RASCALS_IBM Z Datathon 2026 Project - ContinuityGuard" org.opencontainers.image.source="https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON"
USER 1000
WORKDIR /opt/continuityguard
COPY --chown=1000:1000 requirements.txt ./
RUN /opt/venv/bin/python3 -m pip install --no-cache-dir -r requirements.txt
COPY --chown=1000:1000 continuityguard ./continuityguard
COPY --chown=1000:1000 artifacts ./artifacts
ENV CG_PROJECT_ROOT=/opt/continuityguard CG_STATE_DIR=/home/ibm-user/cg-state CG_TOKEN_FILE=/home/ibm-user/cg-state/.access-token CG_PORT=8080 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD /opt/venv/bin/python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=4)" || exit 1
ENTRYPOINT ["/opt/venv/bin/python3", "-m", "continuityguard.web"]
