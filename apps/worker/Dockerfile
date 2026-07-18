# Build context is the repo root (see docker-compose.yml) so later phases can
# install apps/api alongside for shared DB models.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY apps/worker /srv/worker-src
RUN pip install /srv/worker-src

CMD ["celery", "-A", "worker.celery_app", "worker", "--beat", "--loglevel=info"]
