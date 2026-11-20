import os
import sys
import time
import requests

GRAPH_VERSION = "v26.0"


def main():
    access_token = os.getenv("META_ACCESS_TOKEN")
    ig_user_id = os.getenv("IG_USER_ID")
    image_url = os.getenv("IMAGE_URL")
    caption = os.getenv("CAPTION", "Automated post via GitHub Actions")

    if not access_token or not ig_user_id or not image_url:
        print("Missing required env vars: META_ACCESS_TOKEN, IG_USER_ID, IMAGE_URL")
        sys.exit(1)

    host = "graph.instagram.com" if access_token.startswith("IGA") else "graph.facebook.com"
    base_url = f"https://{host}/{GRAPH_VERSION}/{ig_user_id}"

    create_res = requests.post(
        f"{base_url}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    if not create_res.ok:
        print(f"Step 1 failed ({create_res.status_code}): {create_res.text}")
        sys.exit(1)

    creation_id = create_res.json().get("id")
    print(f"Created container ID: {creation_id}")

    time.sleep(3)

    publish_res = requests.post(
        f"{base_url}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    if not publish_res.ok:
        print(f"Step 2 failed ({publish_res.status_code}): {publish_res.text}")
        sys.exit(1)

    print("Published media response:", publish_res.json())


if __name__ == "__main__":
    main()
