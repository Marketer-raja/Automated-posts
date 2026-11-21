import email.utils
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .net import fetch

SOURCES = Path(__file__).with_name("sources.json")
STOP = set("this that with from your into about now new what have more google meta openai announces introducing release launches for the and".split())


def clean(value):
    return " ".join(html.unescape(re.sub("<[^>]+>", " ", value or "")).split())


def tokens(value):
    return set(re.findall(r"[a-z0-9][a-z0-9.-]{2,}", value.lower())) - STOP


def entries(url):
    root = ET.fromstring(fetch(url))
    for node in root.iter():
        if node.tag.split("}")[-1] not in ("entry", "item"):
            continue
        fields = {}
        for child in node:
            key = child.tag.split("}")[-1]
            value = "".join(child.itertext())
            if key == "link":
                if child.get("rel", "alternate") != "alternate":
                    continue
                value = child.get("href", value)
            fields.setdefault(key, value)
        yield fields


def date_of(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        result = email.utils.parsedate_to_datetime(value)
    if result.tzinfo is None:
        raise ValueError("Undated timezone")
    return result.astimezone(timezone.utc)


def rank(history, affinity=None, now=None):
    now = now or datetime.now(timezone.utc)
    candidates = []
    successes = 0
    for category, source, url, pattern in json.loads(SOURCES.read_text()):
        try:
            items = list(entries(url))
            if not items:
                raise ValueError("empty feed")
            successes += 1
        except Exception as exc:
            print(f"Source unavailable: {source} ({type(exc).__name__})")
            continue
        for row in items:
            title = clean(row.get("title"))
            body = max((clean(row.get(k)) for k in ("encoded", "content", "summary", "description")), key=len)
            if len(body) < 65 or not re.search(pattern, title + " " + body[:400], re.I):
                continue
            try:
                stamp = date_of(row.get("published") or row.get("pubDate") or row.get("updated", ""))
            except (ValueError, TypeError, OverflowError):
                continue
            age = (now - stamp).total_seconds() / 3600
            if not 0 <= age <= 72:
                continue
            parts = urlsplit(row.get("link", ""))
            if parts.scheme != "https" or not parts.hostname:
                continue
            link = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
            key = hashlib.sha256(link.encode()).hexdigest()[:20]
            if key in history:
                continue
            if source.endswith("SDK releases") or source.endswith("ADK releases"):
                title = source.replace(" releases", "") + " " + title
            kind = "AI agents" if category == "AI tools" and re.search(r"\bagent(s|ic)?\b", title, re.I) else category
            if any(item.get("title", "").casefold() == title.casefold() for item in history.values()):
                continue
            candidates.append(dict(key=key, title=title, category=kind, source=source, url=link,
                                   date=stamp.date().isoformat(), excerpt=body[:6000], age=age))
    if not successes:
        raise RuntimeError("All primary feeds failed. Check the workflow logs.")
    if not candidates:
        return []
    feeds = {"India search interest": "https://trends.google.com/trending/rss?geo=IN",
             "Industry coverage": "https://searchengineland.com/feed"}
    for label, url in feeds.items():
        try:
            signals = []
            for row in entries(url):
                date = row.get("pubDate") or row.get("published") or row.get("updated", "")
                try:
                    if 0 <= (now - date_of(date)).total_seconds() <= 72 * 3600:
                        signals.append(tokens(clean(row.get("title"))))
                except (ValueError, TypeError):
                    continue
            for story in candidates:
                words = tokens(story["title"])
                if any(len(words & signal) >= 2 and len(words & signal) / max(1, min(len(words), len(signal))) >= 0.6 for signal in signals):
                    story.setdefault("signals", []).append(label)
        except Exception as exc:
            print(f"Optional signal unavailable: {label} ({type(exc).__name__})")
    return sorted(candidates, reverse=True, key=lambda s: 24 * len(s.get("signals", [])) + (affinity or {}).get(s["category"], 0) - s["age"] / 6)
