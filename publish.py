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


            try:
            candidates = rank(records, affinity)
        except RuntimeError as exc:
            if str(exc) != "All primary feeds failed. Check the workflow logs.":
                raise
            print("News feeds unavailable. Using a marketing tip today.")
            candidates = []

        for story in candidates:
            post = write(story)
            if post:
                break
        else:
            tips = [
                ("Google Ads", "Which searches brought you leads?",
                 "Review the search terms behind your recent clicks.",
                 "Look for searches that describe a different service.",
                 "Review those terms before adding negative keywords."),

                ("Meta Ads", "Which opening line gets attention?",
                 "Write two openings for the same product and offer.",
                 "Keep the visual and audience consistent during your test.",
                 "Compare qualified enquiries as well as clicks."),

                ("SEO", "Does your page answer the search?",
                 "Pick one search query that already earns impressions.",
                 "Read the landing page from that searcher's perspective.",
                 "Move the clearest answer closer to the top."),

                ("AI agents", "Give your agent a practice run",
                 "Choose one routine task with a clear expected result.",
                 "Run it on sample data and inspect each action.",
                 "Set an approval step before it changes live records."),

                ("AI tools", "Can your AI summary be trusted?",
                 "Give the tool a short brief with three known facts.",
                 "Compare its summary with the original names and numbers.",
                 "Correct unsupported claims before sharing the result."),

                ("Google Ads", "Which leads became customers?",
                 "Label recent enquiries by campaign and sales outcome.",
                 "Compare how many qualified leads each campaign produced.",
                 "Review those results before moving your budget."),

                ("Meta Ads", "Does your landing page match your ad?",
                 "Read your ad headline and landing page side by side.",
                 "Check that the offer and next step match.",
                 "Fix the first point where the two disagree."),

                ("SEO", "Can visitors find your service page?",
                 "Open a related article on your own website.",
                 "Find the paragraph where a reader might need your service.",
                 "Add a descriptive link there if it helps the reader."),

                ("AI agents", "What should your agent do when unsure?",
                 "Give it a sample enquiry with a missing detail.",
                 "Check whether it asks a question or invents an answer.",
                 "Define when it should hand the task to a person."),

                ("AI tools", "Which tool writes the better brief?",
                 "Give two tools the same audience, offer, and word limit.",
                 "Score both drafts for accuracy, clarity, and editing time.",
                 "Choose the one that needs fewer factual corrections."),
            ]

            # Unused tips come first. After all ten, reuse the oldest one.
            last_used = {}
            for entry in records.values():
                if entry.get("state") == "published":
                    title = entry.get("title", "")
                    last_used[title] = max(
                        last_used.get(title, ""), entry.get("run_day", "")
                    )

            category, hook, detail, impact, action = min(
                tips, key=lambda tip: last_used.get(tip[1], "")
            )
            day = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
            story = {
                "key": f"marketing-tip-{day}",
                "title": hook,
                "date": day,
                "category": category,
                "source": "Marketer Raja",
                "url": "",
                "kind": "evergreen_tip",
            }
            hashtag = "#" + category.replace(" ", "")
            post = {
                "slides": [hook, detail, impact, action],
                "caption": (
                    f"{category} tip from Marketer Raja\n\n{hook}\n\n"
                    f"{detail} {impact}\n\n{action}\n\n"
                    f"{hashtag} #DigitalMarketing #MarketerRaja"
                ),
            }
            print(f"Selected daily tip: {hook}")

    
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
