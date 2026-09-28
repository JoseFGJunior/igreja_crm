#!/bin/sh
set -eu

if [ "${ENVIRONMENT:-development}" = "production" ]; then
    if [ "${ALLOW_PRODUCTION_MIGRATIONS:-}" = "true" ]; then
        python manage.py migrate --noinput
    fi
else
    python manage.py migrate --noinput
fi

python manage.py collectstatic --noinput

exec "$@"
