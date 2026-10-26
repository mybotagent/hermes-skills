# Thread-Scoped Wiki Routing (for Multi-Context Agents)

> Extension of the Karpathy LLM Wiki pattern for agents operating across multiple
> conversation contexts (Discord threads, Telegram topics, cron jobs) where each
> context needs different knowledge scoped to it.
>
> Origin: aiprofit's Hermes Agent setup with Discord threads for schedule management,
> portfolio analysis, and automated cron reporting.

## The Problem

A single wiki directory serves all conversations.
When the agent operates across multiple Discord threads, each thread needs
relevant knowledge — but the agent has no built-in mechanism to scope
knowledge per-thread.

Previous attempt: separate GitHub repos per thread. These failed because:
- No integration — Hermes Agent only loads from the wiki directory
- No routing mechanism existed to map thread → repo
- The repos drifted stale and were never actually read

## The Solution: AGENTS.md Routing + Per-Thread Subdirectories

Instead of separate repos, organize thread-specific knowledge as subdirectories
within the single wiki, and write routing rules in AGENTS.md / SCHEMA.md.

### Structure

```
wiki/
├── AGENTS.md              ← Schema + Thread Routing rules (THE KEY)
├── index.md               ← Master catalog, includes thread routing table
├── analysis/              ← Shared knowledge (all threads can access)
├── infra/                 ← Shared infrastructure docs
├── watchlist/             ← Shared reference data
├── code/                  ← Shared script documentation
└── threads/               ← Per-thread knowledge (routed)
    ├── schedule/          ← Schedule management thread
    │   └── index.md       ← Calendar config, cron schedule, recurring events
    ├── portfolio/         ← Portfolio/stock analysis thread
    │   └── index.md       ← Ticker list, valuation methods, market context
    └── cron/              ← Cron job context (no user thread)
        └── index.md       ← Report format specs, delivery rules
```

### AGENTS.md Routing Rules

Add this section to AGENTS.md / SCHEMA.md:

```markdown
## Thread Routing

The agent MUST determine its current conversation context before loading
thread-specific knowledge.

### Detection
1. Read MEMORY entry matching `"This Discord thread (...)"` to get the
   platform, channel, and thread ID of the current session.
2. If no thread ID is found (cron job, CLI session), fall back to `threads/cron/`.

### Mapping
- `<channel-name>` (thread: <ID>) → `threads/<topic>/`
- Cron jobs → `threads/cron/`

### Loading Order
1. Read AGENTS.md → determine current thread
2. Read index.md → full catalog
3. Read threads/<context>/index.md → context-specific knowledge
4. THEN read any additional pages needed

Shared knowledge (analysis/, infra/, watchlist/) is always available
to all contexts — only the thread subdirectory changes.
```

### Memory Entries

Each session must know which thread it's in. Save to memory when
a new thread is set up:

```
This Discord thread (<channel> / <topic>, thread: <ID>)
is aiprofit's dedicated <purpose> thread.
```

The agent reads this on every turn to determine thread routing.

## Adding a New Thread

1. Create `threads/<name>/index.md` with topic-specific knowledge
2. Add the mapping line to AGENTS.md Thread Routing section
3. Add the thread to index.md's thread routing table
4. Save a memory entry with the thread ID
5. Log the change

## No-Thread Contexts (Cron Jobs)

Cron jobs run without a user-present session — they have no thread ID.
Create a `threads/cron/` directory with knowledge for automated tasks:
- Report format specs: what each cron job should produce
- Delivery rules: where reports go
- Error handling: what to do when data fails to load

## Pitfalls

- **AGENTS.md is the single source of truth** — if routing rules drift from
  memory entries, the agent loads the wrong context. Keep them in sync.
- **Don't create separate repos** — they won't be loaded by the agent.
  Use subdirectories within the single wiki.
- **Index.md must list all thread directories** — unlisted threads are invisible.
- **Thread index files should be self-contained** — reader should understand
  the thread's purpose from a single file.
- **Memory is the detection mechanism** — every session starts with memory
  loaded. If the thread ID isn't in memory, routing falls back to `threads/cron/`.
- **Name threads after their context, not their repo** — `threads/schedule/`
  not `threads/hermes-wiki-thread-schedule/`.
