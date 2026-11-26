# Arsitektur KilatMart

KilatMart menampilkan pesanan yang telah dibayar dan terkait dengan produk yang stoknya berada pada atau di bawah ambang pemesanan ulang. Data pesanan tersimpan di PostgreSQL, sedangkan data stok tersimpan di MySQL. Layanan `federation` menggunakan DuckDB untuk menyusun laporan dari kedua sumber saat permintaan diterima.

```text
Analis → federation (DuckDB, port 8003)
              │
              ├── baca → orders-db (PostgreSQL) ← tulis ── webshop-api (port 8001)
              └── baca → stock-db  (MySQL)      ← tulis ── inventory-api (port 8002)
```

## Alur permintaan laporan

1. Layanan membuka koneksi DuckDB baru dan memuat ekstensi `postgres` serta `mysql`. Kedua ekstensi dipasang saat citra Docker dibangun.
2. DuckDB menghubungkan `orders-db` sebagai `shop` dan `stock-db` sebagai `inv` melalui `ATTACH ... READ_ONLY`. Akun basis data `fed_ro` hanya memiliki izin `SELECT`.
3. DuckDB menjalankan [kueri laporan](../services/federation/queries/low_stock_paid_orders.sql). Kueri menggabungkan pesanan dan stok berdasarkan `sku`, menyaring pesanan berstatus `paid`, lalu memeriksa kondisi `qty_on_hand <= reorder_level`.
4. Layanan mengembalikan hasil sebagai JSON dan koneksi DuckDB ditutup pada akhir eksekusi. Permintaan berikutnya membuka koneksi baru sehingga sumber yang pulih dapat digunakan kembali tanpa memulai ulang `federation`.

## Kegagalan sumber

Setiap sumber dihubungkan melalui pemanggilan `ATTACH` tersendiri. Jika pemanggilan itu gagal, API mengembalikan HTTP `503` dengan kode `source_unavailable` dan nama sumber. Jika eksekusi melewati batas `QUERY_TIMEOUT_S` (bawaan 5 detik), API mengembalikan HTTP `504` dengan kode `source_timeout`. Nama sumber tersedia pada respons `504` jika batas waktu tercapai saat `ATTACH`. Kedua respons tersebut hanya memuat informasi kegagalan.

Pada percobaan F1, resolusi nama `stock-db` yang dihentikan memerlukan sekitar 4 detik. Waktu tersebut merupakan hasil pengukuran pada lingkungan uji. Lihat [catatan percobaan](experiments.md).

## Batas operasional

DuckDB berjalan dalam satu kontainer. Basis data sumber menanggung beban pembacaan, sedangkan DuckDB mengerjakan penggabungan hasil. Laporan bergantung pada ketersediaan kedua sumber dan hanya mencerminkan data yang dapat dibaca saat permintaan berjalan. Prototipe ini tidak menyimpan salinan atau riwayat laporan.

Konfigurasi demo menggunakan variabel lingkungan Docker Compose untuk menyusun string koneksi yang memuat kredensial. Penggunaan di lingkungan produksi memerlukan pengelolaan kredensial yang sesuai.
