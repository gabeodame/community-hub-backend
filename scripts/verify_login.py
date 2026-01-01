import json
import os
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


def _env(name, default=None):
    value = os.getenv(name, default)
    return value if value is not None else default


def _cookie_value(cookiejar, name):
    for cookie in cookiejar:
        if cookie.name == name:
            return cookie.value
    return None


def _request_json(opener, method, url, body=None, headers=None):
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        return opener.open(req)
    except HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code} for {url}: {payload}") from exc


def _request_form(opener, url, body, headers=None):
    data = urlencode(body).encode("utf-8")
    req = Request(url, data=data, method="POST")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        return opener.open(req)
    except HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code} for {url}: {payload}") from exc


def main():
    base_url = _env("BASE_URL", "http://127.0.0.1:8000")
    username = _env("USERNAME")
    password = _env("PASSWORD")
    csrf_cookie_name = _env("CSRF_COOKIE_NAME", "csrftoken")

    if not username or not password:
        raise SystemExit("Set USERNAME and PASSWORD env vars.")

    cookiejar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookiejar))
    opener.cookiejar = cookiejar

    _request_json(opener, "GET", f"{base_url}/api/v1/auth/csrf/")
    csrf_token = _cookie_value(cookiejar, csrf_cookie_name)
    if not csrf_token:
        raise SystemExit("CSRF cookie not set. Check CSRF settings.")

    resp = _request_form(
        opener,
        f"{base_url}/api/v1/auth/token/",
        {"username": username, "password": password},
        headers={"X-CSRFToken": csrf_token},
    )
    body = resp.read().decode("utf-8", errors="ignore")
    print(f"status={resp.status}")
    print(body or "<empty>")


if __name__ == "__main__":
    main()
