#!/usr/bin/env bash
set -euo pipefail

REPORT="${REPORT:-http://localhost:8003/reports/low-stock-paid-orders}"
STOCK="${STOCK:-http://localhost:8002/stock}"
SKU="${SKU:-SKU-001}"
PAUSE="${PAUSE:-5}"

orders() { curl -s "$REPORT" | grep -o '"order_id":[0-9]*' | cut -d: -f2 | paste -sd, - || true; }

set_qty() {
  echo "\$ PUT $STOCK/$SKU  qty_on_hand=$1"
  curl -s -X PUT "$STOCK/$SKU" -H 'content-type: application/json' -d "{\"qty_on_hand\":$1}" >/dev/null
}

orig=$(curl -s "$STOCK" | grep -o "\"sku\":\"$SKU\"[^}]*" | grep -o '"qty_on_hand":[0-9]*' | cut -d: -f2)

echo "== 1. sebelum: stok $SKU = $orig"
before=$(orders); echo "   order di laporan: $before"

echo "== 2. turunkan stok $SKU ke 2 lewat inventory-api"
set_qty 2
after=$(orders); echo "   order di laporan: $after"

echo "   (jeda ${PAUSE}s agar jendela analis sempat menampilkan perubahan)"
sleep "$PAUSE"

echo "== 3. kembalikan stok $SKU ke $orig"
set_qty "$orig"
restored=$(orders); echo "   order di laporan: $restored"

echo "== ringkasan: sebelum=[$before] sesudah=[$after] pulih=[$restored]"
if [ "$before" = "$after" ]; then
  echo "GAGAL: laporan tidak berubah setelah stok diubah"
  exit 1
fi
echo "OK: laporan berubah segera setelah sumber berubah, tanpa sinkronisasi"