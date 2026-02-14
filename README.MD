
# 💇‍♀️ Glamour Salon Management System

Aplikasi manajemen operasional salon kecantikan berbasis web yang dibangun menggunakan **Python Flask** dan  **MySQL** . Sistem ini mencakup manajemen booking, layanan, staf, hingga visualisasi analitik pendapatan.

---

## 🛠️ Prasyarat (Prerequisites)

Sebelum menjalankan aplikasi, pastikan perangkat Anda telah terpasang:

* **Python 3.x**
* **MySQL Server** (Disarankan menggunakan XAMPP atau Laragon)
* **Web Browser** (Chrome/Edge/Firefox)

---

## 🚀 Cara Menjalankan Aplikasi

### 1. Persiapan Database

1. Buka **phpMyAdmin** atau MySQL client lainnya.
2. Buat database baru dengan nama `db_salon`.
3. Import file `db_salon.sql` yang tersedia di folder utama proyek ini.

### 2. Instalasi Library (Virtual Environment)

Buka terminal/CMD di folder proyek dan jalankan perintah:

**Bash**

```
pip install flask flask-mysqldb
```

 *(Atau sesuaikan dengan library konektor yang Anda gunakan)* .

### 3. Konfigurasi Port Database

Jika MySQL Anda tidak berjalan di port default ( **3306** ), Anda **WAJIB** mengubahnya agar aplikasi bisa terhubung ke database.

1. Buka file `config.py`.
2. Cari bagian `MYSQL_PORT`.
3. Ubah nilainya sesuai port MySQL Anda (misal: `3307`).

**Contoh isi `config.py`:**

**Python**

```
class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'db_salon'
    MYSQL_PORT = 5000  # <--- UBAH DI SINI JIKA PORT BERBEDA
```

### 4. Menjalankan Server

Jalankan perintah berikut di terminal:

**Bash**

```
python app.py
```

Aplikasi akan berjalan di alamat: `http://127.0.0.1:5002`

---

## 📂 Struktur Proyek

**Plaintext**

```
TUBES_BASDAT_SALON/
├── app.py           # Controller utama Flask
├── config.py        # Konfigurasi Database & Port
├── models.py        # Logika Query SQL
├── static/          # CSS, JS, & Upload Gambar
└── templates/       # File HTML (Admin, Staff, User)
```

---

## 👤 Akun Demo

| **Role**      | **Username** | **Password** | **Secret Code** |
| ------------------- | ------------------ | ------------------ | --------------------- |
| **Admin**     | `admin_salon`    | `admin123`       | `SALON2026`         |
| **Staff**     | `rian_staff`     | `staff123`       | `SALON2026`         |
| **Pelanggan** | `budi_customer`  | `user123`        | -                     |

---

## 📝 Fitur Utama

* **Autentikasi Aman** : Hash password menggunakan SHA-256.
* **Role Based Access** : Pembagian hak akses Admin, Staff, dan Pelanggan.
* **Database Lanjut** : Menggunakan Trigger, Stored Procedure, dan Function.
* **Dashboard Analitik** : Visualisasi grafik menggunakan Chart.js.
* **Laporan** : Ekspor data ke format Excel.
