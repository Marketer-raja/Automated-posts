"""Daily Marketer Raja Instagram carousel. Run --mode sample for an offline preview."""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from instagram.copywriter import write
from instagram.design import render
from instagram.discover import rank
from instagram.history import History
from instagram.meta import Instagram

OUTPUT = Path("instagram-output")
SAMPLE = {
    "slides": ["Where did your leads come from?", "One form can capture leads from several campaigns.",
               "Your sales team needs the source before it can compare lead quality.",
               "Save the campaign name with every enquiry."],
    "caption": "Design preview · Example marketing tip. Track campaign names alongside enquiries so you can compare lead quality. #MarketerRaja #GoogleAds"
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("sample", "preview", "publish"), default="sample")
    mode = parser.parse_args().mode
    OUTPUT.mkdir(exist_ok=True)
    for name in ("01.jpg", "02.jpg", "03.jpg", "04.jpg", "caption.txt", "story.json", "skip.txt"):
        (OUTPUT / name).unlink(missing_ok=True)
    if mode == "sample":
        post, story = SAMPLE, {"sample": True, "category": "Google Ads"}
    else:
        live = mode == "publish"
        history = History(live) if live or os.getenv("GH_TOKEN") else None
        records = history.records if history else {}
        ig = Instagram() if live or (os.getenv("META_ACCESS_TOKEN") and os.getenv("IG_USER_ID")) else None
        if live:
            ig.reconcile(history)
            today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
            if any(r.get("run_day") == today and r["state"] == "published" for r in records.values()):
                return skip("A carousel has already been published today.")
        affinity = ig.audience_scores(records) if ig else {}
        # A thin announcement may be rejected by the writer. Try the next candidate.
        candidates = rank(records, affinity)
        if not candidates:
            return skip("No eligible, fresh, unused story found.")
        for story in candidates:
            post = write(story)
            if post:
                break
        else:
            return skip("The top candidates lacked enough material for a factual carousel.")
    render(post["slides"], OUTPUT)
    (OUTPUT / "caption.txt").write_text(post["caption"], encoding="utf-8")
    (OUTPUT / "story.json").write_text(json.dumps({**story, "slides": post["slides"]},
                                                   indent=2, ensure_ascii=False), encoding="utf-8")
    if mode == "publish":
        ig.publish(story, post, OUTPUT, history)


def skip(message):
    print(message)
    (OUTPUT / "skip.txt").write_text(message, encoding="utf-8")


if __name__ == "__main__":
    main()
