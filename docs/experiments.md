# Failure experiments

Aturan: prediksi ditulis sebelum percobaan dijalankan. Hasil yang berbeda dari prediksi tetap ditulis apa adanya, dan prediksi tidak diubah sesudahnya.

Percobaan dijalankan dengan skrip di `scripts/` dan buktinya ada di `docs/evidence/`. Jam penulisan prediksi: 2026-11-24 17:32, sebelum percobaan apa pun dijalankan.

## F1: sumber mati (`docker compose stop stock-db`)

**Percobaan.** Stok SKU-001 diturunkan ke 2 supaya order 2 ikut laporan (jadi 5 baris, sebagai penanda data). Lalu `docker compose stop stock-db`, laporan dipanggil, `docker compose start stock-db`, dan laporan dipanggil sampai pulih. `scripts/analyst.sh` berjalan sepanjang percobaan. Skrip: `scripts/failure_stop_source.sh`.

**Prediksi:**

1. Laporan menjawab HTTP 503 dengan `error: "source_unavailable"` dan `source: "stock-db"`.
2. Gagalnya cepat, bukan menunggu timeout: waktu respons di bawah 1,5 detik, jauh di bawah `QUERY_TIMEOUT_S` = 5. Alasannya: setelah container berhenti, nama `stock-db` tidak lagi bisa di-resolve di jaringan Docker, jadi `ATTACH` gagal seketika. Analis menampilkan GAGAL pada tick pertama sesudah `stop` (paling lambat 3 detik).
3. Tidak ada hasil sebagian: respons hanya berisi error, tanpa kunci `rows`.
4. Sisi `orders-db` tidak terpengaruh: `GET /orders` pada `webshop-api` tetap 200 dengan 12 order.
5. Setelah `docker compose start stock-db`, laporan kembali 200 dalam 5 sampai 20 detik (MySQL naik dari data yang sudah ada, tanpa menjalankan `init.sql`), tanpa restart `federation` karena koneksi dibuka per request (D2). Stok SKU-001 tetap 2 (order 2 masih ada, 5 baris), karena `stop` dan `start` mempertahankan data di container yang sama (D7).
6. Isi `detail` pada JSON 503 memuat pesan dari driver (kemungkinan menyebut host `stock-db`), tetapi tidak memuat password `fed_ro_pw`.

**Hasil:**

(akan diisi setelah percobaan dijalankan)

**Penjelasan:**

(akan diisi setelah percobaan dijalankan)

## F2: sumber menggantung (`docker compose pause stock-db`)

**Percobaan.** `docker compose pause stock-db` membekukan proses MySQL: koneksi masih diterima jaringan tetapi tidak ada jawaban. Laporan dipanggil, lalu `docker compose unpause stock-db`. Skrip: `scripts/failure_pause_source.sh`.

**Prediksi:**

1. Laporan menjawab HTTP 504 dengan `error: "source_timeout"`, `timeout_s: 5.0`, dan `source: "stock-db"` (sumber yang sedang di-ATTACH saat batas waktu habis).
2. Waktu respons sekitar 5,0 sampai 5,6 detik, dan sama untuk setiap panggilan. Tidak ada panggilan yang lebih cepat dari 5 detik.
3. `GET /health` pada `federation` tetap 200 dengan cepat (di bawah 1 detik) selama laporan menggantung, karena endpoint berupa `def` biasa yang berjalan di thread pool dan tidak memblokir server.
4. Setelah `docker compose unpause stock-db`, laporan kembali 200 dalam 3 detik, tanpa restart `federation`.
5. Yang saya ragukan: `conn.interrupt()` belum tentu bisa memutus `ATTACH` yang tersangkut di jaringan, jadi thread latar mungkin tetap menggantung sampai MySQL menjawab. Yang saya yakini hanyalah respons 504 tetap datang tepat waktu, karena request menunggu dengan `join(timeout)`, bukan menunggu thread itu.

**Hasil:**

(akan diisi setelah percobaan dijalankan)

**Penjelasan:**

(akan diisi setelah percobaan dijalankan)
