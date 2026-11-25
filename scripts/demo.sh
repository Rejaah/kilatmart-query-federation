#!/usr/bin/env bash
set -euo pipefail

REPORT="${REPORT:-http://localhost:8003/reports/low-stock-paid-orders}"
STOCK="${STOCK:-http://localhost:8002/stock}"
SKU="${SKU:-SKU-001}"

# apa pun yang terjadi, stock-db harus hidup lagi saat skrip berakhir
cleanup() {
  docker compose unpause stock-db >/dev/null 2>&1 || true
  docker compose start stock-db >/dev/null 2>&1 || true
}
trap cleanup EXIT

orders() {
  local ids
  ids=$(curl -s -m 20 "$REPORT" | grep -o '"order_id":[0-9]*' | cut -d: -f2 | paste -sd, - || true)
  echo "${ids:-gagal, tanpa hasil}"
}

set_qty() {
  echo "\$ PUT $STOCK/$SKU  qty_on_hand=$1"
  curl -s -X PUT "$STOCK/$SKU" -H 'content-type: application/json' -d "{\"qty_on_hand\":$1}" >/dev/null
}

step() {
  echo
  read -r -p "[Enter] $1 " _
}

orig=$(curl -s "$STOCK" | grep -o "\"sku\":\"$SKU\"[^}]*" | grep -o '"qty_on_hand":[0-9]*' | cut -d: -f2)

echo "== Demo KilatMart. Buka http://localhost:8003/ di browser dan biarkan terbuka."
echo "   order di laporan sekarang: $(orders)"

step "1/3 SEGAR: turunkan stok $SKU ke 2 lewat inventory-api"
set_qty 2
echo "   lihat browser: order baru muncul di pembaruan berikutnya, tanpa sinkronisasi"

step "kembalikan stok $SKU ke $orig"
set_qty "$orig"
echo "   lihat browser: order itu keluar lagi"

step "2/3 GAGAL: matikan stock-db"
echo "\$ docker compose stop stock-db"
docker compose stop stock-db
echo "   lihat browser (sekitar 5 detik): GAGAL, sumber stock-db, tanpa hasil sebagian"

step "3/3 PULIH: nyalakan stock-db lagi (federation tidak di-restart)"
echo "\$ docker compose start stock-db"
docker compose start stock-db
start=$(date +%s)
until [ "$(curl -s -m 10 -o /dev/null -w '%{http_code}' "$REPORT" || true)" = "200" ]; do
  if [ $(( $(date +%s) - start )) -ge 60 ]; then
    echo "GAGAL: belum pulih setelah 60 detik"
    exit 1
  fi
  sleep 1
done
echo "   pulih setelah sekitar $(( $(date +%s) - start )) detik. order di laporan: $(orders)"
echo
echo "== selesai"
