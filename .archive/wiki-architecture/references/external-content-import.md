# External Content → Karpathy Wiki Import Pattern

> Import structured external markdown repos (courses, docs, handbooks) into the wiki format.
> The key insight: restructure by **domain/topic**, not by source file structure.

## When to Use

- User provides a URL to a public repo (course, documentation site, tutorial series)
- User says "organize this content into my wiki the Karpathy way"
- You have a directory of loosely-structured markdown files that need reorganization

## Anti-Patterns

| Don't | Do |
|:------|:---|
| Keep the original folder structure (part1/, part2/, chapter-3/) | Restructure by **topic**: fundamentals/, tools/, concepts/ |
| Create one page per source file | **Merge** related files into topic pages (5–10 small files → 1 well-organized page) |
| Include config files, binaries, images in the wiki | Keep only `.md` files + essential diagrams (as links/png refs) |
| Mirror the source repo's README as index | Write a **new** index.md that's a browsable catalog by topic |

## Step-by-Step

### Step 1: Clone and Survey

```bash
git clone <source-url> source-temp
cd source-temp
find . -name "*.md" | sort
```

Quick-read every `.md` file to extract topics. Use `delegate_task` for large repos.

### Step 2: Design Topic Taxonomy

Group the content into **6–12 topic directories**. Examples from a real session:

| Source Structure | Target Structure |
|:----------------|:-----------------|
| `part1/01_*`, `part1/02_*` (lecture order) | `fundamentals/concepts.md`, `tools/comparison.md` |
| `part2/handout/*.md`, `part2/research/*.md` | `instruction-files/AGENTS.md`, `context-management/basics.md` |
| `part3/01-delegation*.md`, `part3/02-workflow*.md` | `delegation/policy.md`, `team-workflows/hooks.md` |
| `.agents/skills/*/SKILL.md` | `lab/skills-hub.md` or `tools/agent-platforms.md` |

Rule of thumb: if a topic has 3+ source files, it gets its own directory. If only 1–2 files, merge into a broader page.

### Step 3: Create Target Structure

```bash
mkdir -p ~/target-wiki/{fundamentals,tools,concepts,...}
```

### Step 4: Write Each Page — Content Rules

Each `.md` page should be:

1. **Self-contained** — a reader doesn't need to open 5 other files to understand this one
2. **Headered** — start with a `# Title`, then a 1-line description
3. **Opinionated** — include key quotes, conclusions, "the author argues that..."
4. **Practical** — include code snippets, config examples, CLI commands
5. **Linked** — cross-reference other pages at the bottom

### Step 5: Prune Basic Content Before Schema

**CRITICAL STEP — skip this and the wiki fills with noise.**

Before writing AGENTS.md, review every page you created and remove content that is:

**Always remove:**
- ❌ CLI basics (`cd`, `ls`, `pwd`, `mkdir`, `grep`, `find`, `man`) — anyone can Google
- ❌ Git basics (`git clone`, `git add`, `git commit`, `git push`, `git pull`) — no insight value
- ❌ Install/setup guides for well-known tools (Claude Code, Codex, Docker, etc.) — official docs are more accurate
- ❌ Course/lecture orientations — if the reader took the course, they don't need "what we'll learn in part 2"
- ❌ Tool comparisons that only restate official feature lists — keep only if they contain hard-won practical insights

**Keep:**
- ✅ Mental models, concepts, philosophies
- ✅ Patterns, anti-patterns, and pitfalls
- ✅ Architecture decisions and trade-offs
- ✅ Hard-to-discover workflows with real-world context
- ✅ Edge cases, debugging recipes, and known workarounds
- ✅ Opinions and analysis (not just summaries)

**Rule: the merged result should be SMALLER than the sum of the parts.** If you consolidated two repos and the result is bigger than each was alone, you kept too much noise.

**Example from a real session (2026-05-31):**
Two harness engineering wikis (40+ pages combined) → consolidated into 24 pages by removing CLI/Git basics, install guides, and orientation overview. The unified repo is smaller and more valuable than either original.

### Step 6: Write AGENTS.md

The schema file. For a topic wiki (not a thread wiki):

```markdown
## Layers

1. **Source** (immutable): `session_search`, chat history
2. **Wiki** (this repo): organized knowledge by topic
3. **Logs**: external log repo

## How to Use
1. Read `index.md` → find relevant topic
2. Open the topic page
3. Cross-reference related pages as needed
```

For a **thread wiki** (Discord thread specific), use the full 5-layer schema from the shared wiki's AGENTS.md.

### Step 6: Write index.md

Template:

```markdown
# Topic Wiki

> Structured knowledge from [source-name].
> See [AGENTS.md](AGENTS.md) for schema.

## Topics

| Topic | Page | Description |
|:------|:----|:------------|
| Fundamentals | [overview.md](fundamentals/overview.md) | Core philosophy |
| Tools | [comparison.md](tools/comparison.md) | Claude Code vs Codex |

## How to Use

1. Browse topics above
2. Follow links to detailed pages
3. Each page has cross-references at the bottom
```

### Step 7: Create Repo and Push

```python
import re, json, urllib.request

# Create private repo on GitHub
with open('/home/ubuntu/.git-credentials') as f:
    token = re.search(r'https://[^:]+:(.+)@github', f.read()).group(1)

req = urllib.request.Request(
    'https://api.github.com/user/repos',
    data=json.dumps({
        'name': repo_name,
        'description': desc,
        'private': True
    }).encode(),
    method='POST'
)
req.add_header('Authorization', f'token {token}')
urllib.request.urlopen(req)
```

```bash
# Clone, seed, push
git clone https://github.com/mybotagent/<repo>.git
# Copy all files into the clone
cd <repo>
git add -A
git commit -m "init: topic wiki from [source]"
git push -u origin main
```

⚠️ **Branch name trap**: `git init` creates `master`, but GitHub defaults to `main`.
If push fails with `src refspec main does not match any`:
```bash
git branch -m master main
git push -u origin main
```

### Step 8: Register in Shared Wiki

Add a reference in the shared wiki's `index.md` under "Quick Reference" or "Repo Map":

```markdown
| 🏗️ **Topic Name** | [mybotagent/repo-name](https://github.com/mybotagent/repo-name) | `~/.hermes/repo-name/` |
```

Also add to memory:
```
memory(action='add', target='memory', content='Topic wiki: mybotagent/repo-name (private). Local at ~/.hermes/repo-name/.')
```

### Step 9: Clean Up

```bash
rm -rf source-temp
```
