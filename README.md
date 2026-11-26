# MLBB INSIGHT API

Backend read-only untuk statistik hero ranked MLBB. Website static tetap bisa di-host di GitHub Pages; backend ini di-deploy terpisah ke Vercel.

## Apa yang disediakan

- `GET /api/health` — status service.
- `GET /api/meta/stats?window=7d&rank=all` — statistik win/pick/ban hero.
- `GET /api/heroes/catalog` — katalog hero dari sumber GMS.
- `GET /docs` — dokumentasi endpoint interaktif.

Pilihan `window`: `1d`, `3d`, `7d`, `15d`, `30d`.

Pilihan `rank`: `all` atau `epic_plus`.

Tidak mengumpulkan Game ID, Server ID, password, OTP, atau data akun pemain.

## Deploy ke Vercel

1. Ekstrak folder ini.
2. Buat repository GitHub baru, misalnya `mlbb-insight-api`.
3. Upload isi folder ini ke root repository (file `app.py` dan `requirements.txt` harus berada di root).
4. Buka Vercel, pilih **Add New → Project**, lalu import repository `mlbb-insight-api`.
5. Framework preset biarkan auto-detect / Other. Jangan isi Build Command atau Output Directory.
6. Deploy. Vercel mendukung FastAPI pada Python runtime dan mendeteksi aplikasi `app` di `app.py`.
7. Setelah deploy, buka `https://NAMA-PROJECT.vercel.app/api/health`.
8. Uji `https://NAMA-PROJECT.vercel.app/api/meta/stats?window=7d&rank=all`.
9. Salin URL dasar `https://NAMA-PROJECT.vercel.app` ke bagian **Alamat API MLBB INSIGHT** di halaman utama website.

## Konfigurasi opsional Vercel

- `CACHE_TTL_SECONDS=1800` (default 30 menit)
- `UPSTREAM_TIMEOUT_SECONDS=12` (default 12 detik)
- `ALLOWED_ORIGINS=*` (untuk publik; bisa diubah menjadi domain GitHub Pages lu setelah tahu URL-nya)
- `GMS_SOURCE_ROOT=https://api.gms.moontontech.com/api/gms/source/2669606`

## Tentang sumber statistik

API ini memanggil langsung endpoint GMS yang tersedia dari layanan web Moonton, bukan MLBBHub. Endpoint dan ID sumber merupakan hasil pengamatan komunitas terhadap jaringan web game, bukan dokumentasi developer publik dengan jaminan kompatibilitas. Moonton dapat mengubah endpoint, schema, atau akses sewaktu-waktu. Backend mengembalikan error ketika data tidak valid; ia tidak membuat angka statistik pengganti.

Statistik merupakan agregat untuk periode terpilih, bukan feed pertandingan per detik. Cache backend default 30 menit untuk mengurangi beban ke upstream.

Proyek fan-made, tidak berafiliasi dengan atau didukung Moonton. Nama dan aset game adalah milik pemegang haknya.
