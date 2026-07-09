# Gateway ImportError Recovery — Diagnostic Recipe

Full incident writeup (2026-07-03): `wiki/infra/discord-gateway.md` Troubleshooting
section. This reference captures the **diagnostic procedure** and **distinguishing
table** so the next session doesn't rediscover the pattern from scratch.

## The signature symptom

- All platforms report `✓ <platform> connected` in `~/.hermes/logs/gateway.log`
- Every inbound message gets a short error reply (`Sorry, I encountered an error (ImportError)`)
- Stack trace ends with:
  ```
  File ".../run_agent.py", line N, in <module>
      from tools.terminal_tool import cleanup_vm
    File ".../tools/terminal_tool.py", line N, in <module>
      from tools.tool_backend_helpers import (...)
  ImportError: cannot import name '<X>' from 'tools.<module>'
  ```
- The named module **exists** and the named symbol **exists** in
  `~/.hermes/hermes-agent/tools/<module>.py`
- `python -c "from tools.<module> import <X>"` from a fresh shell **succeeds**

That combination — main process OK, subprocess fails, CLI succeeds — is the
fingerprint. If two of those three are present, suspect this bug.

## Why the contradiction happens

```
                       ┌─────────────────────────┐
                       │  hermes-gateway.service │
                       │  (long-lived process)   │
                       │                         │
                       │  sys.modules =          │
                       │   { tools.X: <good> }   │  ← imported cleanly at startup
                       │                         │
                       └────────┬────────────────┘
                                │ per inbound message:
                                ▼
                       ┌─────────────────────────┐
                       │  run_agent subprocess    │
                       │  (fresh Python)          │
                       │                         │
                       │  sys.modules = {}        │  ← starts clean
                       │  then re-imports run_   │
                       │  agent → tools.X        │
                       │  → reads __pycache__/   │
                       │  → finds stale .pyc     │  ← loads bad partial
                       └─────────────────────────┘
```

CLI from your shell is a **third** Python process — also fresh, but you didn't
edit `tools/` between CLI invocation and gateway restart, so `.pyc` happens to
match `.py` and you get the good path. The gateway subprocess is the same shape
in theory, but the `.pyc` was written by an earlier partial update and never
re-validated because the gateway was never restarted.

## Diagnostic steps

```bash
# 1. Confirm symptom shape
grep -c "ImportError" ~/.hermes/logs/gateway.log

# 2. Identify the failing module + symbol from the traceback
#    (look at the last `from tools.<M> import <X>` line in the trace)

# 3. Confirm the symbol exists in the .py file
grep -n "def <X>\|^<X> " ~/.hermes/hermes-agent/tools/<M>.py

# 4. Check .pyc mtime vs .py mtime — stale evidence
ls -la ~/.hermes/hermes-agent/tools/__pycache__/<M>.cpython-311.pyc \
       ~/.hermes/hermes-agent/tools/<M>.py
# If .pyc is OLDER than .py → stale (Python SHOULD have invalidated but the
#   byte-compile raced during hermes update)
# If .pyc is NEWER than .py → worse — partial compile or hand-written bytecode

# 5. Walk the actual import chain the gateway walks (NOT just one import)
cd ~/.hermes/hermes-agent && ./venv/bin/python -c "
from tools.<M> import <X>
from tools.terminal_tool import cleanup_vm
import run_agent
print('OK')
"
```

If step 3 finds the symbol but step 5 fails → you have this bug.

## Fix (verified sequence)

```bash
# Pick the failing module(s) from the traceback + anything in the same
# import chain (terminal_tool + tool_backend_helpers in the 2026-07-03 incident)
rm ~/.hermes/hermes-agent/tools/__pycache__/<module1>.cpython-311.pyc
rm ~/.hermes/hermes-agent/tools/__pycache__/<module2>.cpython-311.pyc

# Restart clears sys.modules in the long-lived process
hermes gateway restart

# Verify end-to-end
tail -20 ~/.hermes/logs/gateway.log
# Expect: "✓ discord connected" (or whichever platform) + zero ImportError lines
# Then send one test message from the messaging platform
```

## Distinguishing from other ImportErrors

| Pattern | Likely cause | Fix |
|---------|--------------|-----|
| `cannot import name '<X>' from 'tools.<M>'` on a known-good file | **This bug** | rm `.pyc` + restart |
| Symbol genuinely missing from file | Stale `.py` checked in, deleted function, refactor regression | Restore from git or fix refactor |
| `ModuleNotFoundError: No module named 'X'` (different from import name) | Missing dep, broken venv, wrong PYTHONPATH | `hermes doctor --fix`; reinstall |
| `ImportError: cannot import name 'X' from 'utils'` (or other lib, not `tools`) | Library version mismatch | `pip install <lib>==<version>` or `hermes update` |
| Cyclic import (`circular import` in traceback) | Two modules importing each other | Code fix |
| `ImportError: attempted relative import with no known parent package` | Bad relative-import depth, file moved into wrong dir | Restore directory structure |

## When this will recur

- `hermes update` that lands new code without full process restart
- Manual `git pull` in `~/.hermes/hermes-agent/` followed by partial `uv pip install -e .`
- Hot-reload attempts that touch `tools/` while the gateway is running
- Profile clone from older hermes install onto newer source tree
- Running tests that mutate `tools/` then exit, leaving `.pyc` mid-state

## Reference transcript (2026-07-03, abbreviated)

```
inbound message: platform=discord user=aiprofit chat=1522201680584638474 msg='아ㄴ녕'
ERROR gateway.run: Agent error in session ...
  File ".../gateway/run.py", line 14557, in _run_agent
  File ".../run_agent.py", line 142, in <module>
      from tools.terminal_tool import cleanup_vm
  File ".../tools/terminal_tool.py", line 70, in <module>
      from tools.tool_backend_helpers import (
ImportError: cannot import name 'nous_tool_gateway_unavailable_message'
from 'tools.tool_backend_helpers'
```

Resolution took 3 minutes:
1. Confirmed `tools/tool_backend_helpers.py` line 44 had the function (`grep -n`)
2. Confirmed direct CLI import succeeded (`python -c "from tools.tool_backend_helpers import nous_tool_gateway_unavailable_message"` → exit 0)
3. Found stale `.pyc` via `ls -la __pycache__/`
4. Removed two `.pyc` files (failing module + its import chain member)
5. `hermes gateway restart` (PID 1308 → 5502)
6. Smoke-tested import chain including `run_agent` → OK
7. Logged recovery in `wiki/logs/2026/2026-07-03-0025.md`

## Related

- SKILL.md inline troubleshooting: search for "Stale `.pyc` → ImportError"
- Wiki: `wiki/infra/discord-gateway.md` (Troubleshooting section)
- Wiki log: `wiki/logs/2026/2026-07-03-0025.md`
- Memory pointer: short entry referencing this skill file