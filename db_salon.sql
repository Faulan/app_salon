-- ==========================================================
-- 1. PEMBUATAN DATABASE & TABEL (DDL)
-- ==========================================================
DROP DATABASE IF EXISTS db_salon;
CREATE DATABASE IF NOT EXISTS db_salon;
USE db_salon;

-- Tabel Users: Menyimpan akun untuk Admin, Pelanggan, dan Staff
CREATE TABLE users (
    id_user INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL, 
    role ENUM('admin', 'pelanggan', 'staff') NOT NULL
) ENGINE=InnoDB;

-- Tabel Pelayan: Terhubung ke tabel users agar staff bisa login
CREATE TABLE pelayan (
    id_pelayan INT PRIMARY KEY AUTO_INCREMENT,
    id_user INT UNIQUE DEFAULT NULL, 
    nama_pelayan VARCHAR(100) NOT NULL,
    spesialisasi VARCHAR(100),
    foto_pelayan VARCHAR(255), -- DEFAULT Dihapus agar INSERT foto langsung bekerja
    status_aktif ENUM('tersedia', 'sibuk', 'cuti') DEFAULT 'tersedia',
    FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Tabel Layanan: Katalog jasa salon
CREATE TABLE layanan (
    id_layanan INT PRIMARY KEY AUTO_INCREMENT,
    nama_layanan VARCHAR(100) NOT NULL,
    harga INT NOT NULL,
    kategori ENUM('Rambut', 'Wajah', 'Kuku', 'Badan') NOT NULL,
    foto_katalog VARCHAR(255), -- DEFAULT Dihapus agar INSERT foto langsung bekerja
    deskripsi TEXT
) ENGINE=InnoDB;

-- Tabel Profil Pelanggan: Data diri member
CREATE TABLE profil_pelanggan (
    id_profil INT PRIMARY KEY AUTO_INCREMENT,
    id_user INT NOT NULL,
    nama_lengkap VARCHAR(100) NOT NULL,
    no_hp VARCHAR(15),
    alamat TEXT,
    FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tabel Booking: Mencatat transaksi, antrian, dan rincian pembayaran
CREATE TABLE booking (
    id_booking INT PRIMARY KEY AUTO_INCREMENT,
    id_user INT NOT NULL, 
    id_layanan INT NOT NULL,
    id_pelayan INT NOT NULL,
    tgl_booking DATE NOT NULL,      -- Menyimpan tanggal janji temu (YYYY-MM-DD)
    jam_booking TIME NOT NULL,		-- Menyimpan jam kedatangan pelanggan (HH:MM:SS)
    status ENUM('Menunggu', 'Diterima', 'Ditolak', 'Selesai') DEFAULT 'Menunggu',
    total_bayar INT DEFAULT 0,
    uang_bayar INT DEFAULT 0,
    kembalian INT DEFAULT 0,
    metode_bayar ENUM('Tunai', 'QRIS', 'Transfer') DEFAULT NULL, -- DEFAULT SET NULL
    -- [AUTO TIMESTAMP]: Mencatat waktu persis data dimasukkan ke sistem secara otomatis
    tgl_input TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES users(id_user),
    FOREIGN KEY (id_layanan) REFERENCES layanan(id_layanan),
    FOREIGN KEY (id_pelayan) REFERENCES pelayan(id_pelayan)
) ENGINE=InnoDB;

-- ==========================================================
-- TAMBAHAN KHUSUS: STORED PROCEDURE, FUNCTION, & TRIGGER
-- (SESUAI PERINTAH TUGAS DOKUMENTASI)
-- ==========================================================

-- A. STORED PROCEDURE: Untuk mengambil total omzet berdasarkan rentang tanggal (Laporan Khusus)
-- [FILTERING DATE]: Menggunakan operator BETWEEN pada kolom tipe DATE untuk membatasi rentang laporan.
DELIMITER //
CREATE PROCEDURE sp_HitungOmzetPeriode(IN tgl_mulai DATE, IN tgl_akhir DATE)
BEGIN
    SELECT SUM(total_bayar) AS total_pendapatan
    FROM booking
    WHERE status = 'Selesai' AND tgl_booking BETWEEN tgl_mulai AND tgl_akhir;
END //
DELIMITER ;

-- B. FUNCTION: Untuk memformat angka nominal menjadi format mata uang Rupiah
DELIMITER //
CREATE FUNCTION fn_FormatRupiah(nominal INT) 
RETURNS VARCHAR(50)
DETERMINISTIC
BEGIN
    RETURN CONCAT('Rp ', FORMAT(nominal, 0, 'id_ID'));
END //
DELIMITER ;

-- C. TRIGGER: Otomatis merubah status pelayan menjadi 'sibuk' jika booking status 'Diterima'
-- Dan kembali 'tersedia' jika status 'Selesai'
DELIMITER //
CREATE TRIGGER trg_UpdateStatusPelayan
AFTER UPDATE ON booking
FOR EACH ROW
BEGIN
    IF NEW.status = 'Diterima' THEN
        UPDATE pelayan SET status_aktif = 'sibuk' WHERE id_pelayan = NEW.id_pelayan;
    ELSEIF NEW.status = 'Selesai' OR NEW.status = 'Ditolak' THEN
        UPDATE pelayan SET status_aktif = 'tersedia' WHERE id_pelayan = NEW.id_pelayan;
    END IF;
END //
DELIMITER ;

-- ==========================================================
-- 2. PENGISIAN DATA AWAL (DML) - FOTO LANGSUNG DI-INSERT
-- ==========================================================

-- Insert Akun (Admin, Pelanggan, Staff)
INSERT INTO users (username, password, role) VALUES  
('admin_salon', SHA2('admin123', 256), 'admin'),
('budi_customer', SHA2('user123', 256), 'pelanggan'),
('siti_customer', SHA2('user123', 256), 'pelanggan'),
('ani_customer', SHA2('user123', 256), 'pelanggan'),
('rian_staff', SHA2('staff123', 256), 'staff'),
('maya_staff', SHA2('staff123', 256), 'staff'),
('dewi_staff', SHA2('staff123', 256), 'staff');

-- Data Pelayan (staff) dengan FOTO LANGSUNG (Sinkron dengan folder uploads)
INSERT INTO pelayan (id_user, nama_pelayan, spesialisasi, status_aktif, foto_pelayan) VALUES  
(5, 'Rian Stylist', 'Hair Coloring & Cut', 'tersedia', 'rian_stylist.jpg'),
(6, 'Maya Beautician', 'Facial & Makeup', 'sibuk', 'maya_beautician.jpg'),
(7, 'Dewi Specialist', 'Manicure & Pedicure', 'tersedia', 'dewi_specialist.jpg');

-- Data Profil Pelanggan
INSERT INTO profil_pelanggan (id_user, nama_lengkap, no_hp, alamat) VALUES  
(2, 'Budi Santoso', '08123456789', 'Jl. Merdeka No. 10'),
(3, 'Siti Aminah', '08577788899', 'Jl. Mawar No. 5'),
(4, 'Ani Wijaya', '08112233445', 'Jl. Melati No. 88');

-- Katalog Layanan dengan FOTO LANGSUNG (Sinkron dengan folder uploads)
INSERT INTO layanan (nama_layanan, harga, kategori, deskripsi, foto_katalog) VALUES  
('Potong Rambut Pria', 50000, 'Rambut', 'Potong rambut model terbaru + cuci', 'potong_rambut.jpg'),
('Facial Glowing', 150000, 'Wajah', 'Pembersihan wajah dan masker organik', 'facial_glowing.jpg'),
('Manicure Pedicure', 120000, 'Kuku', 'Perawatan kuku tangan dan kaki', 'manicure_pedicure.jpg'),
('Creambath', 85000, 'Rambut', 'Nutrisi rambut dan pijat relaksasi', 'creambath.jpg'),
('Coloring Premium', 250000, 'Rambut', 'Pewarnaan rambut kualitas salon Paris', 'coloring_premium.jpg');

-- ==========================================================
-- 3. TRANSAKSI MASIF (DML VARIATIF - TERMASUK DITOLAK)
-- ==========================================================

-- Riwayat: Rian Stylist (Pelayan ID 1)
INSERT INTO booking (id_user, id_layanan, id_pelayan, tgl_booking, jam_booking, status, total_bayar, uang_bayar, kembalian, metode_bayar) VALUES  
(2, 1, 1, '2026-01-05', '09:00:00', 'Selesai', 50000, 50000, 0, 'Tunai'),
(3, 5, 1, '2026-01-10', '13:00:00', 'Selesai', 250000, 250000, 0, 'QRIS'),
(4, 1, 1, '2026-01-15', '10:00:00', 'Selesai', 50000, 100000, 50000, 'Tunai'),
(2, 5, 1, '2026-01-20', '15:30:00', 'Selesai', 250000, 250000, 0, 'Transfer'),
(3, 4, 1, '2026-02-01', '11:00:00', 'Selesai', 85000, 100000, 15000, 'Tunai'),
(4, 1, 1, '2026-02-03', '14:00:00', 'Ditolak', 0, 0, 0, NULL), -- DATA DITOLAK
(2, 4, 1, '2026-02-05', '10:00:00', 'Selesai', 85000, 100000, 15000, 'Transfer'),
(3, 5, 1, '2026-02-07', '16:00:00', 'Selesai', 250000, 250000, 0, 'Tunai');

-- Riwayat: Maya Beautician (Pelayan ID 2)
INSERT INTO booking (id_user, id_layanan, id_pelayan, tgl_booking, jam_booking, status, total_bayar, uang_bayar, kembalian, metode_bayar) VALUES  
(3, 2, 2, '2026-01-02', '11:00:00', 'Selesai', 150000, 150000, 0, 'QRIS'),
(4, 2, 2, '2026-01-08', '14:00:00', 'Ditolak', 0, 0, 0, NULL), -- DATA DITOLAK
(2, 2, 2, '2026-01-12', '16:00:00', 'Selesai', 150000, 150000, 0, 'Transfer'),
(3, 2, 2, '2026-01-18', '09:30:00', 'Selesai', 150000, 150000, 0, 'QRIS');

-- Riwayat: Dewi Specialist (Pelayan ID 3)
INSERT INTO booking (id_user, id_layanan, id_pelayan, tgl_booking, jam_booking, status, total_bayar, uang_bayar, kembalian, metode_bayar) VALUES  
(2, 3, 3, '2026-01-03', '10:00:00', 'Selesai', 120000, 120000, 0, 'Transfer'),
(3, 3, 3, '2026-01-07', '15:00:00', 'Selesai', 120000, 150000, 30000, 'Tunai'),
(4, 3, 3, '2026-01-14', '11:00:00', 'Selesai', 120000, 120000, 0, 'QRIS'),
(2, 3, 3, '2026-01-21', '14:00:00', 'Ditolak', 0, 0, 0, NULL), -- DATA DITOLAK
(3, 1, 3, '2026-01-28', '16:30:00', 'Selesai', 50000, 50000, 0, 'Tunai'),
(4, 3, 3, '2026-02-02', '13:00:00', 'Selesai', 120000, 120000, 0, 'QRIS');

-- Antrian Campuran Aktif (Diterima / Menunggu)
INSERT INTO booking (id_user, id_layanan, id_pelayan, tgl_booking, jam_booking, status, total_bayar, uang_bayar, kembalian, metode_bayar) VALUES  
(2, 2, 2, '2026-02-12', '14:00:00', 'Diterima', 150000, 0, 0, NULL),
(3, 5, 1, '2026-02-15', '11:00:00', 'Menunggu', 0, 0, 0, NULL);

-- ==========================================================
-- 3. CEK DATA TIAP TABEL 
-- ==========================================================
SELECT * FROM users;
SELECT * FROM pelayan;
SELECT * FROM layanan;
SELECT * FROM profil_pelanggan;
SELECT * FROM booking;

-- ==========================================================
-- 4. QUERY KHUSUS TAMPILAN PELANGGAN
-- ==========================================================
-- Mengambil data katalog layanan untuk ditampilkan pada halaman Booking Pelanggan, 
-- diurutkan berdasarkan kategori agar tampilan lebih rapi.
SELECT id_layanan, nama_layanan, harga, kategori, deskripsi, foto_katalog 
FROM layanan 
ORDER BY kategori ASC;

-- Mengambil data tim pelayan (staff) yang memiliki status 'tersedia' 
-- agar pelanggan hanya bisa memilih staf yang tidak sedang sibuk atau cuti.
SELECT id_pelayan, nama_pelayan, spesialisasi 
FROM pelayan 
WHERE status_aktif = 'tersedia';

-- ==========================================================
-- 5. QUERY DASHBOARD ADMIN & LAPORAN (SINKRONISASI)
-- ==========================================================
-- Ringkasan Card Utama
SELECT  
    (SELECT SUM(total_bayar) FROM booking WHERE status = 'Selesai') as total_pendapatan,
    (SELECT COUNT(*) FROM profil_pelanggan) as total_member,
    (SELECT COUNT(*) FROM booking WHERE status = 'Menunggu') as booking_pending;

-- Data Grafik Batang (Performa Staf - Berdasarkan jumlah order)
SELECT pl.nama_pelayan, COUNT(b.id_booking) as total_order
FROM pelayan pl
LEFT JOIN booking b ON pl.id_pelayan = b.id_pelayan
GROUP BY pl.id_pelayan;

-- Data Grafik Lingkaran (Semua Status)
SELECT status, COUNT(*) as jumlah 
FROM booking 
GROUP BY status
ORDER BY FIELD(status, 'Selesai', 'Diterima', 'Menunggu', 'Ditolak');

-- Statistik Omzet per Metode Pembayaran
SELECT metode_bayar, SUM(total_bayar) as omzet_per_metode
FROM booking 
WHERE status = 'Selesai'
GROUP BY metode_bayar;

-- Detail Laporan Lengkap dengan Jam & Pembayaran (Untuk Rekap Transaksi)
-- MENGGUNAKAN JOIN ANTAR TABEL (Syarat Dokumentasi)
SELECT 
    b.id_booking, b.tgl_booking, b.jam_booking, 
    p.nama_lengkap, l.nama_layanan, b.total_bayar, 
    b.uang_bayar, b.kembalian, b.metode_bayar
FROM booking b
JOIN profil_pelanggan p ON b.id_user = p.id_user
JOIN layanan l ON b.id_layanan = l.id_layanan
WHERE b.status = 'Selesai';

-- Laporan Pendapatan dari Masing-Masing Pelayan (staff) - Untuk Admin
SELECT 
    p.nama_pelayan, 
    COUNT(b.id_booking) as jumlah_layanan,
    SUM(b.total_bayar) as omzet_dihasilkan
FROM pelayan p
JOIN booking b ON p.id_pelayan = b.id_pelayan
WHERE b.status = 'Selesai'
GROUP BY p.id_pelayan;

-- ==========================================================
-- 6. QUERY DASHBOARD STAFF (PRIBADI)
-- ==========================================================
-- A. Ringkasan Statistik (Contoh untuk Staff Rian/ID_User 5)
SELECT 
    (SELECT COUNT(*) FROM booking b JOIN pelayan p ON b.id_pelayan = p.id_pelayan WHERE p.id_user = 5 AND b.status = 'Diterima') as antrian_aktif,
    (SELECT COUNT(*) FROM booking b JOIN pelayan p ON b.id_pelayan = p.id_pelayan WHERE p.id_user = 5 AND b.status = 'Selesai') as total_selesai,
    (SELECT SUM(total_bayar) FROM booking b JOIN pelayan p ON b.id_pelayan = p.id_pelayan WHERE p.id_user = 5 AND b.status = 'Selesai') as estimasi_pendapatan;

-- B. Grafik Garis: Tren Pendapatan Harian Staff
-- [AGGREGATION BY DATE]: Mengelompokkan pendapatan berdasarkan hari untuk visualisasi tren.
SELECT tgl_booking, SUM(total_bayar) as pendapatan_harian
FROM booking b
JOIN pelayan p ON b.id_pelayan = p.id_pelayan
WHERE p.id_user = 5 AND b.status = 'Selesai'
GROUP BY tgl_booking
ORDER BY tgl_booking ASC;

-- C. Grafik Lingkaran: Rasio Status Kerja Staff
SELECT status, COUNT(*) as jumlah
FROM booking b
JOIN pelayan p ON b.id_pelayan = p.id_pelayan
WHERE p.id_user = 5
GROUP BY status;

-- D. Antrian Terbaru di Dashboard Staff
-- [TIME-SENSITIVE DATA]: Menampilkan 5 antrian paling mendesak bagi staff yang bertugas.
SELECT b.jam_booking, pr.nama_lengkap as pelanggan, l.nama_layanan
FROM booking b
JOIN pelayan p ON b.id_pelayan = p.id_pelayan
JOIN profil_pelanggan pr ON b.id_user = pr.id_user
JOIN layanan l ON b.id_layanan = l.id_layanan
WHERE p.id_user = 5 AND b.status IN ('Menunggu', 'Diterima')
ORDER BY b.tgl_booking DESC, b.jam_booking DESC
LIMIT 5;

/* =============================================
   PENGATURAN HAK AKSES DATABASE (GRANT)
   ============================================= */
DROP USER IF EXISTS 'admin_salon_db'@'localhost';
DROP USER IF EXISTS 'pelanggan_salon_db'@'localhost';
DROP USER IF EXISTS 'staff_salon_db'@'localhost';

CREATE USER 'admin_salon_db'@'localhost' IDENTIFIED BY 'pass_admin_salon';
CREATE USER 'pelanggan_salon_db'@'localhost' IDENTIFIED BY 'pass_pelanggan_salon';
CREATE USER 'staff_salon_db'@'localhost' IDENTIFIED BY 'pass_staff_salon';

GRANT ALL PRIVILEGES ON db_salon.* TO 'admin_salon_db'@'localhost';
GRANT SELECT ON db_salon.layanan TO 'pelanggan_salon_db'@'localhost';
GRANT SELECT ON db_salon.pelayan TO 'pelanggan_salon_db'@'localhost';
GRANT SELECT, INSERT ON db_salon.booking TO 'pelanggan_salon_db'@'localhost';
GRANT SELECT, UPDATE ON db_salon.profil_pelanggan TO 'pelanggan_salon_db'@'localhost';
GRANT SELECT ON db_salon.users TO 'pelanggan_salon_db'@'localhost';

-- Hak Akses Staff (Operasional)
GRANT SELECT ON db_salon.booking TO 'staff_salon_db'@'localhost';
GRANT SELECT ON db_salon.pelayan TO 'staff_salon_db'@'localhost';
GRANT UPDATE (status) ON db_salon.booking TO 'staff_salon_db'@'localhost';

FLUSH PRIVILEGES;

-- CEK STATUS AKHIR
SELECT user, host FROM mysql.user WHERE user LIKE '%salon_db%';
SHOW GRANTS FOR 'admin_salon_db'@'localhost';
SHOW GRANTS FOR 'pelanggan_salon_db'@'localhost';
SHOW GRANTS FOR 'staff_salon_db'@'localhost';