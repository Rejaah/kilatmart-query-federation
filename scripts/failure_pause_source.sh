#!/usr/bin/env bash
set -euo pipefail

REPORT="${REPORT:-http://localhost:8003/reports/low-stock-paid-orders}"
HEALTH="${HEALTH:-http://localhost:8003/health}"

# cetak kode HTTP, waktu respons, dan awal isi
probe() {
  local resp meta body
  resp=$(curl -s -m 20 -w $'\n%{http_code} %{time_total}' "$1" || true)
  meta=${resp##*$'\n'}
  body=${resp%$'\n'*}
  echo "   HTTP ${meta%% *}  ${meta##* }s  ${body:0:260}"
}

echo "== 0. baseline"
probe "$REPORT"

echo "== 1. \$ docker compose pause stock-db"
docker compose pause stock-db

echo "== 2. laporan saat stock-db di-pause (curl menunggu maksimal 20 detik)"
probe "$REPORT"
probe "$REPORT"

echo "== 3. federation tetap hidup saat satu laporan menggantung"
tmp=$(mktemp)
probe "$REPORT" >"$tmp" &
pid=$!
sleep 1
echo "   GET /health saat laporan menggantung:"
probe "$HEALTH"
wait "$pid"
echo "   laporan yang tadi menggantung:"
cat "$tmp"
rm -f "$tmp"

echo "== 4. \$ docker compose unpause stock-db"
docker compose unpause stock-db
start=$(date +%s)

echo "== 5. tunggu laporan kembali 200 (poll tiap 1 detik, maksimal 60 detik)"
until [ "$(curl -s -m 10 -o /dev/null -w '%{http_code}' "$REPORT" || true)" = "200" ]; do
  if [ $(( $(date +%s) - start )) -ge 60 ]; then
    echo "GAGAL: belum pulih setelah 60 detik"
    exit 1
  fi
  sleep 1
done
echo "   pulih setelah sekitar $(( $(date +%s) - start )) detik, tanpa restart federation"
probe "$REPORT"
echo "== selesai"
