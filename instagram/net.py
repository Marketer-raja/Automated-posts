import json
import os
import urllib.error
import urllib.request


def required(key):
    value = os.environ.get(key, "").strip()
    if not value:
        raise RuntimeError(f"Missing setting: {key}")
    return value


class RemoteError(RuntimeError):
    def __init__(self, status, host, detail=""):
        self.status = status
        super().__init__(f"{host} returned HTTP {status} {detail}")


def fetch(url, *, method="GET", data=None, headers=None, limit=10_000_000):
    from urllib.parse import urlsplit
    request = urllib.request.Request(url, data=data, method=method, headers={
        "User-Agent": "MarketerRaja-Carousel/1.0", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read(limit + 1)
            if len(body) > limit:
                raise ValueError("Remote response exceeds size limit")
            return body
    except urllib.error.HTTPError as exc:
        # Never print tokens, request URLs, signed upload forms or API bodies.
        raise RemoteError(exc.code, urlsplit(url).hostname) from None


def api(url, *, method="GET", payload=None, headers=None):
    data = None if payload is None else json.dumps(payload).encode()
    return json.loads(fetch(url, method=method, data=data, headers={
        "Content-Type": "application/json", **(headers or {})}))
