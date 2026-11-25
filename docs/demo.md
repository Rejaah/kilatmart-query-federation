# Demo

## Mencoba sendiri

**Laporan.**

| Cara | Isi |
|---|---|
| http://localhost:8003/ | halaman analis: OK atau GAGAL, tabel, status tiap sumber |
| `curl -s localhost:8003/reports/low-stock-paid-orders` | JSON laporan |
| `curl -s localhost:8003/health/sources` | status `up`, `down`, atau `timeout` untuk tiap sumber |
| `curl -s localhost:8003/reports/low-stock-paid-orders/explain` | rencana eksekusi DuckDB: bagian query yang dikirim ke tiap sumber |

**Mengubah data sumber.** Turunkan stok SKU-001 ke 2:

```bash
curl -s -X PUT localhost:8002/stock/SKU-001 -H 'content-type: application/json' -d '{"qty_on_hand":2}'
```

Panggil laporan lagi: order paid milik SKU-001 (order 2) ikut muncul. Kembalikan dengan `qty_on_hand` 50. Alternatif tanpa `curl`: buka http://localhost:8002/docs, pilih `PUT /stock/{sku}`, lalu **Try it out**. Di PowerShell pakai `curl.exe` dan tulis tanda kutip JSON sebagai `\"`.

**Melihat query sampai ke sumber.**

```bash
docker compose logs -f orders-db                          # cari user=fed_ro
docker compose exec stock-db tail -f /tmp/general.log     # cari inventory.stock
```

Di log PostgreSQL, query `fed_ro` berisi `WHERE "status" = 'paid'` dan hanya kolom yang dibutuhkan. Bagian itu dikirim ke sumber, sedangkan perbandingan `qty_on_hand <= reorder_level` dihitung DuckDB (lihat endpoint `explain`).

## Demo 3 menit

Siapkan dengan `docker compose up -d --build --wait`, lalu susun layar tiga panel:

| Panel | Isi |
|---|---|
| Analis | browser di http://localhost:8003/ |
| Operator | terminal: `bash scripts/demo.sh` (tiap langkah menunggu Enter) |
| Log sumber | terminal: `docker compose logs -f --tail 0 orders-db` (cari `user=fed_ro`) |

| Waktu | Yang dilakukan |
|---|---|
| 0:00 - 0:40 | buka halaman analis (4 order), tunjukkan log: tiap pembaruan ada query `fed_ro` ke sumber |
| 0:40 - 1:30 | Enter pertama: stok diturunkan, order baru muncul. Enter kedua: stok kembali, order keluar |
| 1:30 - 2:30 | Enter ketiga: `stock-db` dimatikan, halaman GAGAL dengan nama sumber dan tanpa tabel (butuh sekitar 5 detik) |
| 2:30 - 3:00 | Enter keempat: `stock-db` dinyalakan, halaman kembali OK tanpa restart `federation` |

Alternatif: `bash scripts/analyst.sh` menampilkan hal yang sama di terminal, dan `bash scripts/demo_freshness.sh` menjalankan bagian kesegaran data saja tanpa menunggu Enter.

## Video cadangan

Jika demo langsung tidak dapat dijalankan, gunakan [walkthrough slide](demo-video.mp4). Video ini menampilkan alur query federation, perubahan data, respons saat sumber berhenti, dan batasan alat. Jalankan demo langsung untuk melihat respons layanan dan log database.
