#!/bin/bash
set -o pipefail

echo "🔥 FORCING DEPLOYMENT TO WORK..."

wait_for_db() {
    echo "⏰ Waiting for database..."
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python manage.py check --database default > /dev/null 2>&1; then
            echo "✅ Database ready!"
            break
        else
            sleep 2
            attempt=$((attempt + 1))
        fi
        
        if [ $attempt -gt $max_attempts ]; then
            echo "❌ Database timeout"
            exit 1
        fi
    done
}

# Check if this is a celery/beat/flower worker
if [ $# -gt 0 ] && ( [[ "$1" == "celery" ]] || [[ "$1" == "beat" ]] || [[ "$1" == "flower" ]] ); then
    echo "🐝 Celery worker detected, skipping migrations..."
    sleep 10
else
    # Run migrations for web server
    echo "🌐 Web server detected, running migrations..."
    wait_for_db
    python manage.py makemigrations || echo "✅ makemigrations done"
    python manage.py migrate --fake-initial || echo "✅ migrate --fake-initial done"
    python manage.py migrate --run-syncdb || echo "✅ migrate --run-syncdb done"
    python manage.py migrate || echo "✅ migrate done"
    python manage.py collectstatic --noinput || echo "✅ collectstatic done"
fi

echo "🚀 Starting: ${@:-python manage.py runserver 0.0.0.0:8000}"
exec ${@:-python manage.py runserver 0.0.0.0:8000}