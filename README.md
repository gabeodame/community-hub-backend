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
- JWT endpoints are wired but optional for health check:
  - `POST /api/v1/auth/token/`
  - `POST /api/v1/auth/token/refresh/`
  - `POST /api/v1/auth/register/`
  - `GET/PATCH /api/v1/users/me/`
  - `GET/PATCH /api/v1/profiles/me/`
  - `POST/DELETE /api/v1/users/{id}/follow/`
  - `POST/DELETE /api/v1/users/{id}/block/`

## Auth usage

This API uses JWT Bearer tokens (stateless). Access tokens are stored on the client and sent
via the `Authorization` header. The server does not store access tokens in session state.

Example:

```powershell
# Login to obtain tokens
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/auth/token/ `
  -Body (@{ username = "user"; password = "password" } | ConvertTo-Json) `
  -ContentType "application/json"

# Call a protected endpoint
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/users/me/ `
  -Headers @{ Authorization = "Bearer <access_token>" }
```
