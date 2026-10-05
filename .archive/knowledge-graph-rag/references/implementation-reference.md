# Session Reference: Phase 5-6 GraphRAG Implementation

## File Locations
| Component | Path |
|-----------|------|
| Super repo | `~/hermes-wiki-super/` |
| Meta scripts | `~/hermes-wiki-super/.metagraph/` |
| Skill plugin | `~/hermes-wiki-super/.metagraph/skill/` |
| Neo4j install | `/usr/local/neo4j/` |
| Systemd unit | `/etc/systemd/system/neo4j.service` |
| Venv | `~/.venv-neo4j/` |
| Cron scripts | `~/.hermes/scripts/neo4j_health.sh` |

## Key Commands

### Health Check
```bash
source ~/.venv-neo4j/bin/activate
python3 ~/hermes-wiki-super/.metagraph/check_health.py --verbose
# → 223 nodes, 409 edges, vector=✅, 431MB
```

### Query Knowledge Graph
```bash
source ~/.venv-neo4j/bin/activate
python3 ~/hermes-wiki-super/.metagraph/skill/query.py "your question" --top-k 5
```

### Full Reindex
```bash
source ~/.venv-neo4j/bin/activate
python3 ~/hermes-wiki-super/.metagraph/indexer.py
```

### Discover New Repos
```bash
source ~/.venv-neo4j/bin/activate
python3 ~/hermes-wiki-super/.metagraph/discover.py --check
python3 ~/hermes-wiki-super/.metagraph/discover.py --init-new
```

### Neo4j Systemd
```bash
sudo systemctl status neo4j.service   # check
sudo systemctl restart neo4j.service  # restart
sudo systemctl enable neo4j.service   # boot auto-start
```

### Force Kill + Clean Start (when locked)
```bash
sudo pkill -f org.neo4j
sleep 2
sudo systemctl start neo4j.service
```

## Cron Jobs
| Job ID | Name | Schedule | Type | Description |
|--------|------|----------|------|-------------|
| 65ef8dbdfa5d | neo4j-health-check | 08:00 KST (23:00 UTC) | no_agent | Silent when healthy, alert on failure |
| 972c64d3f4da | neo4j-incremental-index | 03:00 KST (02:00 UTC+8) | agent | discover → init → index → report |

## Database Test Queries
```cypher
// Count all
MATCH (n) RETURN count(n)
MATCH ()-[r]-() RETURN count(DISTINCT r)

// Per-repo stats
MATCH (n:Page) RETURN n.repo, count(n) ORDER BY count(n) DESC

// Vector index
SHOW INDEXES WHERE name = 'page_emb'

// Find by namespace
MATCH (n:Page {id: "hw:infra:cron-jobs"}) RETURN n

// Find connected pages
MATCH (n:Page {id: "hw:infra:cron-jobs"})-[r:LINKS]-(c) RETURN n.title, type(r), c.title
```

## Supported Repos (14 total, 12 indexed)
| Namespace | Repo | Pages | Content |
|-----------|------|-------|---------|
| aa | ai-agent-wiki | ✅ 17 | LLM Hallucination→DeepResearch/Manus |
| hw | hermes-wiki | ✅ 35 | Hermes Agent operation wiki |
| tp | trade-pipeline | ✅ 24 | Investment analysis pipeline |
| he | harness-engineering-wiki | ✅ 26 | FastCampus course wiki |
| am | ai-marketing-wiki | ✅ 20 | AI marketing knowledge |
| hp | hermes-prompts | ✅ 18 | Prompt library |
| cc | hermes-wiki-claude-code | ✅ 18 | Claude Code CLI wiki |
| hq | hermes-wiki-quant | ✅ 10 | Quant investing |
| cx | hermes-wiki-codex | ✅ 9 | Codex CLI wiki |
| hl | hermes-logs | ✅ 35 | Change log archive |
| aj | ai-job-analysis | ✅ 8 | AI job market analysis |
| hs | hermes-slash-commands | ✅ 3 | Slash command reference |
| hsd | hermes-wiki-schedule | ❌ uninitialized | Schedule wiki |
| sl | subagents-library | ❌ uninitialized | Sub-agent patterns |

## Design Decisions
1. **bge-m3 over DeepSeek embedding**: DeepSeek embedding API doesn't exist → bge-m3 (384d, multilingual, free)
2. **Local Neo4j over AuraDB**: $0 cost, portfolio value, 1.9GB RAM sufficient
3. **Query Router: universal over keyword**: Removed all hardcoded keyword matching in P6. pure vector × graph.
4. **Auto-discovery over manual NAMESPACES**: .gitmodules parser replaces 34 lines of hardcoded dict
5. **Incremental over full reindex**: git HEAD tracking saves time on large wiki sets
6. **New repo auto-ingest**: discover.py --check detects new .gitmodules entries → auto init + index
