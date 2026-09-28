# Low-RAM Neo4j Configuration (1.9GB)

Verified working on DigitalOcean VM (1.9GB RAM, 2 cores, Ubuntu 22.04).

## neo4j.conf Overrides

Add to `/usr/local/neo4j/conf/neo4j.conf`:

```ini
# Heap — critical for 1.9GB RAM
dbms.memory.heap.initial_size=256m
dbms.memory.heap.max_size=512m
dbms.memory.pagecache.size=256m

# Local-only (no auth needed)
dbms.security.auth_enabled=false

# Bolt connector
dbms.connector.bolt.listen_address=:7687
dbms.connector.bolt.advertised_address=:7687

# HTTP connector (disable if not needed)
dbms.connector.http.enabled=false
dbms.connector.https.enabled=false
```

## Memory Breakdown (observed)

| Component | Actual | Notes |
|-----------|--------|-------|
| Java heap | 262M/512M | G1GC, -Xms262144k -Xmx524288k |
| Page cache | ~256M | File mappings |
| JVM overhead | ~100M | Class metadata, GC, threads |
| **Total Neo4j** | ~430-500M | 2h+ idle |
| Peak with embedding | ~600M | During indexer run |
| Swap used | ~240M | Acceptable for background service |

## systemd Service File

```ini
[Unit]
Description=Neo4j Graph Database (Community, Local KB)
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/neo4j/bin/neo4j start
ExecStop=/usr/local/neo4j/bin/neo4j stop
ExecReload=/usr/local/neo4j/bin/neo4j restart
User=ubuntu
Group=ubuntu
PIDFile=/usr/local/neo4j/run/neo4j.pid
Restart=on-failure
RestartSec=10
LimitNOFILE=40000
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
```

## Java 17 Installation

```bash
sudo apt install -y openjdk-17-jre-headless
java -version
# Expected: openjdk version "17.0.x"
```

## Neo4j Installation

```bash
wget https://dist.neo4j.org/neo4j-community-5.26.0-unix.tar.gz
sudo tar xf neo4j-community-5.26.0-unix.tar.gz -C /usr/local
sudo mv /usr/local/neo4j-community-5.26.0 /usr/local/neo4j
sudo chown -R ubuntu:ubuntu /usr/local/neo4j
```

## Python Dependencies

```bash
python3 -m venv ~/.venv-neo4j
source ~/.venv-neo4j/bin/activate
pip install neo4j numpy sentence-transformers fastembed
```

## Recurring Maintenance

### Rebuild from scratch (schema + index + vector)
```bash
source ~/.venv-neo4j/bin/activate
cd ~/hermes-wiki-super/.metagraph
python3 create_schema.py    # create constraints + vector index
python3 indexer.py           # full index
```

### Verify vector index exists
```bash
source ~/.venv-neo4j/bin/activate
python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687')
with driver.session() as s:
    r = s.run('SHOW INDEXES WHERE name = \"page_emb\"')
    print('Vector index:', r.data()[0]['name'] if r.data() else 'NOT FOUND')
driver.close()
"
```
