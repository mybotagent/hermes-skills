# Capacity Planning — Wiki 추가 가능 개수 추정

## 측정된 실측치 (12 wiki / 223 노드 / 409 엣지 / 1.9GB RAM)

```
위키 .md + .git:   ~1 MB / 위키 (12개 합계 11MB)
Neo4j DB 본체:     ~13.8 KB / 노드 (3MB / 223 노드)
Neo4j transactions: 258MB (백업/임시, 압축 가능)
bge-m3 임베딩:     1.5 KB / 노드 (384 float32)
평균 위키 크기:     18 페이지
```

## 계산 공식 (여유 N GB일 때)

```python
# 위키 1개당 평균 비용
md_per_wiki = 0.92 MB           # .md + .git
neo4j_per_wiki = 0.24 MB        # 노드 + 벡터
cost_per_wiki = md_per_wiki + neo4j_per_wiki  # ≈ 1.2 MB

# 위키 수
n_wiki = (free_gb * 1024) / cost_per_wiki_mb

# 큰 위키 (페이지 100)
cost_big = cost_per_wiki * 5.5
n_big = (free_gb * 1024) / cost_big

# 매우 큰 위키 (페이지 1000)
cost_huge = cost_per_wiki * 55
n_huge = (free_gb * 1024) / cost_huge
```

## 실측 결과 (15GB 여유 기준)

| 시나리오 | 추가 가능 | 현재 12개 대비 |
|---------|----------|---------------|
| 일반 위키 (18 페이지) | **~13,000개** | 1,000배 |
| 큰 위키 (100 페이지) | ~2,400개 | 200배 |
| 매우 큰 위키 (1000 페이지) | ~240개 | 20배 |

## 디스크보다 빨리 오는 한계

| 한계 | 임계치 | 신호 |
|------|--------|------|
| **RAM 1.9GB** | Neo4j swap 사용 | `journalctl -u neo4j` 에서 OOM |
| **Vector 검색 속도** | 노드 5천+ | 응답 > 500ms |
| **임베딩 계산** | 페이지 100개 = 1-2초 | cron 증분 시간 급증 |

## 안전한 확장 sweet spot

- **100~500 위키 (페이지 5,000~15,000개)** — 1.9GB RAM에서 무리 없음
- **10~40배 확장이 현실적 안전선** (그 이상은 RAM 업그레이드 권장)

## 디스크 정리 시 안전 정리 대상

| 항목 | 크기 | 안전도 | 비고 |
|------|------|--------|------|
| `/tmp/pip-unpack-*` | 1-2GB | 🟢 안전 | pip install 완료 후 |
| `/tmp/neo4j-community.tar.gz` | 150MB | 🟢 설치 후 안전 | 1회성 |
| `~/.cache/pip/http-v2/*.body` | ~2GB | 🟡 신중 | venv 재설치 시 필요 |
| `~/.cache/uv/` | 1.1GB | 🟢 uv 안 쓰면 안전 | **uv 사용 시 보존** |
| `~/.cache/camoufox/` | 1.4GB | 🟢 browser skill 미사용 시 | 확인 후 |
| `~/.cache/ms-playwright/` | 260MB | 🟢 playwright 미사용 시 | 확인 후 |

## 절대 보존

- `~/.cache/huggingface/` — bge-m3 모델 캐시 (Neo4j 사용 중)
- `~/.venv-neo4j/` — Python 가상환경
- `~/.hermes/state.db` — Hermes 상태 DB
- `/usr/local/neo4j/data/` — Neo4j 데이터
- 모든 `/home/ubuntu/<project>/` 디렉토리
