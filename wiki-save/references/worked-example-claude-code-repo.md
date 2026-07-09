# Worked Example: Claude Code Wiki Repo (2026-06-04)

## Situation
User sent Claude Code CLI commands text via `/wiki-save` (Discord trigger: "저장: ...").
Content: Claude Code commands, skills, and features documentation.

## Classification Decision
- `hermes-slash-commands` (30% match — "명령어" keyword, but wrong context: Hermes vs Claude Code)
- `claude-skill-library` (25% match — "스킬" keyword, but about skills catalog not CLI docs)
- `hermes-wiki` (20% match — "코드/일반" keyword, generic)
- **Result: < 40% for all existing repos → New repo needed**

User confirmed: "새 레포 생성: hermes-wiki-claude-code"

## Execution Timeline

| Step | Action | Duration |
|:-----|:-------|:--------:|
| 1 | GitHub API: `POST /user/repos` → created `hermes-wiki-claude-code` (private) | 2s |
| 2 | `git clone` empty repo → initialized LLM Wiki structure | 3s |
| 3 | Created 6 wiki pages (commands, skills, config, MCP, advanced, CLI modes) | 60s |
| 4 | Updated `index.md` with full catalog + `README.md` | 5s |
| 5 | `git commit + push` (7 files, 411 lines added) | 3s |
| 6 | Updated `gh-token.md` (repo count 10→11), `hermes-wiki/index.md` (Repo Map) | 10s |
| 7 | Updated `wiki-save` SKILL.md (catalog + signatures + count) | 5s |
| 8 | Logged to `hermes-logs/2026-06-04-0715.md` | 3s |
| 9 | Memory update | 2s |
| **Total** | End-to-end | ~90s |

## 카테고리 시그니처 (추가됨)

```yaml
hermes-wiki-claude-code: ["Claude Code", "Claude", "명령어", "CLI", "코드 리뷰", "워크플로우", "자동화", "개발자 도구", "agent"]
```

## Resulting Repo Structure

```
hermes-wiki-claude-code/
├── index.md                         ← 카탈로그 (7개 페이지 링크)
├── README.md
├── command-reference/
│   └── claude-code-commands.md      ← 40+ 명령어 전체 목록
├── skills/
│   └── claude-code-skills.md        ← 스킬 시스템 (생성/설치/Hub)
├── configuration/
│   ├── claude-code-config.md        ← claude.json + 환경변수
│   └── claude-code-settings.md      ← settings.json approvals/hooks
├── mcp/
│   └── claude-code-mcp.md           ← MCP 연동 가이드
├── advanced/
│   └── claude-code-advanced.md      ← 워크스페이스/훅/Diff 편집
├── cli-modes/
│   └── claude-code-cli-modes.md     ← 비대화형/Print/Pipe 모드
└── harness-engineering/
    └── claude-code-harness-config.md ← Harness Eng 설정 템플릿
```

## Key Lessons
1. **Use clarify() when score < 40%** — user confirmed "새 레포" decisively
2. **LLM Wiki naming convention**: `hermes-wiki-{topic}` with lowercase-hyphen
3. **Default branch**: GitHub now creates repos with `main` branch (no `master` rename needed)
4. **`ghp_` token scope**: `repo` scope is sufficient for creating private repos via API
5. **Subsequent enrichment**: user asked to add more content (settings.json, harness-engineering) — handle as iterative page additions to the same repo, not a new classification cycle
