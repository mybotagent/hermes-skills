# Cron Job Output Inspection

Check whether a cron script saves intermediate files or only prints to stdout.

## Quick Checks

```bash
# Check if script writes any files
grep -n '\.write\|\.dump\|open(' /path/to/script.py

# Check if script only prints
grep -n 'print(' /path/to/script.py | tail -10

# Check JSON-specific output
grep -n 'json\.dump\|json\.dumps' /path/to/script.py

# Check Hermes cron configuration
hermes cron list
```

## Common Patterns Found

| Pattern | Means | Action Needed |
|---------|-------|---------------|
| `print(json.dumps(...))` | JSON printed to stdout only | Capture via subprocess |
| `print(f"...")` table output | Text table, not machine-readable | Parse with regex |
| `with open(...) as f:` | File is saved | Just read the file |
| Only prints + Discord delivery | No persistence at all | Must add capture layer |

## Real-World Example (from trading-agents-nuri)

```bash
# fair_value_v3.py — has NO file writes, only print()
grep -n 'open\|json.dump' ~/.hermes/scripts/fair_value_v3.py
# Output: (nothing) ← no files saved!

grep -n 'print(' ~/.hermes/scripts/fair_value_v3.py
# Output: 25+ print() calls ← stdout only

# analyst_target_collector.py — JSON to stdout, no file
grep -n 'json.dump\|open' ~/.hermes/scripts/analyst_target_collector.py
# Output: only json.dumps() → stdout, not json.dump() → file
```
