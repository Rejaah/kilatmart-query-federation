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

| # | Prediksi | Yang terjadi | Cocok |
|---|---|---|---|
| 1 | 503, `source_unavailable`, `stock-db` | persis itu, tiga panggilan berturut-turut | ya |
| 2 | gagal di bawah 1,5 detik | **4,27 s, 4,10 s, 4,11 s** per panggilan | **tidak** |
| 3 | tanpa hasil sebagian | isi respons hanya `error`, `source`, `detail`, tanpa `rows` | ya |
| 4 | `webshop-api` tetap 200, 12 order | `GET /orders` HTTP 200, 12 order | ya |
| 5 | pulih 5 sampai 20 detik, tanpa restart federation, stok tetap | pulih sekitar 2 detik setelah perintah `start` selesai, tanpa restart federation, laporan 5 baris (stok 2 bertahan) | sebagian: pulih dan stok ya, waktunya **lebih cepat** dari prediksi |
| 6 | `detail` tanpa password | `detail` memuat connection string lengkap dengan `password=***` | ya, tetapi lihat penjelasan |

Dari sisi analis (`f1-analyst.txt`): OK pada 17:32:46, GAGAL `source_unavailable` sumber `stock-db` pada 17:32:48, 17:32:51, 17:32:57, dan 17:33:03, lalu OK lagi pada 17:33:06. Jarak antar baris GAGAL melebar dari 2 detik menjadi 3, 6, dan 6 detik.

**Bukti:** `docs/evidence/f1-script.txt` (keluaran skrip, respons JSON, dan waktu tiap panggilan), `f1-analyst.txt` (jendela analis), `f1-federation.log` (log federation: baris `ERROR ... error=source_unavailable source=stock-db`), `f1-dns-check.txt` (pengukuran waktu resolusi nama).

**Penjelasan:**

- **Kenapa prediksi 2 meleset.** Saya mengira "nama tidak bisa di-resolve" berarti gagal seketika. Pengukuran terpisah di luar DuckDB (`f1-dns-check.txt`) menunjukkan sebaliknya: saat `stock-db` mati, resolusi namanya gagal setelah 3,96 detik, nama yang memang tidak ada sama sekali butuh 2,53 detik, sedangkan `orders-db` yang hidup selesai dalam 0,00 detik. Jadi sekitar 4 detik habis di resolusi nama sebelum DuckDB sempat menghubungi apa pun. Dugaan mekanismenya: DNS internal Docker meneruskan nama yang tidak dikenalnya ke resolver di luar jaringan lalu menunggu jawabannya. Dugaan itu belum diuji lebih jauh.
- **Akibatnya terhadap analis.** Setiap panggilan gagal menghabiskan sekitar 4 detik ditambah jeda 2 detik, sehingga baris GAGAL muncul tiap 6 detik, bukan tiap 2 detik.
- **Margin yang tipis.** Waktu gagal 4,1 sampai 4,3 detik hanya sekitar 0,7 detik di bawah `QUERY_TIMEOUT_S` = 5. Bila resolusi nama lebih lambat di jaringan lain, kodenya akan bergeser dari 503 menjadi 504 dengan `source` yang tetap `stock-db`. Itu kesimpulan dari rancangan kode, bukan hasil yang diuji.
- **Password.** Tanda `***` pada `detail` hanya bisa muncul dari penyamaran di `_attach` (`str(exc).replace(FED_PASSWORD, "***")`). Berarti pesan asli DuckDB memuat connection string lengkap dengan password, dan tanpa penyamaran itu password demo akan bocor ke JSON 503 dan ke log. Host, port, nama database, dan user `fed_ro` tetap terlihat di pesan. Ini contoh nyata batasan "kredensial di connection string".
- **Availability coupling terbukti.** Selama `stock-db` mati, laporan gagal total dan menyebut sumbernya. Tidak ada hasil sebagian karena tidak ada salinan yang bisa dipakai sebagai pengganti. Itu harga dari data yang selalu segar.
- **Kenapa pulih tanpa restart.** Koneksi DuckDB dibuka ulang di setiap request (D2), jadi `stock-db` yang menyala kembali langsung terpakai. Stok bertahan karena `stop` dan `start` tidak menghapus container (D7). Waktu pulih sekitar 2 detik lebih cepat dari prediksi 5 sampai 20 detik. Dugaan saya, MySQL naik dari direktori data kecil yang sudah ada sehingga cepat. Itu belum diukur terpisah, dan angka 2 detik dihitung sejak perintah `start` selesai, tanpa durasi perintah itu sendiri.

## F2: sumber menggantung (`docker compose pause stock-db`)

**Percobaan.** `docker compose pause stock-db` membekukan proses MySQL: koneksi masih diterima jaringan tetapi tidak ada jawaban. Laporan dipanggil, lalu `docker compose unpause stock-db`. Skrip: `scripts/failure_pause_source.sh`.

**Prediksi:**

1. Laporan menjawab HTTP 504 dengan `error: "source_timeout"`, `timeout_s: 5.0`, dan `source: "stock-db"` (sumber yang sedang di-ATTACH saat batas waktu habis).
2. Waktu respons sekitar 5,0 sampai 5,6 detik, dan sama untuk setiap panggilan. Tidak ada panggilan yang lebih cepat dari 5 detik.
3. `GET /health` pada `federation` tetap 200 dengan cepat (di bawah 1 detik) selama laporan menggantung, karena endpoint berupa `def` biasa yang berjalan di thread pool dan tidak memblokir server.
4. Setelah `docker compose unpause stock-db`, laporan kembali 200 dalam 3 detik, tanpa restart `federation`.
5. Yang saya ragukan: `conn.interrupt()` belum tentu bisa memutus `ATTACH` yang tersangkut di jaringan, jadi thread latar mungkin tetap menggantung sampai MySQL menjawab. Yang saya yakini hanyalah respons 504 tetap datang tepat waktu, karena request menunggu dengan `join(timeout)`, bukan menunggu thread itu.

**Hasil:**

| # | Prediksi | Yang terjadi | Cocok |
|---|---|---|---|
| 1 | 504, `source_timeout`, `timeout_s` 5.0, `stock-db` | `{"error":"source_timeout","timeout_s":5.0,"source":"stock-db"}` pada tiga panggilan | ya |
| 2 | 5,0 sampai 5,6 detik, sama setiap panggilan | 5,18 s, 5,18 s, 5,18 s | ya |
| 3 | `/health` tetap cepat saat laporan menggantung | HTTP 200 dalam **0,022 s** saat laporan lain sedang menunggu | ya |
| 4 | pulih dalam 3 detik tanpa restart | poll pertama setelah `unpause` sudah 200 (0 detik), tanpa restart federation | ya |
| 5 | `interrupt()` belum tentu memutus ATTACH, tetapi 504 tetap tepat waktu | 504 tepat waktu terbukti. Apakah thread latar tertinggal **tidak diukur** | sebagian terbukti |

Dari sisi analis (`f2-analyst.txt`): OK pada 17:34:18 dan 17:34:20, GAGAL `source_timeout` sumber `stock-db` pada 17:34:23 dan 17:34:30 (selang 7 detik), lalu OK pada 17:34:37 dengan `elapsed_ms` 963, dan OK normal (128 ms) pada 17:34:41.

**Bukti:** `docs/evidence/f2-script.txt`, `f2-analyst.txt`, `f2-federation.log`.

**Penjelasan:**

- **Beda `stop` dan `pause`.** Saat `stop`, nama sumber hilang dari DNS dan gagal dengan 503. Saat `pause`, container masih ada dan koneksi diterima jaringan, tetapi MySQL tidak menjawab, sehingga `ATTACH` menunggu sampai batas waktu kita habis dan jawabannya 504. Lamanya mirip (sekitar 4,1 s dan 5,2 s), tetapi jenis kegagalannya berbeda, dan itu yang membedakan "sumber mati" dari "sumber menggantung".
- **Sumber diketahui.** Nama `stock-db` pada 504 berasal dari `state["stage"]` di `federation.py`, yang diisi sebelum tiap `ATTACH`. Bila yang menggantung query setelah semua `ATTACH` selesai, sumbernya `null`.
- **Server tidak ikut membeku.** `/health` menjawab dalam 0,022 detik saat satu laporan menunggu, karena endpoint federation `def` biasa (thread pool) dan bukan `async def`.
- **Yang tidak terbukti.** Skrip ini tidak menguji perilaku tanpa timeout, dan tidak mengukur apakah thread latar yang tersangkut di `ATTACH` benar-benar selesai setelah `unpause`. Jangan mengklaim `interrupt()` berhasil memutus sambungan. Yang terbukti hanyalah request pemanggil dijawab 504 tepat waktu.
- **Panggilan OK pertama sesudah pulih lebih lambat** (963 ms dibanding sekitar 120 ms). Penyebabnya belum diselidiki.
