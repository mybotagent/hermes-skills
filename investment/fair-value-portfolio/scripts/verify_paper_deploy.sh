#!/usr/bin/env bash
# verify_paper_deploy.sh — hermes-paper-portfolio 라이브 배포 검증 프로브
#
# 용도: push 후 "따라갔나"를 눈으로 믿지 않고 기계적으로 확인한다.
#   - 사이트 응답
#   - 매크로 플롯 N개 실경로 접근 + 바이트 크기 (0바이트면 실패)
#   - index.html에 plot 참조가 실렸는지
#   - macro_dashboard_data.json / portfolio_target.json 값 확인
#
# 사용:
#   bash verify_paper_deploy.sh [base_url]
#   BASE=https://hermes-paper-portfolio.vercel.app bash verify_paper_deploy.sh
#
# 종료코드: 0 = 전부 통과, 1 = 실패 항목 있음

set -uo pipefail

BASE="${1:-${BASE:-https://hermes-paper-portfolio.vercel.app}}"
FAIL=0

pass() { echo "  ✅ $1"; }
fail() { echo "  ❌ $1"; FAIL=1; }

echo "=== Paper Portfolio 배포 검증: $BASE ==="

# 1) 사이트 응답
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/")
if [ "$code" = "200" ]; then pass "사이트 HTTP 200"; else fail "사이트 HTTP $code"; fi

# 2) 매크로 플롯 — index.html이 참조하는 것만 뽑아서 실제 접근
echo ""
echo "── 매크로 플롯 접근 ──"
plots=$(curl -s "$BASE/" | grep -o 'macro_plots/plot_[0-9]*\.png' | sort -u)
if [ -z "$plots" ]; then
  fail "index.html에서 plot 참조를 찾지 못함 (대시보드가 구버전)"
else
  for p in $plots; do
    read -r sc sz < <(curl -s -o /dev/null -w "%{http_code} %{size_download}" "$BASE/$p")
    if [ "$sc" = "200" ] && [ "$sz" -gt 1000 ]; then
      pass "$p HTTP $sc (${sz} bytes)"
    else
      fail "$p HTTP $sc (${sz} bytes) — 0바이트/오류면 배포 미완료"
    fi
  done
fi

# 3) 데이터 JSON 값 확인
echo ""
echo "── 데이터 JSON ──"
mj=$(curl -s "$BASE/macro_dashboard_data.json")
if echo "$mj" | grep -q '"unrate"'; then
  pass "macro_dashboard_data.json에 unrate 존재"
  echo "$mj" | grep -oE '"(sahm_rule|unrate|unrate_3m_chg)":[^,}]*' | sed 's/^/     /'
else
  fail "macro_dashboard_data.json에 unrate 없음 (지표 미반영)"
fi

# 4) portfolio_target.json — 종목 배열 키가 'stocks'가 아니라 'target_allocation'
echo ""
echo "── portfolio_target.json ──"
pt=$(curl -s "$BASE/portfolio_target.json")
if echo "$pt" | grep -q '"target_allocation"'; then
  n=$(echo "$pt" | grep -c '"asset"')
  pass "target_allocation 존재 (항목 $n개)"
  echo "$pt" | grep -oE '"asset": *"[^"]*"' | sed 's/^/     /'
  # KR 국내상장주 유입 검사
  if echo "$pt" | grep -qE '"name": *"(삼성전자|SK하이닉스|LG이노텍|KakaoBank|카카오뱅크)"'; then
    fail "KR 종목이 목표 비중에 남아있음"
  else
    pass "KR 종목 없음"
  fi
else
  fail "target_allocation 키 없음 — 배열 키 확인 필요 (stocks로 착각하지 말 것)"
fi

echo ""
if [ "$FAIL" = "0" ]; then
  echo "=== ✅ 전체 통과 ==="
else
  echo "=== ⚠️ 실패 항목 있음 ==="
fi
exit $FAIL
