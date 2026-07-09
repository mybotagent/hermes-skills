# Auto-Discovery Pattern (.gitmodules → namespace)

## Why This Exists

Phase 5 left `indexer.py` and `query.py` with hardcoded NAMESPACES dict
and hardcoded structural-search keyword categories. Adding a new wiki
repo required editing three places in two files. A new topic outside the
keyword map caused silent fallback to "most connected" results.

Phase 6 removed all of this and replaced it with a single `discover.py`
that parses `.gitmodules` at runtime. Adding a repo is now `git submodule add`
followed by the next cron tick.

## The Parse Function

```python
import configparser
def parse_gitmodules(path=".gitmodules"):
    cfg = configparser.ConfigParser()
    cfg.read(path)
    repos = {}
    for section in cfg.sections():
        if section.startswith("submodule "):
            # Section name format: 'submodule "wiki/ai-agent-wiki"'
            raw_name = section.split('"')[1]
            # Strip 'wiki/' prefix for clean repo name
            name = os.path.basename(raw_name)
            repos[name] = {
                "path": raw_name,           # e.g. "wiki/ai-agent-wiki"
                "url": cfg[section].get("url", ""),
            }
    return repos
```

Two important details:
1. `section.split('"')[1]` extracts the path between the first pair of double
   quotes in the section header. The configparser API gives you the whole
   `submodule "wiki/foo"` string, not a parsed key.
2. `os.path.basename()` strips `wiki/` to get just the repo name. The full
   path is preserved in `info["path"]` for `repo_path = WIKI_SUPER / info["path"]`.

## Namespace Generation Rules

```python
def auto_namespace(repo_name, existing=set()):
    # Step 1: known mappings preserve backward compatibility
    known = {
        "hermes-wiki": "hw", "trade-pipeline": "tp",
        "hermes-wiki-claude-code": "cc", "hermes-wiki-codex": "cx",
        "harness-engineering-wiki": "he", "hermes-logs": "hl",
        "hermes-wiki-quant": "hq", "ai-job-analysis": "aj",
        "ai-marketing-wiki": "am", "hermes-prompts": "hp",
        "hermes-slash-commands": "hs", "hermes-wiki-schedule": "hsd",
        "subagents-library": "sl",
    }
    if repo_name in known:
        ns = known[repo_name]
        # If known ns is taken by an auto-generated one, append digit
        if ns in existing:
            for i in range(2, 10):
                if f"{ns}{i}" not in existing:
                    return f"{ns}{i}"
        return ns

    # Step 2: auto from word initials
    clean = repo_name
    for prefix in ["hermes-wiki-", "hermes-", "wiki-"]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
            break
    words = [w for w in re.split(r'[-_\s]+', clean) if w]
    ns = "".join(w[0] for w in words[:2])[:2]
    if len(ns) < 2:
        ns = clean[:2] if len(clean) >= 2 else (clean + "x")[:2]
    if ns in existing:
        for i in range(2, 10):
            if f"{ns}{i}" not in existing:
                return f"{ns}{i}"
    return ns
```

**Tested examples (forward compatibility):**
- `hermes-wiki` → `hw` (known)
- `trade-pipeline` → `tp` (known)
- `ai-agent-wiki` → `aa` (auto: `a`i + `a`gent...)
- `my-new-wiki` → `mn`
- `coze-research` → `cr`

## Edge Cases Handled

1. **Uninitialized submodule**: `(repo_path / ".git").exists()` returns True
   even for submodules that haven't been checked out, because `.git` is a
   pointer file. Always check the path is populated with actual content
   (e.g., `find_wiki_pages(repo_path)` returns non-empty) before indexing.

2. **Module conflict on same prefix**: `harness-engineering-wiki` and
   `hermes-wiki` both start with `he`/`hw` but the known-mappings dict
   disambiguates them. If you add a new repo whose auto-initials collide
   with an existing one, the digit-suffix rule (`hw`, `hw2`, `hw3`) kicks in.

3. **Empty or single-word repo**: `clean` may be empty after stripping
   prefixes. Fallback is `clean[:2] or "xx"`.

4. **Already-named-but-NS-taken**: rare but possible if you reorganize.
   The collision loop handles this with digit-suffix.

## CLI Surface

```bash
# List all discovered repos
python3 discover.py

# JSON output for scripts
python3 discover.py --json

# Check if new/removed (exit 0 = no change, 1 = change)
python3 discover.py --check
# Exit 0: All repos tracked, no changes
# Exit 1: Changes detected: repo1, repo2

# Auto-initialize uninitialized submodules
python3 discover.py --init-new
# Output: Initialized: hermes-wiki-schedule, subagents-library
```

## Cron Integration

```bash
# Pre-step before incremental index
discover_check=$(python3 .metagraph/discover.py --check)
if [ $? -ne 0 ]; then
  echo "New repos detected: $discover_check"
  python3 .metagraph/discover.py --init-new
fi
python3 .metagraph/index_incremental.py
```

## The Before/After

**Before (Phase 5):**
```python
# indexer.py
NAMESPACES = {
    "hermes-wiki": "hw", "trade-pipeline": "tp",
    "hermes-wiki-claude-code": "cc", "hermes-wiki-codex": "cx",
    "harness-engineering-wiki": "he", "subagents-library": "sl",
    "hermes-logs": "hl", "hermes-wiki-quant": "hq",
    "ai-job-analysis": "aj", "ai-marketing-wiki": "am",
    "hermes-prompts": "hp", "hermes-slash-commands": "hs",
    "hermes-wiki-schedule": "hsd",
}

standalone = {"trade-pipeline": "~/trade-pipeline"}
```

**After (Phase 6):**
```python
# indexer.py
from discover import discover_repos
discovered = discover_repos(include_state=False)
for name, info in discovered.items():
    if info["initialized"] and info["path"] and info["path"].exists():
        repos[name] = info["path"]
```

**Cost difference for adding a new repo:** 4 places in 2 files → 1 git command.

## Lessons Learned (recorded for next session)

- Hardcoded config (NAMESPACES, keywords) silently drifts as the system grows.
- A single source of truth (`.gitmodules` for repos, `.index_state.json` for
  indexing state) is far easier to maintain than parallel dicts.
- When designing a system, ask: "what is the source of truth for X?" If
  there isn't one, create one or make the system read it from somewhere
  already canonical.
- Backward-compat mapping dicts are worth the ~20 lines. They let you
  swap the implementation without breaking IDs that already exist in
  Neo4j or downstream references.
