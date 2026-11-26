# Federasi kueri dalam KilatMart

## Gaya integrasi

KilatMart menggunakan federasi kueri (*query federation*) untuk menggabungkan data dari PostgreSQL dan MySQL. DuckDB membaca `shop.orders` dan `inv.stock` ketika analis meminta laporan, lalu menggabungkan keduanya berdasarkan `sku`. Hasil dikirim sebagai JSON. Perubahan stok melalui `inventory-api` dapat terlihat pada permintaan laporan berikutnya karena DuckDB membaca kembali tabel stok.

## Ketergantungan antarkomponen

PostgreSQL dan MySQL dapat mempertahankan mesin dan skema masing-masing. Analis cukup mengakses satu endpoint laporan, sementara `federation` menangani koneksi ke sumber. API sumber tetap menangani perubahan data. Jalur laporan memakai akun dengan izin baca dan koneksi `READ_ONLY`. Pembacaan langsung juga meniadakan jadwal pemutakhiran tabel salinan untuk laporan ini.

Kueri tetap bergantung pada nama tabel, nama kolom, dan tipe data sumber. Sebagai contoh, perubahan tipe atau makna `sku` pada salah satu tabel dapat mengganggu penggabungan. Alias `shop` dan `inv` juga harus sesuai antara konfigurasi `SOURCES` dan [SQL laporan](../services/federation/queries/low_stock_paid_orders.sql).

Kedua sumber harus dapat dijangkau saat laporan diminta. Resolusi nama, pembukaan koneksi, dan pembacaan data ikut menentukan waktu respons. Semakin sering laporan diminta, semakin sering pula basis data sumber melayani pembacaan. Jika salah satu sumber gagal, pemanggil menerima respons galat untuk laporan gabungan.

## Cakupan pekerjaan ESB dan ETL

Dalam skenario pembacaan ini, `federation` menangani sebagian tugas yang dapat ditempatkan pada alur integrasi berbasis *enterprise service bus* (ESB). Layanan membuka koneksi ke dua sumber, meminta data yang diperlukan, lalu menyajikan satu respons kepada analis. DuckDB meneruskan sebagian penyaringan ke sumber dan mengerjakan penggabungan hasil.

Laporan ini juga dapat disusun tanpa proses ekstraksi, transformasi, dan pemuatan (*extract, transform, load* atau ETL) terjadwal. Penyaringan dan penggabungan berlangsung saat laporan diminta sehingga hasilnya tidak perlu dimuat ke penyimpanan analitik. Cakupan pendekatan ini terbatas pada penyajian laporan dari data sumber yang tersedia saat itu.

## Batas penerapan

DuckDB berjalan dalam satu kontainer. Penggabungan data dikerjakan oleh kontainer tersebut, sedangkan pembacaan membebani basis data sumber. Laporan tidak menyimpan riwayat, sehingga keadaan stok pada waktu sebelumnya tidak dapat ditelusuri dari hasil laporan saat ini.

Endpoint `/health/sources` membantu mengenali sumber yang bermasalah. Batas waktu kueri membatasi waktu tunggu layanan dan memicu upaya interupsi, sementara biaya koneksi atau pembacaan yang telah terjadi tetap ditanggung sumber. Kredensial pada string koneksi dan variabel lingkungan merupakan bagian dari konfigurasi demo.
