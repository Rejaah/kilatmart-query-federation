# Failure experiments

Aturan: prediksi ditulis sebelum percobaan dijalankan. Hasil yang berbeda dari prediksi tetap ditulis apa adanya, dan prediksi tidak diubah sesudahnya.

Percobaan dijalankan dengan skrip di `scripts/` dan buktinya ada di `docs/evidence/`.

## F1: sumber mati (`docker compose stop stock-db`)

**Percobaan.** Stok SKU-001 diturunkan ke 2 supaya order 2 ikut laporan (jadi 5 baris, sebagai penanda data). Lalu `docker compose stop stock-db`, laporan dipanggil, `docker compose start stock-db`, dan laporan dipanggil sampai pulih. `scripts/analyst.sh` berjalan sepanjang percobaan. Skrip: `scripts/failure_stop_source.sh`.

**Prediksi:**

(akan diisi sebelum percobaan dijalankan)

**Hasil:**

(akan diisi setelah percobaan dijalankan)

**Penjelasan:**

(akan diisi setelah percobaan dijalankan)

## F2: sumber menggantung (`docker compose pause stock-db`)

**Percobaan.** `docker compose pause stock-db` membekukan proses MySQL: koneksi masih diterima jaringan tetapi tidak ada jawaban. Laporan dipanggil, lalu `docker compose unpause stock-db`. Skrip: `scripts/failure_pause_source.sh`.

**Prediksi:**

(akan diisi sebelum percobaan dijalankan)

**Hasil:**

(akan diisi setelah percobaan dijalankan)

**Penjelasan:**

(akan diisi setelah percobaan dijalankan)
