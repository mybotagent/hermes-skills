#!/usr/bin/env bash
# Analyst Target 수집 + 검증 + 밸류에이션 전체 파이프라인
# 크론에서 매일 실행하는 순서 (참고용 — 실제 실행은 cron prompt terminal 명령어)
# 통합 레포: ~/trade-pipeline/langgraph/src/

echo "========================================"
echo " STEP 1: Analyst Target 수집 + 검증"
echo "========================================"
cd ~/trade-pipeline && python3 langgraph/src/analyst_target_collector.py

echo ""
echo "========================================"
echo " STEP 2: 밸류에이션 분석"
echo "========================================"
cd ~/trade-pipeline && python3 langgraph/src/fair_value.py

echo ""
echo "✅ 파이프라인 완료"
