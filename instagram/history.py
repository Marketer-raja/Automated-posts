import base64
import json
from urllib.parse import quote
from .net import api, required, RemoteError

BRANCH = "instagram-state"
FILE = "instagram-history.json"


class History:
    def __init__(self, live):
        self.base = "https://api.github.com/repos/" + required("GITHUB_REPOSITORY")
        self.headers = {"Authorization": "Bearer " + required("GH_TOKEN"),
                        "Accept": "application/vnd.github+json"}
        self.sha = None
        self.records = {}
        try:
            self.call(f"/git/ref/heads/{BRANCH}")
        except RemoteError as exc:
            if exc.status != 404:
                raise
            if live:
                sha = self.call("/git/ref/heads/" + quote(required("DEFAULT_BRANCH"), safe="/"))["object"]["sha"]
                self.call("/git/refs", "POST", {"ref": "refs/heads/" + BRANCH, "sha": sha})
            return
        try:
            item = self.call(f"/contents/{FILE}?ref={BRANCH}")
        except RemoteError as exc:
            if exc.status == 404:
                return
            raise
        self.sha = item["sha"]
        self.records = json.loads(base64.b64decode(item["content"]))

    def call(self, path, method="GET", payload=None):
        return api(self.base + path, method=method, payload=payload, headers=self.headers)

    def save(self):
        content = json.dumps(self.records, indent=2, ensure_ascii=False).encode()
        body = {"message": "Update Instagram publication history", "branch": BRANCH,
                "content": base64.b64encode(content).decode()}
        if self.sha:
            body["sha"] = self.sha
        self.sha = self.call("/contents/" + FILE, "PUT", body)["content"]["sha"]
