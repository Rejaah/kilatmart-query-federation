# Panduan demonstrasi KilatMart

Jalankan perintah dari direktori utama repositori. Mulai layanan dan tunggu hingga siap.

```bash
docker compose up -d --build --wait
```

## Memeriksa laporan

| Akses | Informasi yang ditampilkan |
| --- | --- |
| <http://localhost:8003/> | Halaman analis dengan tabel pesanan, status laporan `OK` atau `GAGAL`, dan status tiap sumber. |
| `curl -s localhost:8003/reports/low-stock-paid-orders` | Hasil laporan dalam format JSON. |
| `curl -s localhost:8003/health/sources` | Status koneksi tiap sumber, yaitu `up`, `down`, atau `timeout`. |
| `curl -s localhost:8003/reports/low-stock-paid-orders/explain` | Rencana eksekusi DuckDB, termasuk pemindaian tabel sumber. |

### Perubahan stok

Dengan data awal, turunkan stok `SKU-001` dari 50 menjadi 2 melalui `inventory-api`.

```bash
curl -s -X PUT localhost:8002/stock/SKU-001 -H 'content-type: application/json' -d '{"qty_on_hand":2}'
```

Muat ulang laporan. Pesanan nomor 2 untuk `SKU-001` akan muncul karena jumlah stok memenuhi kondisi `qty_on_hand <= reorder_level`. Ulangi permintaan `PUT` dengan `{"qty_on_hand":50}` untuk memulihkan data awal. Jika data telah diubah sebelum demonstrasi, catat dan pulihkan nilai stok semula.

Permintaan yang sama dapat dikirim melalui <http://localhost:8002/docs>. Pilih `PUT /stock/{sku}`, klik **Try it out**, lalu masukkan SKU dan nilai stok. Untuk menjalankan contoh perintah di Windows, gunakan Git Bash atau WSL.

### Kueri pada basis data sumber

```bash
docker compose logs -f orders-db
docker compose exec stock-db tail -f /tmp/general.log
```

Di log PostgreSQL, cari kueri dari akun `fed_ro`. Kueri tersebut memilih kolom yang diperlukan dan memuat filter `WHERE "status" = 'paid'`. Di log MySQL, cari akses ke `inventory.stock`. Gunakan endpoint `explain` untuk melihat bahwa DuckDB mengevaluasi kondisi `qty_on_hand <= reorder_level` saat menyusun laporan.

## Urutan demonstrasi tiga menit

Buka halaman analis dan biarkan halaman memperbarui laporan secara berkala. Jalankan `bash scripts/demo.sh` di terminal operator. Di terminal lain, jalankan `docker compose logs -f --tail 0 orders-db` untuk menampilkan kueri yang masuk selama demonstrasi. Skrip menunggu tombol Enter sebelum setiap perubahan.

| Waktu | Tindakan dan hasil yang diamati |
| --- | --- |
| 0:00–0:40 | Tampilkan empat pesanan pada data awal. Saat halaman memperbarui laporan, tunjukkan kueri akun `fed_ro` pada log PostgreSQL. |
| 0:40–1:30 | Tekan Enter untuk menurunkan stok. Tunggu hingga pesanan nomor 2 muncul, lalu tekan Enter lagi untuk memulihkan stok dan amati pesanan itu keluar dari laporan. |
| 1:30–2:30 | Tekan Enter untuk menghentikan `stock-db`. Dalam kondisi uji, halaman beralih ke `GAGAL` setelah sekitar 5 detik, menyebut sumber yang bermasalah, dan mengosongkan tabel. |
| 2:30–3:00 | Tekan Enter untuk menyalakan kembali `stock-db`. Setelah koneksi pulih, laporan kembali berstatus `OK` tanpa memulai ulang `federation`. |

Gunakan `bash scripts/analyst.sh` untuk memantau laporan di terminal. Untuk memperagakan perubahan stok saja tanpa jeda interaktif, jalankan `bash scripts/demo_freshness.sh`.

## Video cadangan

Jika demonstrasi langsung tidak dapat dijalankan, gunakan [video penjelasan berbasis slide](demo-video.mp4). Video mencakup alur federasi kueri, perubahan stok, respons saat sumber berhenti, dan batasan prototipe.
