"""Create source-attributed carousel copy without a text-generation service."""
import re

ACTIONS = {
    "Google Ads": ("Does this apply to your campaigns?", "Check eligibility in Google Ads before changing a live campaign.", "#GoogleAds"),
    "Meta Ads": ("Will your ad account see the change?", "Check availability in Ads Manager before updating your campaign.", "#MetaAds"),
    "SEO": ("Which pages should you check first?", "Pick one relevant page and check the official guidance.", "#SEO"),
    "AI agents": ("Could this help your marketing team?", "Test one routine task on sample data before connecting your accounts.", "#AIAgents"),
    "AI tools": ("Is this worth adding to your workflow?", "Try the tool on one real brief and review the result.", "#AITools"),
}


def write(story):
    title = story["title"].strip()
    if not title or len(title) > 155:
        return None
    # Use a complete short source sentence. Avoid navigation text, URLs and fragments.
    sentences = re.split(r"(?<=[.!?])\s+", story["excerpt"])
    detail = next((s.strip() for s in sentences if 5 <= len(s.split()) <= 24
                   and len(s) <= 155 and s.endswith((".", "?", "!"))
                   and not re.search(r"https?://|cookie|subscribe to|sign up for", s, re.I)
                   and s.strip().casefold() != title.casefold()), None)
    if not detail:
        return None
    question, action, tag = ACTIONS[story["category"]]
    return {"slides": [title, detail, question, action],
            "caption": f"{title}\n\n{story['source']} reports: “{detail}”\n\n{action}\n\n"
                       f"Source · {story['source']} · {story['date']}\n{story['url']}\n\n{tag} #MarketerRaja"}
