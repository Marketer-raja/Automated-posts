import base64
import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from .net import api, fetch, required, RemoteError
from .history import BRANCH


def upload(path, key, history):
    # Commit small carousel JPGs on the existing state branch. Use immutable URLs
    # so Instagram can never fetch an older image from a previous day's run.
    name = f"carousel-media/{key}/{path.name}"
    endpoint = "/contents/" + name
    content = path.read_bytes()
    body = {"message": f"Stage carousel image {path.name}", "branch": BRANCH,
            "content": base64.b64encode(content).decode()}
    try:
        existing = history.call(endpoint + "?ref=" + BRANCH)
    except RemoteError as exc:
        if exc.status != 404:
            raise
    else:
        body["sha"] = existing["sha"]
    result = history.call(endpoint, "PUT", body)
    revision = result["commit"]["sha"]
    url = f"https://raw.githubusercontent.com/{required('GITHUB_REPOSITORY')}/{revision}/{name}"
    for attempt in range(5):
        try:
            if fetch(url) == content:
                return url
        except RemoteError as exc:
            if exc.status != 404:
                raise
        if attempt < 4:
            time.sleep(5)
    raise RuntimeError("Public image download failed. Check repository visibility and retry.")


class Instagram:
    def __init__(self):
        token = required("META_ACCESS_TOKEN")
        default_host = "graph.instagram.com" if token.startswith("IGA") else "graph.facebook.com"
        self.host = os.getenv("META_GRAPH_HOST") or default_host
        if self.host not in ("graph.instagram.com", "graph.facebook.com"):
            raise ValueError("Invalid META_GRAPH_HOST")
        self.base = f"https://{self.host}/{os.getenv('META_GRAPH_VERSION') or 'v26.0'}"
        self.headers = {"Authorization": "Bearer " + token}
        self.account = required("IG_USER_ID")

    def post(self, endpoint, **params):
        result = fetch(self.base + "/" + self.account + "/" + endpoint, method="POST",
                       data=urlencode(params).encode(), headers=self.headers)
        return json.loads(result)["id"]

    def status(self, container):
        return api(f"{self.base}/{container}?fields=status_code", headers=self.headers)["status_code"]

    def ready(self, container):
        for _ in range(18):
            state = self.status(container)
            if state == "FINISHED":
                return
            if state in {"ERROR", "EXPIRED", "PUBLISHED"}:
                raise RuntimeError("Unexpected container state: " + state)
            time.sleep(10)
        raise TimeoutError("Instagram is still processing. Try again later.")

    def audience_scores(self, history):
        totals = {}
        posts = sorted((r for r in history.values() if r.get("media_id")),
                       key=lambda r: r["date"], reverse=True)
        for record in posts[:15]:
            try:
                data = api(f"{self.base}/{record['media_id']}/insights?metric=saved,shares,reach",
                           headers=self.headers)["data"]
                counts = {x["name"]: x["values"][0]["value"] for x in data}
                if counts.get("reach", 0):
                    rate = (counts["saved"] + counts["shares"]) / counts["reach"]
                    totals.setdefault(record["category"], []).append(rate)
            except (RemoteError, KeyError, IndexError, TypeError, OSError, ValueError):
                continue
        return {k: min(6, 100 * sum(v)/len(v)) for k, v in totals.items()}

    def publish(self, story, post, output, history):
        urls = [upload(output / f"{i:02d}.jpg", story["key"], history) for i in range(1, 5)]
        children = []
        for url in urls:
            child = self.post("media", image_url=url, is_carousel_item="true")
            self.ready(child)
            children.append(child)
        parent = self.post("media", media_type="CAROUSEL", children=",".join(children),
                           caption=post["caption"])
        self.ready(parent)
        record = {k: story[k] for k in ("title", "date", "category", "url")}
        record.update(state="pending", parent=parent, run_day=datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat())
        history.records[story["key"]] = record
        history.save()  # Persist before the irreversible request.
        media_id = self.post("media_publish", creation_id=parent)
        record.update(state="published", media_id=media_id)
        history.save()
        print("Published Instagram media", media_id)

    def reconcile(self, history):
        for record in history.records.values():
            if record["state"] != "pending":
                continue
            status = self.status(record["parent"])
            if status == "PUBLISHED":
                record["state"] = "published"
                history.save()
            elif status in {"EXPIRED", "ERROR"}:
                record["state"] = "failed"
                history.save()
            else:
                raise RuntimeError("Previous publish outcome is unresolved. Check the Instagram profile and instagram-state history before retrying.")
