#!/bin/bash
# Run Celery worker for maintenance tasks

celery -A app.workers.celery_app.celery_app worker \
    --loglevel=info \
    --queues=maintenance \
    --concurrency=1 \
    --hostname=maintenance@%h

