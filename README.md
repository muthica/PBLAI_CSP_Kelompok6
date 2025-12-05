# PBLAI_CSP_Kelompok6

    🌿🌿🌿🌿🌿
**Deskripsi Singkat**

Program dibuat menggunakan Constraint Satisfaction Problem (CSP) untuk membuat jadwal irigasi optimal pada lahan pertanian dengan berbagai jenis tanaman dan juga untuk mengalokasikan slot waktu irigasi ke setiap petak dengan mempertimbangkan:
-Kebutuhan durasi irigasi per petak
-Kapasitas maksimal pompa per jam
-Jam operasional harian yang tersedia
-Constraint non-overlapping (satu petak tidak boleh disiram 2 kali di jam yang sama)

**📊Dataset**

Program memuat parameter penjadwalan dan kendala dari 2 file CSV:
1. _"plots.csv"_  (Variabel & Kendala Durasi)
    File berisi daftar variabel (X_i) dan kendala durasi ("durasi_jam") untuk setiap petak.
2. _"pump_settings.csv"_ (Domain & Kendala Kapasitas)
    File berisi domain waktu yang tersedia dan kendala kapasitas global.
    Program juga akan otomatis membentuk slot waktu (Domain) dari nilai "jam_mulai"  hingga "jam_selesai" .

**🌾Cara Menjalankan Program🌾**

1. Membaca input _plots.csv_ dan _pump_settings.csv_.
2. Mengubah durasi penyiraman menjadi kumpulan variabel CSP.
3. Memberikan domain waktu (slot jam) ke setiap variabel.
4. Menjalankan pencarian backtracking dengan heuristik MRV dan forward checking.
5. Setiap assignment dicek dengan constraint kapasitas pompa dan larangan penyiraman ganda pada petak yang sama.
6. Jika semua variabel berhasil ditempatkan tanpa melanggar constraint, jadwal dicetak sebagai solusi.
