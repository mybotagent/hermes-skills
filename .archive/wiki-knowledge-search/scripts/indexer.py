#!/usr/bin/env python3
"""
Wiki → Neo4j Indexer
Scans hermes-wiki-super submodules (Karpathy LLM Wiki pattern),
extracts frontmatter + wikilinks, MERGEs into Neo4j.

Usage:
  source ~/.venv-neo4j/bin/activate
  python3 indexer.py                           # all repos
  python3 indexer.py --repo hermes-wiki         # single repo
  python3 indexer.py --dry-run                  # no writes
"""
import os, re, sys, json, argparse
from pathlib import Path
from datetime import date
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
WIKI_SUPER = os.path.expanduser("~/hermes-wiki-super")

NAMESPACES = {
    "hermes-wiki": "hw", "trade-pipeline": "tp",
    "hermes-wiki-claude-code": "cc", "hermes-wiki-codex": "cx",
    "harness-engineering-wiki": "he", "subagents-library": "sl",
    "hermes-logs": "hl",
}

def find_md_files(repo_path):
    pages = []
    for f in Path(repo_path).rglob("*.md"):
        parts = f.relative_to(repo_path).parts
        if any(p.startswith(".") for p in parts): continue
        if parts[0] in ("logs", "raw", ".git"): continue
        pages.append(f)
    return pages

def parse_fm(content):
    fm, body = {}, content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if v.startswith("[") and v.endswith("]"):
                        v = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",")]
                    fm[k] = v
            body = parts[2]
    return fm, body

def extract_wikilinks(body):
    return re.findall(r'\[\[([^\]]+)\]\]', body)

def get_title(f, fm):
    return fm.get("title", f.stem.replace("-", " ").title())

def get_summary(body, max_l=200):
    for line in body.split("\n"):
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("---") and len(s) > 30:
            return s[:max_l]
    return ""

def get_tags(fm):
    t = fm.get("tags", fm.get("tag", []))
    return t if isinstance(t, list) else [t]

def get_related(fm):
    r = fm.get("related", [])
    return r if isinstance(r, list) else [r]

def scan_repo(repo_name, repo_path, dry_run=False):
    ns = NAMESPACES.get(repo_name, repo_name[:2])
    md_files = find_md_files(repo_path)

    pages, links, refs = [], [], []
    path_to_id = {}

    for f in md_files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        fm, body = parse_fm(content)
        rel_path = str(f.relative_to(repo_path))
        page_id = f"{ns}:{rel_path.replace('/', ':').replace('.md', '')}"
        path_to_id[rel_path] = page_id

        pages.append({
            "id": page_id, "repo": repo_name, "path": rel_path,
            "title": get_title(f, fm), "tags": get_tags(fm),
            "summary": get_summary(body),
            "updated": fm.get("updated", fm.get("created", str(date.today()))),
            "confidence": fm.get("confidence", "medium"),
        })

        for r in get_related(fm):
            rid = f"{ns}:{r.replace('.md', '').replace('/', ':')}"
            refs.append((page_id, rid, "related"))

    for f in md_files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        fm, body = parse_fm(content)
        rel_path = str(f.relative_to(repo_path))
        from_id = path_to_id[rel_path]

        for wl in extract_wikilinks(body):
            wl_clean = wl.split("|")[0]
            wl_id = f"{ns}:{wl_clean.replace('/', ':')}"
            if wl_id not in path_to_id.values():
                for pns, prefix in NAMESPACES.items():
                    alt = f"{prefix}:{wl_clean.replace('/', ':')}"
                    if alt in path_to_id.values():
                        wl_id = alt; break
            links.append((from_id, wl_id, "wikilink"))

    if not dry_run and pages:
        write_to_neo4j(pages, links, refs)

    return pages, links, refs

def write_to_neo4j(pages, links, refs):
    driver = GraphDatabase.driver(NEO4J_URI)
    with driver.session() as sess:
        for p in pages:
            sess.run("""MERGE (n:Page {id: $id})
                SET n.repo = $repo, n.path = $path, n.title = $title,
                    n.tags = $tags, n.summary = $summary,
                    n.updated = $updated, n.confidence = $confidence""", p)
        for from_id, to_id, ltype in links + refs:
            try:
                sess.run("""MATCH (a:Page {id: $f}), (b:Page {id: $t})
                    MERGE (a)-[r:LINKS {type: $typ}]->(b)""",
                    {"f": from_id, "t": to_id, "typ": ltype})
            except Exception:
                pass
    driver.close()

def get_all_repos(base):
    repos = {}
    for item in Path(base).iterdir():
        if not item.is_dir() or item.name.startswith("."): continue
        if (item / ".git").exists() or (item / "index.md").exists():
            repos[item.name] = item
    # Level 2: wiki/ subdirectory
    if (Path(base) / "wiki").exists():
        for sub in (Path(base) / "wiki").iterdir():
            if sub.is_dir() and ((sub / ".git").exists() or (sub / "index.md").exists()):
                repos[sub.name] = sub
    return repos

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", help="Single repo only")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repos = get_all_repos(WIKI_SUPER)
    total = {"pages": 0, "links": 0, "refs": 0}

    for name, path in sorted(repos.items()):
        if args.repo and name != args.repo: continue
        p, l, r = scan_repo(name, path, args.dry_run)
        total["pages"] += len(p); total["links"] += len(l); total["refs"] += len(r)

    print(f"Repos: {len(repos)}, Pages: {total['pages']}, "
          f"Wikilinks: {total['links']}, Related: {total['refs']}")
    if args.dry_run: print("(dry run)")

if __name__ == "__main__":
    main()
