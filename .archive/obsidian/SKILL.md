---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `~/.hermes/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

## GitHub Sync Setup (Super Repo + Submodules)

When the user asks about syncing Obsidian with ALL GitHub repos from one account, use this approach.

### Recommended Architecture: Super Repo

Create a **super repo** that aggregates all wiki repos as submodules. Clone once, sync all.

```
GitHub: hermes-wiki-super ← 11 wiki repos as submodules
  ↓
Laptop: git clone --recurse-submodules → Obsidian Vault → Obsidian Git (Pull on startup)
  + sync.sh (cron every 10 min): bidirectional pull + push
  ↓
iOS: Working Copy → clone hermes-wiki-super (submodule-aware)
```

### Key components
1. **Super repo** — lightweight repo with only `.gitmodules` + `README.md` + `sync.sh`
2. **`sync.sh`** — **양방향 sync** 스크립트 (pull + submodule foreach push + super ref 갱신)
3. **cron**: `*/10 * * * *` — sync.sh 10분마다 실행
4. **Obsidian Git**: `Pull on startup: ON` (sync.sh가 주 sync, Obsidian Git은 백업)

### sync.sh 핵심 로직
```bash
# 1. Pull — Hermes가 푸시한 내용 반영
git pull
git submodule update --remote

# 2. Push — Obsidian에서 수정한 내용 자동 커밋+푸시
git submodule foreach 'git add -A && git diff --cached --quiet || (git commit -m "obsidian: auto-sync $(date +%Y-%m-%d_%H:%M)" && git push)'

# 3. Super ref 갱신
git add -A && git diff --cached --quiet || (git commit -m "sync: update submodule refs $(date +%Y-%m-%d_%H:%M)" && git push)
```

### ⚠️ Critical: sync.sh must be IN the super repo
When creating setup instructions for this pattern: **create the sync.sh file in the repo itself**, not just described in the README. The user needs to `chmod +x sync.sh` and cron it — they should not have to copy-paste code from documentation.

### Crontab 등록 (macOS 주의)

zsh에서 `*/10`을 바로 입력하면 glob 패턴으로 오해해 `zsh: no matches found` 에러 발생.

**올바른 방법** — echo + pipe 한 줄로 등록:
```bash
(crontab -l 2>/dev/null; echo "*/10 * * * * ~/path/to/sync.sh >> ~/path/to/sync.log 2>&1") | crontab -
```

이 방식의 장점:
- `crontab -e` (vi/nano) 안 열어도 됨
- zsh glob 오류 회피 (큰따옴표로 감싸져 있으므로)
- `~` (tilde) 경로 사용 가능

**문서화 시 경로 표기**: 사용자는 `/Users/xxx/` 같은 절대경로보다 `~`를 선호함. README나 examples는 `~`로 통일할 것.

### When to create a super repo
✅ Use when: user has 4+ wiki repos they want to sync to Obsidian in one go
❌ Don't use when: 1-2 repos only (just clone directly)

### Trigger phrases
"모든 레포 동기화", "Obsidian GitHub sync", "super repo", "hermes-wiki-super", "서브모듈 sync", "양방향 sync"

### Related files
- `references/obsidian-github-sync-guide.md` — 세부 셋업 가이드

### Pitfalls
- 🔴 **Submodule 내부 수정**: Obsidian Git 플러그인이 submodule 내부 변경을 감지 못 함. 반드시 sync.sh 같은 cron 스크립트 필요.
- 🔴 **sync.sh는 README에만 적지 말 것**: README에 설명만 적고 sync.sh 파일을 안 올리면 사용자가 직접 만들어야 함. **실제 파일을 repo에 포함할 것.**
- 🟡 **처음 클론**: `--recurse-submodules` 필수. 잊으면 submodule 디렉토리가 비어 있음.
- 🟡 **충돌**: Hermes와 Obsidian에서 같은 파일을 동시에 수정하면 충돌. 가능하면 Hermes가 주 작성, Obsidian은 읽기+간단 수정 용도로 사용.
- 🟡 **Working Copy (iOS)**: submodule을 지원하나 자동화 제한적. 수동 Pull 필요.
- 🟡 **강제 push 금지**: `git push -f`는 다른 커밋을 덮어씀.
