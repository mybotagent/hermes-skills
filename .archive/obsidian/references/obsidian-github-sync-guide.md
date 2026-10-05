# Obsidian-GitHub Sync Setup Guide

> 사용자: aiprofit (mybotagent GitHub 계정)
> 날짜: 2026-06-05
> 목표: 계정 내 모든 private 레포 → Obsidian 노트북 + iOS Working Copy

## 최종 아키텍처: Super Repo + Submodules

hermes-wiki-super (https://github.com/mybotagent/hermes-wiki-super) — 모든 wiki 레포를 submodule로 모은 super repo.

```
GitHub: mybotagent/hermes-wiki-super (11개 submodule)
  ↓ clone --recurse-submodules
노트북: Obsidian Vault/hermes-wiki-super/
  ├── wiki/hermes-wiki/
  ├── wiki/hermes-wiki-portfolio/
  ├── wiki/hermes-wiki-codex/
  ├── ... (11개)
  ├── sync.sh  ← cron 10분마다 양방향 sync
  └── sync.log
  ↓ Working Copy
iOS: submodule-aware 자동 관리
```

## 셋업 순서

### 1. Obsidian Git 플러그인 설치
- Obsidian 설정 → 커뮤니티 플러그인 → "Obsidian Git" 설치 및 활성화
- 설정: `Pull on startup: ON`, `Pull interval: 0`

### 2. 최초 1회 클론
```bash
git clone --recurse-submodules https://github.com/mybotagent/hermes-wiki-super.git \
  ~/Documents/Obsidian\ Vault/hermes-wiki-super
```

### 3. sync.sh 준비 (이미 repo에 포함됨)
```bash
chmod +x ~/Documents/Obsidian\ Vault/hermes-wiki-super/sync.sh
```

### 4. cron 등록 (10분마다 양방향 sync)
```bash
(crontab -l 2>/dev/null; echo "*/10 * * * * ~/Documents/Obsidian Vault/hermes-wiki-super/sync.sh >> ~/Documents/Obsidian Vault/hermes-wiki-super/sync.log 2>&1") | crontab -
```

> `crontab -e`로 vi 열지 않아도 됨. 한 줄 복붙으로 끝.

### 5. iOS — Working Copy
- Working Copy → Clone: `mybotagent/hermes-wiki-super`
- Working Copy가 submodule도 알아서 관리해줌
- 주기적으로 Pull → Obsidian에서 Open

## 포함된 레포 (11개)
- hermes-wiki (INDEX 저장소)
- hermes-wiki-portfolio
- hermes-wiki-schedule
- hermes-wiki-claude-code
- hermes-wiki-codex
- hermes-logs
- stock-analysis-toolkit
- subagents-library
- harness-engineering-wiki
- ai-job-analysis
- hermes-slash-commands

## 주의사항
- **sync.sh가 모든 걸 처리**: Obsidian Git 플러그인은 submodule 내부를 감지 못함. sync.sh 크론이 pull + push를 모두 커버.
- **충돌**: Hermes와 Obsidian에서 같은 파일 동시 수정 시 충돌 가능. Hermes가 주 작성자.
- **신규 레포**: super repo submodule 목록에 추가 필요. 자동 감지 안 됨.
