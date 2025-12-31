# Community Platform (Django + DRF) Scaffold

This scaffold is ready to run and test the health endpoint:

- `GET /api/v1/health/` -> `{ "status": "ok" }`

## Windows (PowerShell) quickstart

```powershell
cd community_platform

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

Scripts:

```powershell
.\scripts\dev.ps1
.\scripts\test.ps1
.\scripts\e2e.ps1
```

## Notes
- Uses a custom user model (`users.User`) from day one.
- JWT endpoints are wired but optional for health check:
  - `POST /api/v1/auth/token/`
  - `POST /api/v1/auth/token/refresh/`
