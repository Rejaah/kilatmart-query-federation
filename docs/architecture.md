# Arsitektur

## Gambaran

```
 Tim analytics
      │  http://localhost:8003/
      ▼
 ┌──────────────────────────────┐
 │ federation (DuckDB, :8003)   │   tidak menyimpan data,
 └───────┬──────────────┬───────┘   koneksi dibuka per request
         │ ATTACH       │ ATTACH
         │ postgres     │ mysql
         │ READ_ONLY    │ READ_ONLY
         ▼              ▼
 ┌───────────────┐ ┌───────────────┐
 │ orders-db     │ │ stock-db      │
 │ PostgreSQL    │ │ MySQL         │
 └───────▲───────┘ └───────▲───────┘
         │ tulis           │ tulis
 ┌───────┴───────┐ ┌───────┴───────┐
 │ webshop-api   │ │ inventory-api │
 │ :8001         │ │ :8002         │
 └───────────────┘ └───────────────┘
```

`federation` hanya membaca: user database `fed_ro` hanya punya `SELECT`, dan `ATTACH` memakai `READ_ONLY`. Data sumber hanya berubah lewat `webshop-api` dan `inventory-api`.

## Cara kerja `federation`

- Setiap request membuka koneksi DuckDB baru, `ATTACH` kedua sumber, menjalankan `queries/low_stock_paid_orders.sql`, lalu menutup koneksi. Sumber yang mati lalu menyala langsung terpakai tanpa restart.
- Extension `postgres` dan `mysql` dipasang saat build image, jadi demo tidak butuh internet.
- Tiap sumber di-`ATTACH` di blok terpisah, sehingga error menyebut sumber yang bermasalah.
- Query berjalan di thread dengan batas waktu `QUERY_TIMEOUT_S` (5 detik).
- Hasil kegagalan: **503** `source_unavailable` (sumber mati) atau **504** `source_timeout` (sumber menggantung), selalu tanpa hasil sebagian.
- Query SQL ada di `services/federation/queries/` dan ikut masuk ke image `federation`.

## Batasan

- DuckDB berjalan di satu node dan beban query jatuh ke database sumber.
- Tidak ada salinan, jadi laporan ikut gagal bila salah satu sumber mati. Tidak ada riwayat data.
- Kredensial demo ada di connection string dan variabel lingkungan compose. DuckDB tidak menyarankan ini untuk produksi.
- Gagal akibat sumber mati baru terlihat setelah sekitar 4 detik, karena resolusi nama di jaringan Docker lambat (lihat F1 di [`experiments.md`](experiments.md)).
