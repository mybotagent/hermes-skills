#!/usr/bin/env python3
"""Neo4j schema: constraints + indexes for wiki knowledge search."""
import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
driver = GraphDatabase.driver(NEO4J_URI)

def run(q):
    with driver.session() as s: s.run(q)
    print(f"  OK: {q[:90]}")

print("=== Schema ===")
run("CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.id IS UNIQUE")
run("CREATE CONSTRAINT page_path IF NOT EXISTS FOR (p:Page) REQUIRE (p.repo, p.path) IS UNIQUE")
run("CREATE RANGE INDEX page_tags IF NOT EXISTS FOR (p:Page) ON (p.tags)")
run("CREATE RANGE INDEX page_repo IF NOT EXISTS FOR (p:Page) ON (p.repo)")
run("CREATE RANGE INDEX page_updated IF NOT EXISTS FOR (p:Page) ON (p.updated)")
try:
    run('CREATE VECTOR INDEX page_emb IF NOT EXISTS FOR (p:Page) ON (p.embedding) '
        'OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: "cosine"}}')
except Exception as e:
    print(f"  ! Vector index: {e}")

print("\n=== Verify ===")
with driver.session() as s:
    for r in s.run("SHOW CONSTRAINTS"): print(f"  {r['name']} ({r['type']})")
    for r in s.run("SHOW RANGE INDEXES"): print(f"  {r['name']}")
    for r in s.run("SHOW VECTOR INDEXES"): print(f"  VECTOR: {r['name']} state={r.get('state')}")
driver.close()
print("Done.")
