# Konsep query federation

## Gaya integrasi

KilatMart memakai query federation. `federation` menerima satu permintaan laporan, membuka koneksi DuckDB, lalu menghubungkan PostgreSQL dan MySQL dengan `ATTACH`. Query pada `services/federation/queries/low_stock_paid_orders.sql` menggabungkan `shop.orders` dengan `inv.stock` menggunakan `sku`.

Federation membaca data di sumber ketika laporan diminta. Hasilnya dikembalikan langsung kepada analis dan tidak disimpan di analytics store. Perubahan stok melalui `inventory-api` terlihat pada laporan berikutnya karena query membaca baris terbaru dari MySQL.

## Coupling yang berkurang

- Kedua database tidak perlu memakai mesin atau skema fisik yang sama. DuckDB menangani koneksi PostgreSQL dan MySQL pada satu query.
- Tidak ada tabel salinan yang harus dijadwalkan atau disegarkan. Data laporan mengikuti keadaan sumber saat query berjalan.
- API sumber tetap memiliki tanggung jawab menulis data. `federation` menggunakan akun `fed_ro` dan `READ_ONLY`, sehingga jalur laporan tidak mendapat hak tulis.
- Analis cukup memakai endpoint laporan dan tidak perlu mengetahui detail koneksi setiap sumber.

## Coupling yang muncul

- Query bergantung pada nama tabel, kolom, dan tipe data di kedua sumber. Perubahan `orders.sku`, `stock.sku`, atau kolom filter dapat mematahkan laporan.
- Alias `shop` dan `inv` harus konsisten antara `SOURCES` di `federation.py` dan SQL laporan.
- Satu laporan memerlukan kedua sumber. Jika `orders-db` atau `stock-db` mati, hasil sebagian tidak dikembalikan. API memetakan kegagalan menjadi `503` atau `504`.
- Beban join dan pembacaan jatuh ke database sumber ketika laporan dijalankan. Banyak analis atau query yang mahal dapat meningkatkan beban sumber.
- Ketersediaan laporan mengikuti jaringan dan kredensial sumber. Koneksi baru dibuat pada setiap request, sehingga waktu resolusi nama dan koneksi ikut masuk ke waktu laporan.

## Pekerjaan ESB atau ETL yang diambil alih

Pada skenario ini, federation mengambil pekerjaan orkestrasi baca yang biasanya dikerjakan oleh alur integrasi terpisah. DuckDB membuka koneksi ke dua sumber, mendorong sebagian filter ke sumber, menjalankan join, dan mengembalikan satu bentuk JSON kepada analis.

Federation juga menghilangkan kebutuhan ETL berkala untuk salinan laporan ini. Tidak ada proses ekstraksi terjadwal, transformasi ke tabel perantara, atau pemuatan ke analytics store. API sumber tetap menjadi jalur perubahan data, sedangkan federation hanya menyusun data saat dibaca.

## Batasan alat

- DuckDB pada service ini berjalan pada satu container. Tidak ada cluster query atau pembagian beban lintas node.
- Federation tidak menyimpan riwayat. Laporan hanya menggambarkan data yang dapat dibaca ketika request berlangsung.
- Kegagalan satu sumber menghentikan laporan gabungan. Endpoint `health/sources` membantu menunjukkan sumber yang bermasalah, tetapi tidak menyediakan hasil pengganti.
- Akun dan kata sandi demo dikirim melalui variabel lingkungan dan connection string. Konfigurasi ini cocok untuk latihan, tetapi perlu pengelolaan rahasia yang lebih baik pada lingkungan produksi.
- Query timeout mencegah request menggantung terlalu lama, tetapi tidak menghapus biaya koneksi dan pembacaan yang sudah terjadi di sumber.
