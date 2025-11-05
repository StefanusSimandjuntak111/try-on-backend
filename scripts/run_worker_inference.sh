#!/bin/bash
# Run Celery worker for inference tasks (GPU recommended)

celery -A app.workers.celery_app.celery_app worker \
    --loglevel=info \
    --queues=inference \
    --concurrency=1 \
    --hostname=inference@%h

