MLBB INSIGHT — FINAL WEBSITE PACKAGE
=====================================

FILE UTAMA
- index.html : website MLBB INSIGHT (unggah ke ROOT repository GitHub Pages)
- .nojekyll  : file penanda untuk publikasi file statis
- videos/    : folder video opsional; isi video sendiri yang boleh dipublikasikan

CARA PUBLISH DARI HP (GITHUB PAGES)
1. Download ZIP dan ekstrak di aplikasi Pengelola File Android.
2. Buka folder hasil ekstrak MLBB-INSIGHT-FINAL-PACK.
3. Masuk ke github.com lewat Chrome dan login.
4. Buat repository baru bernama mlbb-insight, pilih Public, lalu Create repository.
5. Buka repository. Pilih Add file > Upload files.
6. Unggah index.html, .nojekyll, dan README-GITHUB-HP.txt ke ROOT repository.
   Jangan unggah folder induk MLBB-INSIGHT-FINAL-PACK sebagai satu folder.
   index.html harus terlihat sejajar dengan README di halaman utama repository.
7. Untuk folder video, unggah videos/README.txt ke folder videos (buat folder videos bila belum ada).
8. Isi commit message, misalnya: Publish MLBB INSIGHT, lalu Commit changes.
9. Buka Settings > Pages. Pada Build and deployment, pilih Source: Deploy from a branch.
10. Pilih Branch: main dan Folder: /(root), lalu Save.
11. Kembali ke Settings > Pages dan buka alamat website yang ditampilkan GitHub.

JIKA REPOSITORY SUDAH ADA
- Backup file lama terlebih dahulu.
- Ganti index.html dengan file index.html dari paket ini.
- Jika GitHub menolak karena nama file sudah ada, buka index.html lama, pilih Delete this file, commit, lalu upload file baru dengan nama index.html.
- Pertahankan folder videos bila sudah berisi video. Jangan hapus video milikmu.

PENTING
- Buka website melalui alamat GitHub Pages setelah dipublikasikan. Membuka HTML langsung dari file manager Android tidak selalu didukung dan tidak sama dengan menjalankan website melalui server.
- Roster hero, equipment, dan sebagian gambar memakai sumber dataset publik; internet diperlukan untuk memuat data/gambar online. Data fallback disediakan untuk kondisi tertentu.
- Tiga pemutar video masih berupa slot lokal. Tambahkan file MP4 yang sesuai ke folder videos jika ingin memakainya.
- Statistik ranked LIVE belum otomatis aktif hanya dengan mengunggah website. Deploy backend API secara terpisah ke Vercel, lalu tempel URL HTTPS backend di bagian Alamat API MLBB INSIGHT. Tanpa backend, statistik tetap menampilkan status belum terhubung, bukan angka palsu.
- Login demo memakai LocalStorage browser, bukan autentikasi akun online. Jangan gunakan password asli.
- Build hero tanpa sumber spesifik terverifikasi tidak diisi item tebakan; gunakan link rujukan per hero.
- Patch terakhir yang terverifikasi saat penyusunan paket ini adalah Original Server 2.2.23 (11 November 2026). Periksa patch terbaru sebelum memperbarui informasi meta.
- MLBB INSIGHT adalah proyek fan-made dan tidak berafiliasi dengan Moonton.
