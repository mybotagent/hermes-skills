# Kanban DB Schema Reference (SQLite)

Source: `~/.hermes/kanban.db`

## Tables

### `tasks` — Main task storage
```sql
CREATE TABLE tasks (
    id                   TEXT PRIMARY KEY,
    title                TEXT NOT NULL,
    body                 TEXT,
    assignee             TEXT,
    status               TEXT NOT NULL,
    priority             INTEGER DEFAULT 0,
    created_by           TEXT,
    created_at           INTEGER NOT NULL,
    started_at           INTEGER,
    completed_at         INTEGER,
    workspace_kind       TEXT NOT NULL DEFAULT 'scratch',
    workspace_path       TEXT,
    claim_lock           TEXT,
    claim_expires        INTEGER,
    tenant               TEXT,
    result               TEXT,
    idempotency_key      TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    worker_pid           INTEGER,
    last_failure_error   TEXT,
    max_runtime_seconds  INTEGER,
    last_heartbeat_at    INTEGER,
    current_run_id       INTEGER,
    workflow_template_id TEXT,
    current_step_key     TEXT,
    skills               TEXT,
    max_retries          INTEGER,
    branch_name          TEXT,
    model_override       TEXT,
    session_id           TEXT
);
```

### `task_events` — Event log
```sql
CREATE TABLE task_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    TEXT NOT NULL,
    run_id     INTEGER,
    kind       TEXT NOT NULL,
    payload    TEXT,
    created_at INTEGER NOT NULL
);
```

### `task_comments` — Comments on tasks
```sql
CREATE TABLE task_comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    TEXT NOT NULL,
    author     TEXT,
    body       TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
```

### `task_links` — Parent-child dependencies
```sql
CREATE TABLE task_links (
    parent_id  TEXT NOT NULL,
    child_id   TEXT NOT NULL,
    PRIMARY KEY (parent_id, child_id)
);
```

### `task_runs` — Worker execution history
```sql
CREATE TABLE task_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT NOT NULL,
    profile     TEXT,
    status      TEXT NOT NULL,
    started_at  INTEGER,
    completed_at INTEGER,
    outcome     TEXT,
    summary     TEXT,
    error       TEXT
);
```

## Status Values
- `todo` — Created, waiting for dependencies
- `ready` — Ready to be claimed
- `in_progress` — Active worker claim
- `done` — Completed
- `blocked` — Waiting on external input
- `cancelled` — Abandoned

## Priority Values
`priority` INTEGER: 0 = highest, higher = lower priority.

## ID Format
Task IDs are prefixed `t_` + hex, e.g. `t_a1b2c3d4`.
