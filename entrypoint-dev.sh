#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# Check if we're running a Celery command (with proper argument checking)
if [ $# -gt 0 ] && [ "$1" = "celery" ]; then
    echo "🔄 Starting Celery: $@"
    exec "$@"
elif [ $# -gt 0 ] && [ "$1" = "flower" ]; then
    echo "🌸 Starting Flower: $@"
    exec "$@"
else
    # Default Django setup for web service
    echo "💡 Running migrations..."
    python manage.py migrate
    
    echo "🎯 Collecting static files..."
    python manage.py collectstatic --noinput
    
    echo "🚀 Starting development server with live reload..."
    exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
fi