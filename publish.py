import os
import sys
import time
import requests

GRAPH_VERSION = "v27.0"


def main():
    access_token = os.getenv("META_ACCESS_TOKEN")
    ig_user_id = os.getenv("IG_USER_ID")
    image_url = os.getenv("IMAGE_URL")
    caption = os.getenv("CAPTION", "Automated post via GitHub Actions")

    if not access_token or not ig_user_id or not image_url:
        print("Missing required env vars: META_ACCESS_TOKEN, IG_USER_ID, IMAGE_URL")
        sys.exit(1)

    base_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{ig_user_id}"

    # Step 1: Create media container (requires a publicly reachable image URL)
    create_res = requests.post(
        f"{base_url}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    create_res.raise_for_status()
    creation_id = create_res.json().get("id")
    print(f"Created container ID: {creation_id}")

    if not creation_id:
        print("No creation_id returned:", create_res.text)
        sys.exit(1)

    time.sleep(3)

    # Step 2: Publish media container
    publish_res = requests.post(
        f"{base_url}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    publish_res.raise_for_status()
    print("Published media response:", publish_res.json())


if __name__ == "__main__":
    main()
