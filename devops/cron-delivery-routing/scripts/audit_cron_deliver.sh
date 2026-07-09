#!/usr/bin/env bash
# audit_cron_deliver.sh — list every active cron's deliver target with channel/topic heuristic
#
# Usage: bash audit_cron_deliver.sh
# Output: table with job_id, name, schedule, deliver target, and a topic-match warning
#
# Heuristic for this Discord:
#   thread 1510404235915694170 → stock/market topic
#   thread 1520640537995247698 → calendar/schedule topic
#   thread 1520255092413038732 → daily-survey topic
#   no thread → 404 (Mode A)
#
# Adjust THREAD_TOPICS and TOPIC_HINTS to your deployment.

set -euo pipefail

# ---- configuration (edit for your environment) ----
THREAD_TOPICS='
1510404235915694170|stock market — portfolio, screener, LangGraph reports
1520640537995247698|calendar — GCal events, reminders, schedules
1520255092413038732|daily-survey — clarify-based daily checklist
'

# Heuristic: if cron name contains any of these tokens, it's that topic
declare -A TOPIC_HINTS=(
  ["포트폴리오"]="stock"
  ["portfolio"]="stock"
  ["langgraph"]="stock"
  ["브리핑"]="stock"
  ["screener"]="stock"
  ["finviz"]="stock"
  ["매크로"]="stock"
  ["캘린더"]="calendar"
  ["calendar"]="calendar"
  ["일정"]="calendar"
  ["reminder"]="calendar"
  ["survey"]="survey"
  ["설문"]="survey"
)

# ---- run ----
echo "===== Cron Deliver Audit ====="
echo "Run timestamp: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo

RAW=$(hermes cron list 2>&1 || echo "ERROR: hermes cron list failed")

# Extract job block lines (job_id and the deliver line within ~10 lines)
echo "$RAW" | awk '
  /^[a-f0-9]{12} \[active\]/ { in_block=1; job_id=$1; print "---"; print "JOB: " job_id; print_job_id=1; next }
  /^[a-f0-9]{12} \[paused\]/ { in_block=1; job_id=$1; print "---"; print "JOB: " job_id "(paused)"; next }
  /Next run:/ { print; next }
  /Schedule:/ { print; next }
  /Deliver:/ { print; next }
  /^$/ { in_block=0 }
  /^  Name:/ { print; next }
'

echo
echo "===== Topic Match Warnings ====="

# Now do a smarter check using parse
echo "$RAW" | python3 - <<'PYEOF'
import re, subprocess, sys

raw = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True).stdout

# Match job blocks
blocks = re.split(r'\n(?=[a-f0-9]{12} \[)', raw)
TOPIC_MAP = {
    "1510404235915694170": "stock",
    "1520640537995247698": "calendar",
    "1520255092413038732": "survey",
}

HINTS = {
    "stock": ["포트폴리오", "portfolio", "langgraph", "브리핑", "screener", "finviz", "매크로"],
    "calendar": ["캘린더", "calendar", "일정", "reminder"],
    "survey": ["survey", "설문"],
}

warnings = 0
for block in blocks:
    job_m = re.search(r'^([a-f0-9]{12}) \[', block, re.M)
    if not job_m:
        continue
    job_id = job_m.group(1)
    name_m = re.search(r'^\s+Name:\s+(.+)$', block, re.M)
    name = name_m.group(1) if name_m else ""
    deliv_m = re.search(r'^\s+Deliver:\s+(\S+)', block, re.M)
    if not deliv_m:
        continue
    deliver = deliv_m.group(1)

    # Parse "discord:CHAT:THREAD" or "discord:CHAT"
    parts = deliver.split(":")
    if len(parts) < 3:
        print(f"⚠  {job_id} ({name[:40]}): NO THREAD (Mode A — will 404)  deliver={deliver}")
        warnings += 1
        continue

    thread = parts[2]
    target_topic = TOPIC_MAP.get(thread, f"UNKNOWN({thread})")

    # Infer intended topic from cron name
    intended_topic = None
    for topic, keywords in HINTS.items():
        if any(kw.lower() in name.lower() for kw in keywords):
            intended_topic = topic
            break

    if intended_topic and target_topic != "UNKNOWN" and intended_topic != target_topic:
        print(f"⚠  {job_id} ({name[:40]}): MISMATCH — cron looks like '{intended_topic}' but deliver topic is '{target_topic}'  thread={thread}")
        warnings += 1
    elif target_topic == "UNKNOWN":
        print(f"⚠  {job_id} ({name[:40]}): UNKNOWN THREAD ID {thread} — verify it's the right channel for this cron")
        warnings += 1
    else:
        print(f"✓  {job_id} ({name[:40]}): OK — {target_topic}  thread={thread}")

print()
print(f"Total warnings: {warnings}")
sys.exit(1 if warnings else 0)
PYEOF
