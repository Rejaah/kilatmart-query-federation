# KilatMart Query Federation

Satu query SQL menggabungkan tabel `orders` (PostgreSQL) dan `stock` (MySQL) lewat DuckDB, tanpa menyalin data. Pertanyaan yang dijawab: **order berstatus `paid` yang barangnya sudah di bawah batas reorder**.

Latihan kelompok IF4052 Service Computing. DuckDB membaca kedua sumber saat laporan diminta dan mengirim hasilnya langsung ke analis.

## Prasyarat

- Docker Engine atau Docker Desktop dengan perintah `docker compose`.
- Akses internet untuk build pertama agar Docker dapat mengambil image, paket Python, dan extension DuckDB.
- Bash dan `curl` untuk menjalankan perintah demo di bawah. Di Windows, gunakan Git Bash atau WSL.

## Mulai cepat

Jalankan dari root repo setelah layanan Federation digabungkan.

```bash
docker compose up --build -d --wait
docker compose ps
curl -fsS --retry 5 --retry-connrefused http://localhost:8003/reports/low-stock-paid-orders
```

Pada data awal, laporan mengembalikan `row_count` sebesar `4` dengan `order_id` 1, 3, 4, dan 10. Halaman analis tersedia di <http://localhost:8003/> setelah halaman tersebut digabungkan.

Untuk menguji database dan API sumber saat layanan Federation masih dikerjakan, jalankan `docker compose up --build -d --wait webshop-api inventory-api`. Kedua database akan ikut dimulai dan menunggu hingga tabel dari `init.sql` bisa dibaca.

Untuk mengembalikan data demo ke seed, jalankan `docker compose down --volumes`, lalu ulangi langkah mulai cepat. Opsi `--volumes` menghapus data database stack ini, termasuk perubahan selama demo.

## Demo singkat

1. Panggil laporan dari langkah mulai cepat. Federation menjalankan [satu query SQL](services/federation/queries/low_stock_paid_orders.sql) yang menggabungkan PostgreSQL dan MySQL.
2. Turunkan jumlah stok `SKU-001` dari 50 ke 2. Pemanggilan berikutnya langsung menampilkan order 2, sehingga jumlah baris menjadi 5. Kembalikan stok ke 50 untuk memulihkan hasil awal.

   ```bash
   curl -fsS -X PUT http://localhost:8002/stock/SKU-001 \
     -H 'Content-Type: application/json' -d '{"qty_on_hand":2}'
   curl -fsS http://localhost:8003/reports/low-stock-paid-orders
   curl -fsS -X PUT http://localhost:8002/stock/SKU-001 \
     -H 'Content-Type: application/json' -d '{"qty_on_hand":50}'
   ```

3. Hentikan MySQL dan panggil laporan lagi. Respons yang diharapkan adalah HTTP 503 dengan `error` bernilai `source_unavailable` dan `source` bernilai `stock-db`. Nyalakan kembali MySQL, tunggu hingga sehat, lalu cek bahwa laporan kembali menampilkan 4 baris.

   ```bash
   docker compose stop stock-db
   curl -isS http://localhost:8003/reports/low-stock-paid-orders
   docker compose up -d --wait stock-db
   curl -fsS http://localhost:8003/reports/low-stock-paid-orders
   ```

## Layanan

| Service | Alamat dari host | Fungsi |
| --- | --- | --- |
| `orders-db` | `127.0.0.1:5433` | PostgreSQL, menyimpan pesanan |
| `stock-db` | `127.0.0.1:3307` | MySQL, menyimpan stok |
| `webshop-api` | `http://localhost:8001` | Membaca, membuat, dan mengubah status pesanan |
| `inventory-api` | `http://localhost:8002` | Membaca dan mengubah stok |
| `federation` | `http://localhost:8003` | Menjalankan laporan DuckDB dan menyajikan hasil ke analis |

Di jaringan Compose, aplikasi memakai nama service dan port internal `5432` untuk PostgreSQL dan `3306` untuk MySQL. Port host hanya mendengarkan di loopback.

## Konfigurasi

Nilai demo ditetapkan di [`docker-compose.yml`](docker-compose.yml). Stack bisa dijalankan langsung tanpa membuat `.env`.

| Variabel | Nilai bawaan | Dipakai oleh |
| --- | --- | --- |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `shop`, `kilat`, `kilat_pw` | Inisialisasi PostgreSQL |
| `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` | `inventory`, `kilat`, `kilat_pw` | Inisialisasi MySQL |
| `MYSQL_ROOT_PASSWORD` | `root_pw` | Akun administrator MySQL |
| `ORDERS_DB_HOST`, `ORDERS_DB_PORT`, `ORDERS_DB_NAME` | `orders-db`, `5432`, `shop` | `webshop-api` dan `federation` |
| `STOCK_DB_HOST`, `STOCK_DB_PORT`, `STOCK_DB_NAME` | `stock-db`, `3306`, `inventory` | `inventory-api` dan `federation` |
| `APP_DB_USER`, `APP_DB_PASSWORD` | `kilat`, `kilat_pw` | Akun baca dan tulis kedua API sumber |
| `FED_DB_USER`, `FED_DB_PASSWORD` | `fed_ro`, `fed_ro_pw` | Akun baca-saja `federation`, dibuat oleh `init.sql` |
| `QUERY_TIMEOUT_S` | `5` | Batas waktu kueri di `federation` dalam detik |

## Dokumentasi dan log

Setelah pekerjaan role terkait digabungkan, `docs/architecture.md` memuat arsitektur, `docs/demo.md` memuat runbook demo, dan `docs/experiments.md` memuat eksperimen kegagalan.

Jalankan laporan lalu periksa log berikut untuk melihat aktivitas di kedua database. Pemeriksaan kesehatan database juga menghasilkan kueri di log.

```bash
docker compose logs --tail=50 orders-db
docker compose exec -T stock-db tail -n 50 /tmp/general.log
```

## Mengatasi masalah

| Gejala | Yang perlu dicek |
| --- | --- |
| `port is already allocated` | Pastikan port host 5433, 3307, dan 8001–8003 tersedia. |
| Build gagal saat menyiapkan Federation | Pastikan `services/federation/Dockerfile` sudah digabungkan dan build dapat mengakses internet. |
| Database belum `healthy` | Periksa `docker compose ps` dan `docker compose logs orders-db stock-db` untuk melihat kegagalan inisialisasi. |
| Laporan mengembalikan `503` atau `504` | Periksa sumber yang disebut di respons dan statusnya lewat `docker compose ps`. Jalankan kembali sumber jika berhenti. |
| Perubahan demo masih ada setelah restart | `stop` dan `start` mempertahankan data. Untuk kembali ke seed, gunakan perintah reset di bagian mulai cepat. |
