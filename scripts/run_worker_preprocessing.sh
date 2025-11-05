#!/bin/bash
# Run Celery worker for preprocessing tasks

celery -A app.workers.celery_app.celery_app worker \
    --loglevel=info \
    --queues=preprocessing \
    --concurrency=2 \
    --hostname=preprocessing@%h

