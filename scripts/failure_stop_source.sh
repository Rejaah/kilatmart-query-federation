#!/usr/bin/env bash
set -euo pipefail

REPORT="${REPORT:-http://localhost:8003/reports/low-stock-paid-orders}"
STOCK="${STOCK:-http://localhost:8002/stock}"
SKU="${SKU:-SKU-001}"

# cetak kode HTTP, waktu respons, dan awal isi
probe() {
  local resp meta body
  resp=$(curl -s -m 20 -w $'\n%{http_code} %{time_total}' "$1" || true)
  meta=${resp##*$'\n'}
  body=${resp%$'\n'*}
  echo "   HTTP ${meta%% *}  ${meta##* }s  ${body:0:260}"
}

set_qty() {
  echo "\$ PUT $STOCK/$SKU  qty_on_hand=$1"
  curl -s -X PUT "$STOCK/$SKU" -H 'content-type: application/json' -d "{\"qty_on_hand\":$1}" >/dev/null
}

orig=$(curl -s "$STOCK" | grep -o "\"sku\":\"$SKU\"[^}]*" | grep -o '"qty_on_hand":[0-9]*' | cut -d: -f2)

echo "== 0. siapkan: stok $SKU = $orig, turunkan ke 2 sebagai penanda data"
set_qty 2
probe "$REPORT"

echo "== 1. \$ docker compose stop stock-db"
docker compose stop stock-db

echo "== 2. laporan saat stock-db mati (3 panggilan)"
probe "$REPORT"
probe "$REPORT"
probe "$REPORT"

echo "== 3. sisi orders-db tetap hidup: webshop-api"
echo "   GET /orders -> HTTP $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/orders), $(curl -s http://localhost:8001/orders | grep -o '"order_id"' | wc -l) order"

echo "== 4. \$ docker compose start stock-db"
docker compose start stock-db
start=$(date +%s)

echo "== 5. tunggu laporan kembali 200 (poll tiap 1 detik, maksimal 90 detik)"
until [ "$(curl -s -m 10 -o /dev/null -w '%{http_code}' "$REPORT" || true)" = "200" ]; do
  if [ $(( $(date +%s) - start )) -ge 90 ]; then
    echo "GAGAL: belum pulih setelah 90 detik"
    exit 1
  fi
  sleep 1
done
echo "   pulih setelah sekitar $(( $(date +%s) - start )) detik, tanpa restart federation"
probe "$REPORT"

echo "== 6. kembalikan stok $SKU ke $orig"
set_qty "$orig"
echo "== selesai"
