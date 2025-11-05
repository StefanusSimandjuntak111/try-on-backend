#!/bin/bash
# Run Celery beat for periodic tasks

celery -A app.workers.celery_app.celery_app beat \
    --loglevel=info

