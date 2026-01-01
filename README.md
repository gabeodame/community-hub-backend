# Community Platform (Django + DRF) Scaffold

This scaffold is ready to run and test the health endpoint:

- `GET /api/v1/health/` -> `{ "status": "ok" }`

## Quickstart

```powershell
cd community_platform_scaffold

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

copy .env.example .env
# Update .env with a strong DJANGO_SECRET_KEY value

python manage.py migrate
python manage.py runserver
```

Test:
- http://127.0.0.1:8000/api/v1/health/

## Tooling

Run tests:

```powershell
python -m pytest
```

Lint:

```powershell
ruff check .
black --check .
isort --check-only .
```

E2E (when added):

```powershell
python -m pytest -m e2e
```

## Notes
- Uses a custom user model (`users.User`) from day one.
- `.env` is required for local runs and must not be committed.
- JWT endpoints are wired but optional for health check:
  - `POST /api/v1/auth/token/`
  - `POST /api/v1/auth/token/refresh/`
  - `POST /api/v1/auth/logout/`
  - `GET /api/v1/auth/csrf/`
  - `POST /api/v1/auth/register/`
  - `GET/PATCH /api/v1/users/me/`
  - `GET/PATCH /api/v1/profiles/me/`
  - `POST/DELETE /api/v1/users/{id}/follow/`
  - `POST/DELETE /api/v1/users/{id}/block/`
  - `POST /api/v1/groups/`
  - `POST /api/v1/groups/{id}/join/`
  - `GET /api/v1/groups/{id}/members/`
  - `POST /api/v1/groups/{id}/members/{user_id}/approve/`
  - Groups require auth; join policy controls `join/` behavior (open -> active, request -> pending, invite -> 403).
  - Private group members list requires active membership; owners/moderators can approve members.
  - `GET /api/v1/posts/`
  - `POST /api/v1/posts/`
  - `GET /api/v1/posts/{id}/`
  - `DELETE /api/v1/posts/{id}/`
  - `GET /api/v1/users/{id}/posts/`
  - `GET /api/v1/groups/{id}/posts/`
  - `GET /api/v1/posts/{id}/comments/`
  - `POST /api/v1/posts/{id}/comments/`
  - `GET /api/v1/comments/{id}/`
  - `DELETE /api/v1/comments/{id}/`
  - `POST /api/v1/reports/`
  - Group posts require active membership; private group feeds/comments are restricted to members.
  - Deletes are soft deletes; reports accept `target_type` (post/comment) and `target_id`.
  - Post feeds support `?pagination=cursor` and default page pagination (`page`, `page_size`).
  - `GET /api/v1/notifications/`
  - `PATCH /api/v1/notifications/{id}/read/`
  - `POST /api/v1/notifications/read-all/`
  - Notifications are stored in the DB and returned newest-first.
  - `GET /api/v1/notifications/?unread=1` filters unread only; pagination uses `page` and `page_size`.
  - `GET /api/v1/notifications/?pagination=cursor` enables cursor pagination.
  - `GET /api/v1/notifications/unread-count/` returns `{ "unread": <count> }`.

## Production configuration

Required environment variables:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (set to `0` in production)
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CORS_ALLOWED_ORIGINS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

Cookie + CSRF settings:
- `JWT_COOKIE_SECURE` should be `1` in production (default when `DJANGO_DEBUG=0`)
- `JWT_COOKIE_SAMESITE` defaults to `Lax`
- `CSRF_COOKIE_SAMESITE` defaults to `Lax`

Cross-site frontend (e.g., WordPress on another domain):
- Set `JWT_COOKIE_SAMESITE=None` and `JWT_COOKIE_SECURE=1`
- Add the frontend origin to `DJANGO_CORS_ALLOWED_ORIGINS` and `DJANGO_CSRF_TRUSTED_ORIGINS`

## Infrastructure readiness

Database:
- Use Postgres in production (`DJANGO_DB_ENGINE=django.db.backends.postgresql`)
- Set `DJANGO_DB_NAME`, `DJANGO_DB_USER`, `DJANGO_DB_PASSWORD`, `DJANGO_DB_HOST`, `DJANGO_DB_PORT`
- Run migrations during deploy: `python manage.py migrate`

Cache/throttling:
- Set `REDIS_URL` for shared caching and throttling in production
- Default is local memory cache (not suitable for multi-instance deployments)

Static/media:
- Configure `STATIC_ROOT`/`MEDIA_ROOT` for collection and uploads
- For cloud storage, replace storage backends with S3/GCS equivalents

Backups:
- Schedule Postgres backups and verify restores regularly

## Security hardening

TLS + headers:
- Enable HTTPS and `SECURE_SSL_REDIRECT=1` in production
- Keep `SECURE_HSTS_*` enabled (default when `DJANGO_DEBUG=0`)
- Use `SECURE_REFERRER_POLICY=same-origin`

Edge rate limiting:
- Use a WAF/CDN rate limit for auth endpoints and write-heavy routes
- DRF throttling is in place, but edge limits are recommended

CSRF + cookies:
- For same-site apps, keep `JWT_COOKIE_SAMESITE=Lax`
- For cross-site (WordPress on another domain), use `JWT_COOKIE_SAMESITE=None` and `JWT_COOKIE_SECURE=1`
- Set `CSRF_COOKIE_HTTPONLY=0` so the browser can read and send `X-CSRFToken`

## Observability & ops

Logging:
- Set `DJANGO_LOG_LEVEL=INFO` (or `DEBUG` during troubleshooting)
- Logs are JSON-free by default; add a JSON formatter if your platform expects it

Health + readiness:
- `GET /api/v1/health/` for basic liveness
- `GET /api/v1/ready/` checks database connectivity

Release checklist:
- Run `python manage.py migrate`
- Verify `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS`, `DJANGO_CSRF_TRUSTED_ORIGINS`
- Confirm HTTPS is enabled and `JWT_COOKIE_SECURE=1`

## Production checklist

- See `docs/PRODUCTION_CHECKLIST.md` for a deploy-ready checklist.

## Auth usage

This API uses JWTs stored in HTTP-only cookies for web clients. Access tokens are read from cookies
and CSRF is required for unsafe methods (POST/PATCH/DELETE), including token refresh and logout.

Example:

```powershell
# Get CSRF cookie (use in browser fetch headers as X-CSRFToken)
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/auth/csrf/

# Login sets HTTP-only access/refresh cookies (requires CSRF)
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/auth/token/ `
  -Body (@{ username = "user"; password = "password" } | ConvertTo-Json) `
  -ContentType "application/json"

# Call a protected endpoint (include cookies + CSRF header in browser clients)
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/users/me/
```

### Auth cookbook (browser)

Notes:
- Use `credentials: "include"` so cookies are sent.
- Send `X-CSRFToken` for unsafe methods.
- For local dev, `JWT_COOKIE_SECURE=0` keeps cookies on http; in production, cookies are secure by default.

```js
async function getCsrf() {
  await fetch("http://127.0.0.1:8000/api/v1/auth/csrf/", {
    method: "GET",
    credentials: "include",
  });
}

function readCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

async function login(username, password) {
  await getCsrf();
  const csrfToken = readCookie("csrftoken");
  const res = await fetch("http://127.0.0.1:8000/api/v1/auth/token/", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({ username, password }),
  });
  return res.json();
}

async function refreshToken() {
  await getCsrf();
  const csrfToken = readCookie("csrftoken");
  const res = await fetch("http://127.0.0.1:8000/api/v1/auth/token/refresh/", {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRFToken": csrfToken },
  });
  return res.json();
}

async function getMe() {
  const res = await fetch("http://127.0.0.1:8000/api/v1/users/me/", {
    method: "GET",
    credentials: "include",
  });
  return res.json();
}

async function logout() {
  await getCsrf();
  const csrfToken = readCookie("csrftoken");
  await fetch("http://127.0.0.1:8000/api/v1/auth/logout/", {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRFToken": csrfToken },
  });
}
```

## Load testing

Basic load test (health/posts/notifications):

```bash
BASE_URL=http://127.0.0.1:8000 REQUESTS=200 CONCURRENCY=4 python scripts/load_test.py
```

Throttle-aware pacing:

```bash
BASE_URL=http://127.0.0.1:8000 REQUESTS=120 CONCURRENCY=1 SLEEP_MS=1000 python scripts/load_test.py
```

Authenticated load test:

```bash
BASE_URL=http://127.0.0.1:8000 USERNAME=user PASSWORD=password python scripts/load_test.py
```

Verify login credentials:

```bash
BASE_URL=http://127.0.0.1:8000 USERNAME=user PASSWORD=password python scripts/verify_login.py
```
