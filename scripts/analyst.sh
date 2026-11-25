#!/usr/bin/env bash
set -euo pipefail

URL="${URL:-http://localhost:8003/reports/low-stock-paid-orders}"
INTERVAL="${INTERVAL:-2}"
GREEN=$'\033[32m'; RED=$'\033[31m'; RESET=$'\033[0m'
ok=0; fail=0; body=""

num() { grep -o "\"$1\":[0-9]*" <<<"$body" | head -1 | cut -d: -f2 || true; }
str() { grep -o "\"$1\":\"[^\"]*\"" <<<"$body" | head -1 | cut -d'"' -f4 || true; }

trap 'echo; echo "ringkasan: OK=$ok GAGAL=$fail"; exit 0' INT

echo "analyst: GET $URL tiap ${INTERVAL}s (Ctrl+C untuk berhenti)"
while true; do
  now=$(date +%H:%M:%S)
  resp=$(curl -s -m 15 -w $'\n%{http_code}' "$URL" || true)
  code=${resp##*$'\n'}
  body=${resp%$'\n'*}
  if [ "$code" = "200" ]; then
    ok=$((ok + 1))
    src=$(grep -o '"sources":\[[^]]*\]' <<<"$body" | sed 's/.*\[//; s/\].*//; s/"//g; s/,/, /g' || true)
    ids=$(grep -o '"order_id":[0-9]*' <<<"$body" | cut -d: -f2 | paste -sd, - || true)
    echo "$now  ${GREEN}OK   ${RESET}  $(num row_count) baris  $(num elapsed_ms) ms  [$src]  order: ${ids:--}"
  else
    fail=$((fail + 1))
    err=$(str error); who=$(str source)
    echo "$now  ${RED}GAGAL${RESET}  ${err:-federation_unreachable}  sumber: ${who:-tidak diketahui}  (HTTP $code, tanpa hasil parsial)"
  fi
  sleep "$INTERVAL"
done