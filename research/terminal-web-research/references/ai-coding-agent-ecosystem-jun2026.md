# AI Coding Agent Ecosystem — June 2026 Field Notes

Session-specific intelligence gathered while researching the AI coding agent landscape for the 2026-06-03 → 2026-07-03 window. Facts verified via first-party sources during research — save as reference for follow-up sessions.

## Verified First-Party Sources (Live URLs)

| Source | URL | Notes |
|--------|-----|-------|
| Anthropic news index | https://www.anthropic.com/news | Next.js, server-rendered. Use `<a href="/news/...">` link extraction. |
| Anthropic Sonnet 5 launch | https://www.anthropic.com/news/claude-sonnet-5 | Jun 30, 2026. Pricing $2/$10 intro, $3/$15 after Aug 31. |
| Anthropic Seoul office | https://www.anthropic.com/news/seoul-office-partnerships-korean-ai-ecosystem | Jun 17, 2026. |
| Anthropic Claude Tag | https://www.anthropic.com/news/introducing-claude-tag | Jun 23, 2026. |
| OpenAI Codex releases | https://github.com/openai/codex/releases | Rust rewrite (`rust-v0.142.x` stable, `rust-v0.143.0-alpha.x` nightly). |
| OpenAI Codex API | https://api.github.com/repos/openai/codex/releases | Always use `curl -sL` — repo redirects on rename. |
| Cursor changelog | https://cursor.com/changelog | Next.js on Vercel. June 2026: 3.8 (Jun 18), 3.9 (Jun 22 + Jun 29), Team MCPs (Jun 30). |
| Devin (Cognition) blog | https://devin.ai/blog | Windsurf was acquired by Cognition and rebranded to "Devin Desktop" on Jun 2, 2026. |
| Devin Agentic MapReduce | https://devin.ai/blog/agentic-map-reduce | Jul 1, 2026. Whole-codebase reasoning architecture. |
| Devin Security Swarm | https://devin.ai/blog/security-swarm-eval | Jul 1, 2026. Powered by Agentic MapReduce. 50-vuln dataset across 14 languages. |
| Devin Fable 5 | https://devin.ai/blog/claude-fable-5-available-in-devin | Jul 1, 2026 update. Anthropic's frontier model, top of FrontierCode benchmark. |
| Devin Sonnet 5 in Devin | https://devin.ai/blog/claude-sonnet-5 | Jun 30, 2026. 30% less quota than Sonnet 4.6 through Aug 31. |
| Devin Kimi K2.7 + GLM 5.2 | https://devin.ai/blog/kimi-k27-glm-52-devin-desktop | Jun 24, 2026. Chinese OSS models added to Devin Desktop and CLI. |
| Devin Desktop rebrand | https://devin.ai/blog/windsurf-is-now-devin-desktop | Jun 2, 2026. Introduces Agent Command Center, Spaces, ACP protocol support. |
| Cline releases | https://github.com/cline/cline/releases | v4.0.x series: Sonnet 5 support added Jun 30. ClinePass subscription launched late June. |
| Roo Code releases | https://github.com/RooCodeInc/Roo-Code/releases | Quiet since v3.54.0 (May 15, 2026). No June releases found. |
| Aider releases | https://github.com/Aider-AI/aider/releases | **Stalled at v0.86.0 (Aug 9, 2025)** — over 10 months without a release. |
| OpenCode (anomalyco fork) | https://api.github.com/repositories/975734319 | Repo redirected from sst/opencode → anomalyco/opencode. 181k stars. |
| AGENTS.md spec | https://agents.md | 22,730 stars. Repo: https://github.com/agentsmd/agents.md |
| Agent Client Protocol | https://github.com/agentclientprotocol/agent-client-protocol | Open protocol for editor↔agent. 3,564 stars, Apache-2.0. |
| Simon Willison June | https://simonwillison.net/2026/Jun/ | 103 posts. Confirms MAI-Code-1-Flash, Uber $1,500/mo AI cap, Codex desktop. |
| Simon Willison July | https://simonwillison.net/2026/Jul/ | DSPy eval pattern, llm-coding-agent, Fable 5 for web. |

## Key Pricing Data Points (Anthropic, June 30, 2026)

| Model | Input $/MTok | Output $/MTok | Notes |
|-------|--------------|---------------|-------|
| Claude Sonnet 5 (intro through Aug 31) | $2 | $10 | Default in Free/Pro Claude Code plans |
| Claude Sonnet 5 (after Aug 31) | $3 | $15 | Regular pricing |
| Claude Opus 4.8 | $5 | $25 | Reference comparison model |

## Uber AI Tool Spending Policy (Bloomberg via Simon Willison, June 3, 2026)

- $1,500/month per tool per employee cap
- Applies to Cursor, Claude Code (and other agentic coding tools)
- Implies ~$36k/year per engineer AI spend at 2 tools
- Bloomberg source: Natalie Lung
- Per-engineer AI cap ≈ 11% of Uber median SWE comp ($330k/yr via Levels.fyi)

## Microsoft MAI Models (Microsoft Build, June 2, 2026)

- MAI-Thinking-1: 1T params, 35B active, reasoning — "preferred to Sonnet 4.6" in MSFT evals
- MAI-Code-1-Flash: 137B params, 5B active, purpose-built for GitHub Copilot + VS Code
- Both trained on "clean and appropriately licensed" data (later clarified = standard web crawl with UT1 filter)

## Known Blocked / Difficult Targets

- `openai.com/news/` — Cloudflare managed challenge; need browser or specific sub-URLs
- `kiro.dev` — `.dev` TLD blocked by `tirith` security scan in terminal commands
- `codeium.com/windsurf/changelog` — Returns "Page Not Found" post-Windsurf acquisition by Cognition; redirect to devin.ai

## Cloudflare Challenge Detection Snippet

```python
def is_cloudflare_challenge(html: str) -> bool:
    indicators = [
        'cdn-cgi/challenge-platform',
        'Enable JavaScript and cookies to continue',
        'cf_chl_opt',
    ]
    return any(i in html for i in indicators)

def is_real_content(html: str, min_size_kb: int = 30) -> bool:
    return not is_cloudflare_challenge(html) and len(html) > min_size_kb * 1024
```

Always check `len(html)` and the challenge signature before extraction. A 10KB response with `cdn-cgi` in body = wasted fetch.

## Next.js / Vercel Article Extraction Recipe (works for Anthropic, Cursor, Devin, Linear, Vercel blogs)

```python
import re, html as htmllib

def extract_article(path, start_marker='', length=3000):
    with open(path) as f:
        html = f.read()
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = htmllib.unescape(text)
    idx = text.find(start_marker) if start_marker else 0
    return text[max(0, idx):max(0, idx)+length]

# Article list extraction
links = re.findall(r'<a[^>]*href="(/blog/[^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
seen = set()
for href, content in links:
    if href in seen: continue
    seen.add(href)
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'\s+', ' ', text).strip()
    if text and len(text) < 200:
        print(f'{href}\n  {text[:200]}\n')

# Date extraction (often near titles in JSON or props)
import re
dates = re.findall(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}', html)
print(set(dates))
```

## GitHub Releases Filter Pattern

```python
import json
with open('/tmp/releases.json') as f:
    data = json.load(f)
# Stable only — critical signal for "what shipped" vs internal alphas
stable = [r for r in data if not r['prerelease']]
for r in stable[:10]:
    print(f"{r['tag_name']:30s} {r['published_at']:25s}")
    body = (r.get('body') or '')[:600]
    print('  ', body.replace('\n', ' | ')[:500])
```

Tag-pattern recognition (helps distinguish release trains):
- `rust-v0.142.x` + `rust-v0.143.0-alpha.x` = stable vs nightly split (Codex CLI)
- `v4.0.x` + `cli-v3.0.x` = VS Code ext vs CLI split (Cline)
- Tags with `-alpha.N` incrementing daily = rapid pre-release cadence

## Iteration Budget Rule for 30-50KB Deliverables (~50 calls cap)

- Phase 1 plan: 1-2 calls
- Phase 2 fetch (parallel batches): 15-20 calls
- Phase 3 extract (cache as JSON): 10-15 calls
- Phase 4 write_file (atomic): 1-2 calls
- Reserve: 10-15 calls for follow-ups

**Cache or die**: every extraction writes to `/tmp/*.json` so write_file can ingest in one call. Re-reading HTML to "remember" burns 3-5 calls per source.

## Follow-up Research Targets (for future sessions)

1. **GitHub Copilot Coding Agent** — needs specific June 2026 release notes (check `github.blog` or `github.com/features/copilot` blog tag).
2. **Cursor Composer 2** — search Cursor changelog for composer-related updates beyond what was captured.
3. **AWS Kiro** — `.dev` blocked; try alternative routes (AWS news blog, aws.amazon.com/blogs/aws).
4. **Gemini Code Assist / Jules** — Google properties, check blog.google or deepmind.google.
5. **GPT-5.5 release notes** — Simon referenced it but no OpenAI source captured. Try `platform.openai.com/docs/models`.
6. **AGENTS.md governance** — who maintains it? Last commit Mar 12, 2026 — is it dormant?
7. **MCP ecosystem** — June 2026 MCP server announcements, security incidents.
8. **Eval infrastructure vendors** — Braintrust, LangSmith, Helicone, Arize — June 2026 product moves.
9. **Geoffrey Litt's AIE 2026 talk** — "Understand to participate" framing — could surface at https://www.youtube.com/@geoffreylitt
10. **The AGENTS.md spec evolution** — see `https://agents.md` directly; check for v1.0 or formal governance announcement.