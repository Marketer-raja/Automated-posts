# Free Instagram carousel setup

Use a public GitHub repository with a standard ubuntu-latest Actions runner. This workflow skips private repositories to avoid metered runner usage. It uses public feeds, local text templates and Pillow. It stages the finished JPEGs publicly on the instagram-state branch for Meta to fetch. Free services have usage limits.

1. Extract this ZIP beside the repository README.md. Merge folders and replace included files. Commit and push to the default branch. If you installed the previous package, the changed files are publish.py, instagram/copywriter.py, instagram/meta.py, .github/workflows/instagram-automation.yml and this guide.
2. In Actions → Instagram Automation → Run workflow, choose sample for the design or preview for a fresh topic. Download the resulting workflow artifact within one day. If the feeds have no suitable story, the artifact contains skip.txt.
3. In Settings → Secrets and variables → Actions → Secrets, set META_ACCESS_TOKEN and IG_USER_ID for a professional Instagram account authorized to publish. Reuse your existing values. The built-in GitHub token stages images and records history. The state branch must allow Actions contents:write. You may set META_GRAPH_HOST to graph.instagram.com for Instagram Login or graph.facebook.com for Facebook Login if needed.
4. Select publish for one live test. Then set the repository Actions variable AUTO_PUBLISH to true for daily publishing at 11:30 AM India time. The job selects again at publication time, checks for duplicates and skips days without suitable material. Switch AUTO_PUBLISH to false to return to preview mode.
5. The previous workflow used OpenAI and Cloudinary. This workflow never calls either. Other workflows in your repository may have their own billing settings.

The poster uses the source headline, a short attributed excerpt, and category-specific questions and advice. Feed recency, secondary coverage, India search trends and optional account Insights influence topic ranking. These signals estimate audience interest. Instagram-wide trend monitoring is outside this workflow.

If a publish outcome is unclear, inspect the pending item in instagram-state/instagram-history.json and your Instagram profile. The next live run checks the existing parent container before allowing another post.
