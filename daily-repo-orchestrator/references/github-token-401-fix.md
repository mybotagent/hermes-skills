# GitHub Token 401 Unauthorized — 2026-09-09

## 증상
```python
urllib.error.HTTPError: HTTP Error 401: Unauthorized
# curl 테스트 결과:
{"message": "Bad credentials", "status": 401}
```

`.env`에 저장된 `GITHUB_TOKEN`이 GitHub API에서 "Bad credentials" 반환.

## 원인
- PAT (Personal Access Token) 만료 또는 취소
- Fine-grained token의 repository access 권한 변경/만료
- 토큰이 GitHub 설정에서 삭제됨

## 진단 절차
```bash
# 1) 토큰으로 직접 테스트
source ~/.hermes/.env
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

# 2) 정상 응답 예시:
# {"login": "mybotagent", "id": ..., "name": "..."}

# 3) 401 응답:
# {"message": "Bad credentials", ...}
```

## 재발급 절차
1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. 새 토큰 생성:
   - **Resource owner**: `mybotagent`
   - **Permissions**: `Contents: Read and write`, `Issues: Read and write`, `Pull requests: Read and write`
   - **Repository access**: `All repositories` 또는 특정 repo 선택
3. 새 토큰 복사
4. `.env` 업데이트:
   ```bash
   # GITHUB_TOKEN=ghp_... 줄 교체
   sed -i 's/^GITHUB_TOKEN=.*/GITHUB_TOKEN=ghp_YOUR_NEW_TOKEN/' ~/.hermes/.env
   ```
5. 다시 진단:
   ```bash
   source ~/.hermes/.env
   curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   ```

## daily-repo-orchestrator에서의 401 처리
`daily_repo_orchestrator.py`의 `gh()` 함수에서 401 반환 시:
- 스크립트 전체 FAIL (exit 1)
- 로그: `urllib.error.HTTPError: HTTP Error 401: Unauthorized`
- 자동 복구 불가 — **수동 토큰 갱신 필요**

## 선제적 예방
- Fine-grained token은 **1년 만료** — 매년 갱신 필요
- 만료 1개월 전 GitHub에서 알림 이메일 발송
- `hermes-ecosystem-audit` 주기적 실행으로 token 유효성 검증 권장
