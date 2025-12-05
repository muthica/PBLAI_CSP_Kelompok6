# PBLAI_CSP_Kelompok6

**Deskripsi Singkat**
/n Program dibuat menggunakan Constraint Satisfaction Problem (CSP) untuk membuat jadwal irigasi optimal pada lahan pertanian dengan berbagai jenis tanaman. Program mengalokasikan slot waktu irigasi ke setiap petak dengan mempertimbangkan:
-Kebutuhan durasi irigasi per petak
-Kapasitas maksimal pompa per jam
-Jam operasional harian yang tersedia
-Constraint non-overlapping (satu petak tidak boleh disiram 2 kali di jam yang sama)

**Dataset**
Program memuat parameter penjadwalan dan kendala dari 2 file CSV:
1. "plots.csv"  (Variabel & Kendala Durasi)
    Berisi daftar variabel (X_i) dan kendala durasi ("durasi_jam" ) untuk setiap petak.
2. "pump_settings.csv"  (Domain & Kendala Kapasitas)
    File mendefinisikan domain waktu yang tersedia dan kendala kapasitas global.
    Program juga akan otomatis membentuk slot waktu (Domain) dari nilai "jam_mulai"  hingga "jam_selesai" .

**Cara Menjalankan Program**
