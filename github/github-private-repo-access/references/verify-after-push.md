# Verification Cheat Sheet — After Pushing to a GitHub Repo

When you've just committed + pushed and need to confirm the artifact actually
landed on GitHub (especially for private repos), use this recipe. Each step
checks a different layer; passing all four gives you high confidence the user
will see the artifact when they open the repo in their browser.

## The Four Layers

| # | Layer | What it proves | What it doesn't prove |
|---|-------|----------------|----------------------|
| 1 | git ls-remote | Your local push reached the remote | The *file content* is what you intended |
| 2 | API contents/ | The file *exists* in the tree with the right size | The bytes are correct (only SHA is shown) |
| 3 | raw fetch + byte check | The exact bytes match what you pushed | (final layer — proves everything) |
| 4 | vision_analyze (for images) | The image renders correctly with the right content | (also final layer) |

**You only need layers 1+3 for text files.** For images, **3+4** (or just 4 if
small enough to inline).

## Step 1 — git ls-remote

```bash
cd /path/to/local/repo
git ls-remote origin main
# Expected output: <sha>	refs/heads/main
# Compare SHA to your local: git rev-parse HEAD
```

If the SHAs match → your push reached the remote.

## Step 2 — API contents/ (size + SHA)

```bash
TOKEN=$(grep -E 'github\.com' ~/.git-credentials 2>/dev/null \
  | head -1 \
  | sed -E 's|^https?://[^:]+:||; s|@github\.com.*||')

curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/OWNER/REPO/contents/PATH" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'message' in d:
    print('ERROR:', d['message'])
else:
    print(f'name: {d[\"name\"]} | size: {d[\"size\"]}B | sha: {d[\"sha\"][:8]}')
"
```

If you get `name + size + sha` → file exists on GitHub.

## Step 3 — raw fetch + byte check

```bash
TOKEN=$(grep -E 'github\.com' ~/.git-credentials 2>/dev/null \
  | head -1 \
  | sed -E 's|^https?://[^:]+:||; s|@github\.com.*||')

# Download to a temp file
curl -s -H "Authorization: token $TOKEN" \
  "https://raw.githubusercontent.com/OWNER/REPO/BRANCH/PATH" \
  -o /tmp/verify.bin

# Compare to local
diff -q /tmp/verify.bin /path/to/local/file
# Expected: (silent) — files are identical

# For images, also check the magic bytes
file /tmp/verify.bin
# Expected: e.g. "PNG image data, 947 x 490, 8-bit/color RGBA, non-interlaced"
```

If `diff -q` is silent → byte-for-byte match.

## Step 4 — vision_analyze (for images only)

```python
from hermes_tools import vision_analyze

# Pass the downloaded file (or a local path to the source)
result = vision_analyze(
    image_url="/tmp/verify.bin",
    question="Does this image look correct? Check for rendering issues, "
             "missing labels, color problems, font issues, etc."
)
# Read result and judge
```

This is the highest-confidence check — it proves the image is *meaningfully
correct*, not just byte-identical to something broken.

## Common Pitfalls

### Pitfall 1: Anonymous raw fetch returns 404 even for files you have access to

GitHub returns 404 (not 401) when an anonymous request hits private repo
content. Easy to misdiagnose as "file didn't upload" when actually you just
forgot to send the token.

```bash
# WRONG — looks like a 404 / missing-file problem
curl -sI https://raw.githubusercontent.com/OWNER/REPO/main/file.png

# RIGHT — actually authenticates
TOKEN=$(...)
curl -sI -H "Authorization: token $TOKEN" \
  https://raw.githubusercontent.com/OWNER/REPO/main/file.png
```

### Pitfall 2: GitHub propagation delay (30s–2min)

If steps 1+2 pass but step 3 fails for a brand-new commit, wait 60s and retry.
The raw CDN lags behind the git server for a short window after push.

### Pitfall 3: Wrong branch

`git push origin main` only updates `refs/heads/main`. If the repo's default
branch is `master` or something else, you pushed to a different ref:

```bash
git symbolic-ref refs/remotes/origin/HEAD  # see what origin considers default
```

### Pitfall 4: API returns empty list instead of file

If `contents/PATH` returns `[]` instead of the file object, the path is wrong.
GitHub's contents API doesn't return 404 for non-existent paths — it returns
an empty list.

## Quick Decision Tree

```
Just pushed. Need to verify.
├─ Text/markdown file?
│  └─ Steps 1+3 are enough (skip API size check)
├─ Image/PNG?
│  └─ Steps 3+4 (byte check + vision_analyze)
├─ Binary of unknown type?
│  └─ Steps 1+2+3 (size + bytes, skip vision)
└─ Private repo and getting weird results?
   └─ Check Step 0 of diagnosis recipe in main SKILL.md first
```

## Example Session (2026-07-05)

Context: Just pushed `heatmap.png` (33,393 bytes, 947×490 PNG) to a private
repo via cron. Want to confirm it'll render in the README.

```bash
# Step 1
cd ~/daily-survey && git ls-remote origin main
# → f79335ec0daf0b1451b88f2aa970065ccb317a62	refs/heads/main  ✅

# Step 2
TOKEN=$(grep 'mybotagent:' ~/.git-credentials | head -1 | sed -E 's|.*://mybotagent:||; s|@github.com.*||')
curl -s -H "Authorization: token $TOKEN" "https://api.github.com/repos/mybotagent/daily-survey/contents/" \
  | python3 -c "import sys,json; [print(f'{x[\"name\"]:25} {x.get(\"size\",0):>7}B') for x in json.load(sys.stdin)]"
# → heatmap.png               33393B  ✅

# Step 3
curl -s -H "Authorization: token $TOKEN" "https://raw.githubusercontent.com/mybotagent/daily-survey/main/heatmap.png" \
  -o /tmp/verify.png
diff -q /tmp/verify.png ~/.hermes/survey/heatmap_latest.png  # silent ✅
file /tmp/verify.png
# → PNG image data, 947 x 490, 8-bit/color RGBA, non-interlaced  ✅

# Step 4
# vision_analyze(image_url="/tmp/verify.png", question="...")
# → confirms rendering: 5 rows, all labels visible, colors correct, no font issues  ✅
```

Four layers passing = the user will see the exact same image when they open
the README. Total time: ~10s.

## See Also

- Main SKILL.md, "Step 0" section — credential/token extraction recipe
- `github-auth` skill — how tokens get into `~/.git-credentials` in the first place