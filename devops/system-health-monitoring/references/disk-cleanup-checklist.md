# 디스크 정리 안전도 분류표

Quick reference for `system-health-monitoring` SKILL의 디스크 정리 섹션. 이 표만 봐도 안전/위험 항목 판단 가능.

## 🟢 안전 — 확인 없이 삭제 가능

| 경로 | 일반적 크기 | 설명 |
|------|------------|------|
| `/tmp/pip-unpack-*` | 100MB-500MB each, 총 ~2GB | pip install 중간 파일. venv에 패키지 설치 완료된 상태 |
| `/tmp/<pkg>-<ver>.tar.gz` | 50-300MB | 설치 완료된 패키지 소스 tarball |
| `/tmp/*.html` (1주일 이전) | 1-3MB each | 일회성 curl/크롤링 결과 |
| `/tmp/*.xml` (1주일 이전) | 1-5KB each | RSS/atom feed |
| `/tmp/*.log` (1주일 이전) | 1-50MB | set_xps.log, setRps.log 등 시스템 부팅 로그 |
| `/tmp/fastembed_cache/models--*--onnx-Q` | 200-300MB | 미사용 임베딩 모델 캐시 (현재 모델과 다르면 안전) |
| `/home/ubuntu/.cache/pip/http-v2/**/*.body` | 100-500MB each | pip HTTP 응답 캐시. 같은 패키지 재설치 시만 빨라짐 |

## 🟡 사용자 확인 필요

| 경로 | 일반적 크기 | 보존 신호 | 삭제 신호 |
|------|------------|----------|----------|
| `/home/ubuntu/.cache/pip/` (전체) | 1-3GB | `pip install` 빈번, 같은 패키지 재설치 | 트래픽 절약 우선, 시간 제약 |
| `/home/ubuntu/.cache/uv/` | 500MB-2GB | `uv` 쓰는 venv 있음 | uv 미사용 |
| `/home/ubuntu/.cache/huggingface/` | 100-500MB | `sentence-transformers` 사용 중 | 다른 임베딩 모델로 전환 |
| `/home/ubuntu/.cache/ms-playwright/` | 200-300MB | `playwright` import | 미사용 |
| `/home/ubuntu/.cache/camoufox/` | 1-2GB | `camoufox` 또는 browser skill 사용 | 미사용 |
| `/home/ubuntu/.cache/JNA/` | 1-10MB | Java 기반 도구 (Neo4j 등) | Java 미사용 |
| `/home/ubuntu/<project>/.git/` | 1-10MB | 활성 프로젝트 | git history만 (clone 다시 받기 가능) |
| `/home/ubuntu/<project>/__pycache__/` | 10-50MB | 활성 프로젝트 | `find . -name __pycache__ -exec rm -rf {} +` 안전 |
| `/home/ubuntu/<project>/node_modules/` | 100-500MB | 활성 Node 프로젝트 | `rm -rf && npm install` 가능 |
| `/home/ubuntu/<project>/.venv/` | 100-500MB | venv 활성 | 절대 보존 |

## 🔴 절대 안 됨

| 경로 | 일반적 크기 | 이유 |
|------|------------|------|
| `/home/ubuntu/*/venv/` | 100-500MB | Python venv. site-packages에 모든 의존성 |
| `/home/ubuntu/.venv*` | 100-500MB | venv |
| `/home/ubuntu/.hermes/state.db` | 100-300MB | Hermes 상태, 메모리, 사용자 청크 |
| `/home/ubuntu/.hermes/hermes-agent/` | 100-500MB | Hermes Agent 코드 자체 |
| `/home/ubuntu/.hermes/skills/` | 10-100MB | 스킬 라이브러리 |
| `/home/ubuntu/<active-project>/` | varies | 진행 중인 프로젝트 |
| `/home/ubuntu/.gitconfig`, `.git-credentials` | <1MB | GitHub 인증 |

## 디스크 사용률별 대응

| 사용률 | 상태 | 액션 |
|--------|------|------|
| <50% | 여유 충분 | 없음 |
| 50-70% | 정상 | 예방 점검만 |
| 70-85% | 주의 | 🟢 안전 항목 일괄 정리 (~2-3GB 확보 가능) |
| 85-95% | 위험 | 🟢 + 🟡 정리, 큰 캐시 점검 |
| >95% | 위험 | 모든 안전 항목 정리 + 🟡 협의 + Neo4j/서비스 재시작으로 메모리 swap 정리 |

## 일회성 정리 명령어 (안전 항목)

```bash
# 2-3GB 확보
rm -rf /tmp/pip-unpack-*
rm -f /tmp/neo4j-community.tar.gz
rm -f /tmp/*.tar.gz
rm -rf /tmp/fastembed_cache/  # 미사용 모델만

# 1-3GB 확보 (pip 재설치 느려짐 감수)
rm -rf /home/ubuntu/.cache/pip/http-v2/

# 200-300MB 확보 (playwright 미사용 시)
rm -rf /home/ubuntu/.cache/ms-playwright/

# __pycache__ 일괄 정리 (활성 프로젝트는 자동 재생성)
find /home/ubuntu -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find /home/ubuntu -name "*.pyc" -delete 2>/dev/null

# .git history 압축 (active 프로젝트)
git -C /home/ubuntu/<project> gc --aggressive --prune=now
```

## Pitfalls

1. **`rm -rf /tmp/*` 위험** — 시스템 부팅 로그, systemd-private 같은 디렉토리 같이 있음. **glob 패턴 신중히**
2. **`rm -rf .cache` 위험** — 사용자 인증 토큰, pip 캐시, OS 설정 섞여 있음. **하위 디렉토리별 판단**
3. **venv 보존 최우선** — `find /home/ubuntu -name "venv" -prune -o ...`로 venv 보호 후 작업
4. **`.hermes`는 Hermes 관리 영역** — 사용자 명시 요청 없이 `.hermes/*` 삭제 금지
5. **git gc --aggressive** — 활성 프로젝트는 시간 오래 걸림. **사용자 확인 후**
