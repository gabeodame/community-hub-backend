import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from http.cookiejar import CookieJar
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
    return opener.open(req)


def _login(opener, base_url, username, password, csrf_cookie_name):
    _request_json(opener, "GET", f"{base_url}/api/v1/auth/csrf/")
    csrf_token = _cookie_value(opener.cookiejar, csrf_cookie_name)
    if not csrf_token:
        raise RuntimeError("CSRF cookie not set. Check CSRF settings.")
    _request_json(
        opener,
        "POST",
        f"{base_url}/api/v1/auth/token/",
        {"username": username, "password": password},
        headers={"X-CSRFToken": csrf_token},
    )


def _worker(
    worker_id,
    base_url,
    username,
    password,
    csrf_cookie_name,
    requests_per_worker,
    sleep_seconds,
):
    cookiejar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookiejar))
    opener.cookiejar = cookiejar

    if username and password:
        _login(opener, base_url, username, password, csrf_cookie_name)

    urls = [
        f"{base_url}/api/v1/health/",
        f"{base_url}/api/v1/posts/",
    ]
    if username and password:
        urls.append(f"{base_url}/api/v1/notifications/")
    start = time.perf_counter()
    errors = 0
    throttled = 0
    for i in range(requests_per_worker):
        url = urls[i % len(urls)]
        try:
            opener.open(Request(url, method="GET"))
        except Exception as exc:
            errors += 1
            if "HTTP Error 429" in str(exc):
                throttled += 1
                time.sleep(0.05)
            else:
                time.sleep(0.01)
        if sleep_seconds:
            time.sleep(sleep_seconds)
    elapsed = time.perf_counter() - start
    return {"worker": worker_id, "elapsed": elapsed, "errors": errors, "throttled": throttled}


def main():
    base_url = _env("BASE_URL", "http://127.0.0.1:8000")
    username = _env("USERNAME", "")
    password = _env("PASSWORD", "")
    csrf_cookie_name = _env("CSRF_COOKIE_NAME", "csrftoken")
    concurrency = int(_env("CONCURRENCY", "4"))
    total_requests = int(_env("REQUESTS", "100"))
    sleep_ms = int(_env("SLEEP_MS", "0"))
    sleep_seconds = sleep_ms / 1000.0 if sleep_ms > 0 else 0

    requests_per_worker = max(1, total_requests // concurrency)
    print(f"Base URL: {base_url}")
    print(f"Concurrency: {concurrency}, Requests: {requests_per_worker} per worker")
    if username:
        print("Auth: enabled")
    else:
        print("Auth: disabled")

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(
            executor.map(
                lambda wid: _worker(
                    wid,
                    base_url,
                    username,
                    password,
                    csrf_cookie_name,
                    requests_per_worker,
                    sleep_seconds,
                ),
                range(concurrency),
            )
        )
    total_elapsed = time.perf_counter() - start
    total_done = requests_per_worker * concurrency
    rps = total_done / total_elapsed if total_elapsed else 0
    total_errors = sum(item["errors"] for item in results)
    total_throttled = sum(item["throttled"] for item in results)
    print(f"Total: {total_done} requests in {total_elapsed:.2f}s ({rps:.2f} rps)")
    print(f"Errors: {total_errors} (429s: {total_throttled})")
    slowest = max(results, key=lambda item: item["elapsed"])
    print(f"Slowest worker: {slowest['worker']} in {slowest['elapsed']:.2f}s")


if __name__ == "__main__":
    main()
