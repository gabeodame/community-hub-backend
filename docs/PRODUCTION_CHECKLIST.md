# Production Checklist

## Configuration
- Set `DJANGO_DEBUG=0`
- Set `DJANGO_SECRET_KEY` to a strong value
- Set `DJANGO_ALLOWED_HOSTS`
- Set `DJANGO_CORS_ALLOWED_ORIGINS`
- Set `DJANGO_CSRF_TRUSTED_ORIGINS`
- Set `JWT_COOKIE_SECURE=1`
- Set `JWT_COOKIE_SAMESITE` and `CSRF_COOKIE_SAMESITE` for your frontend topology

## Database
- Use Postgres (`DJANGO_DB_ENGINE=django.db.backends.postgresql`)
- Set `DJANGO_DB_NAME`, `DJANGO_DB_USER`, `DJANGO_DB_PASSWORD`, `DJANGO_DB_HOST`, `DJANGO_DB_PORT`
- Run `python manage.py migrate`
- Set backups and verify restores

## Cache/Throttling
- Set `REDIS_URL`
- Confirm DRF throttling works across multiple instances

## Storage
- Configure static and media storage
- Run `python manage.py collectstatic` if serving locally
- Use S3/GCS in production if needed

## Security
- Ensure HTTPS is enabled and `SECURE_SSL_REDIRECT=1`
- Confirm HSTS headers are active
- Configure edge rate limits for auth and write-heavy routes
- Validate CSRF flow from your frontend

## Observability
- Set `DJANGO_LOG_LEVEL=INFO`
- Add error tracking (Sentry) and alerting
- Monitor `/api/v1/health/` and `/api/v1/ready/`

## Testing/Load
- Run `python -m pytest`
- Run a basic load test: `python scripts/load_test.py`
- Use `SLEEP_MS` to pace requests and avoid tripping throttles during baseline tests
- Validate credentials with `python scripts/verify_login.py`
