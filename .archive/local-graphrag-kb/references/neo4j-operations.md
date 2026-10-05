# Local Neo4j Knowledge Graph — Operation Guide

## Connection

| Item | Value |
|------|-------|
| URI | `bolt://localhost:7687` |
| Auth | 없음 (로컬 전용) |
| Sys svc | `neo4j.service` |

## Commands

```bash
# 상태
sudo systemctl status neo4j.service
/usr/local/neo4j/bin/neo4j status

# 재시작
sudo systemctl restart neo4j.service

# 헬스 체크
source ~/.venv-neo4j/bin/activate
python3 ~/hermes-wiki-super/.metagraph/check_health.py --verbose

# 전체 재인덱스
python3 ~/hermes-wiki-super/.metagraph/indexer.py

# 증분 인덱스
python3 ~/hermes-wiki-super/.metagraph/index_incremental.py
```

## Cron Jobs

| Job ID | Name | Schedule | Type |
|--------|------|----------|------|
| `65ef8dbdfa5d` | neo4j-health-check | 08:00 KST | no_agent |
| `972c64d3f4da` | neo4j-incremental-index | 03:00 KST | agent |

## State File

`~/.metagraph/.index_state.json` — tracks per-repo git HEAD.

## Troubleshooting

### "File is locked by another process" on startup

```bash
sudo /usr/local/neo4j/bin/neo4j stop
sudo pkill -f "org.neo4j"
sudo systemctl start neo4j.service
```

### Neo4j not listening on 7687

```bash
# Check if it's running
sudo systemctl status neo4j.service
# Check journal for errors
sudo journalctl -u neo4j.service --since "5 min ago" | tail -20
# Check port
ss -tlnp | grep 7687
```

### Incremental indexer shows 0 changed repos

State file is stale. Run with `--force`:
```bash
python3 ~/hermes-wiki-super/.metagraph/index_incremental.py --force
```

## Cypher Cheatsheet

```cypher
// Count everything
MATCH (n) RETURN count(n) AS pages
MATCH ()-[r]->() RETURN count(r) AS edges

// Repo breakdown
MATCH (n:Page) RETURN n.repo, count(n) ORDER BY count(n) DESC

// Wiki links from a page
MATCH (n:Page {id: "hw:infra:neo4j-local"})-[r:LINKS]->(to)
RETURN type(r), to.title

// Vector index check
SHOW INDEXES WHERE name = 'page_emb'

// Full-text search (by title)
MATCH (n:Page) WHERE n.title CONTAINS "cron" RETURN n.title, n.repo
```
