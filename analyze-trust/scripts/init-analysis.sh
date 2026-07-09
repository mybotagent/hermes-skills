#!/usr/bin/env bash
# init-analysis.sh — Bootstrap a new analyze-trust project
# Usage: ./init-analysis.sh <project_name> <goal_slug>

set -euo pipefail

PROJECT="${1:?Usage: $0 <project_name> <goal_slug>}"
GOAL_SLUG="${2:?Usage: $0 <project_name> <goal_slug>}"

ROOT="$HOME/workspace/$PROJECT"
DATE="$(date +%Y%m%d)"

mkdir -p "$ROOT"/{docs/{plans,reports,charts},scratch,data/{raw,processed}}

# Copy template files for each stage
TPL="$HOME/.hermes/skills/analyze-trust/references"
cp "$TPL/pipeline-template.md" "$ROOT/docs/plans/${GOAL_SLUG}.md.tpl"

# Create empty scratch files for the 9 stages
for f in env kaggle-discover hypothesis-eda analysis-cycle \
         trust-metrics-llm trust-metrics-code qa-review \
         head-of-data-decision verify-report; do
    touch "$ROOT/scratch/$f.md"
done

# Initialize README
cat > "$ROOT/README.md" << EOF
# $PROJECT

**Goal**: <fill in>
**Date**: $DATE

## Pipeline status
- [ ] Stage 1: define-analysis → docs/plans/$GOAL_SLUG.md
- [ ] Stage 2: kaggle-discover → scratch/kaggle-discover.md
- [ ] Stage 3: local-setup → data/raw/
- [ ] Stage 4: hypothesis-eda → scratch/hypothesis-eda.md
- [ ] Stage 5: analysis-cycle → scratch/analysis-cycle.md
- [ ] Stage 6: verify-report → docs/reports/${DATE}-${GOAL_SLUG}.{md,ipynb}
- [ ] Stage 7: trust-metrics → scratch/trust-metrics-{llm,code}.md
- [ ] Stage 8: qa-review → scratch/qa-review.md
- [ ] Stage 9: head-of-data → scratch/head-of-data-decision.md

## Iron Laws
1. ✅ plan approved before execution
2. ✅ env selected before execution
3. ✅ stdout evidence for every claim
4. ✅ conclusions from data only
5. ✅ loop state updated each iter
6. ✅ stages 7-9 read-only
7. ✅ PUBLISH gate complete

## Reference
- ~/.hermes/skills/analyze-trust/SKILL.md
EOF

# Initialize git
cd "$ROOT"
git init
git add .
git commit -m "Initial scaffold for $PROJECT"

echo "✅ Project bootstrapped: $ROOT"
echo "📋 Next: fill in docs/plans/$GOAL_SLUG.md (Stage 1)"
echo "📁 Tree:"
find "$ROOT" -type f | sort