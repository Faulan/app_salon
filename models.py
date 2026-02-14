import hashlib
from config import get_db_connection

class SalonModel:
    # ==========================================================
    # 1. AUTHENTICATION & ACCOUNT MANAGEMENT
    # ==========================================================
    
    @staticmethod
    def get_user_by_username(username):
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        db.close()
        return user

    @staticmethod
    def register_user(username, password, role, nama, hp, alamat):
        db = get_db_connection()
        cursor = db.cursor()
        try:
            hashed_pass = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                           (username, hashed_pass, role))
            user_id = cursor.lastrowid
            
            if role == 'pelanggan':
                cursor.execute("INSERT INTO profil_pelanggan (id_user, nama_lengkap, no_hp, alamat) VALUES (%s, %s, %s, %s)", 
                               (user_id, nama, hp, alamat))
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    def update_account_settings(id_user, username, password_hashed=None):
        db = get_db_connection()
        cursor = db.cursor()
        try:
            if password_hashed:
                cursor.execute("UPDATE users SET username=%s, password=%s WHERE id_user=%s", 
                               (username, password_hashed, id_user))
            else:
                cursor.execute("UPDATE users SET username=%s WHERE id_user=%s", 
                               (username, id_user))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    def update_staff_profile(id_user, nama, foto=None):
        db = get_db_connection()
        cursor = db.cursor()
        try:
            if foto:
                cursor.execute("UPDATE pelayan SET nama_pelayan=%s, foto_pelayan=%s WHERE id_user=%s", 
                               (nama, foto, id_user))
            else:
                cursor.execute("UPDATE pelayan SET nama_pelayan=%s WHERE id_user=%s", 
                               (nama, id_user))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()

    # ==========================================================
    # 2. ADMIN DASHBOARD & STATS
    # ==========================================================

    @staticmethod
    def get_admin_stats():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COALESCE((SELECT SUM(total_bayar) FROM booking WHERE status='Selesai'), 0) as pendapatan,
                (SELECT COUNT(*) FROM profil_pelanggan) as member,
                (SELECT COUNT(*) FROM booking WHERE status='Menunggu') as pending
        """)
        stats = cursor.fetchone()
        db.close()
        return stats

    @staticmethod
    def get_staf_performance():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT pl.nama_pelayan, COUNT(b.id_booking) as total 
            FROM pelayan pl 
            LEFT JOIN booking b ON pl.id_pelayan = b.id_pelayan 
            GROUP BY pl.id_pelayan
        """)
        data = cursor.fetchall()
        db.close()
        return data

    @staticmethod
    def get_booking_status_stats():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT status, COUNT(*) as jumlah FROM booking GROUP BY status")
        results = cursor.fetchall()
        db.close()
        all_statuses = ['Menunggu', 'Diterima', 'Selesai', 'Ditolak']
        data_dict = {row['status']: row['jumlah'] for row in results}
        return [{'status': s, 'jumlah': data_dict.get(s, 0)} for s in all_statuses]

    # ==========================================================
    # 3. STAFF DASHBOARD & STATS
    # ==========================================================

    @staticmethod
    def get_staff_dashboard_data(id_user):
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM booking b JOIN pelayan p ON b.id_pelayan = p.id_pelayan 
                 WHERE p.id_user = %s AND b.status = 'Menunggu') as total_menunggu,
                (SELECT COUNT(*) FROM booking b JOIN pelayan p ON b.id_pelayan = p.id_pelayan 
                 WHERE p.id_user = %s AND b.status = 'Diterima') as total_aktif,
                (SELECT COUNT(*) FROM booking b JOIN pelayan p ON b.id_pelayan = p.id_pelayan 
                 WHERE p.id_user = %s AND b.status = 'Selesai') as total_selesai,
                (SELECT COUNT(*) FROM booking b JOIN pelayan p ON b.id_pelayan = p.id_pelayan 
                 WHERE p.id_user = %s AND b.status = 'Ditolak') as total_ditolak,
                COALESCE((SELECT SUM(total_bayar) FROM booking b JOIN pelayan p ON b.id_pelayan = p.id_pelayan 
                 WHERE p.id_user = %s AND b.status = 'Selesai'), 0) as total_pendapatan
        """, (id_user, id_user, id_user, id_user, id_user))
        stats = cursor.fetchone()

        cursor.execute("""
            SELECT b.tgl_booking as label, SUM(b.total_bayar) as value
            FROM booking b JOIN pelayan p ON b.id_pelayan = p.id_pelayan
            WHERE p.id_user = %s AND b.status = 'Selesai'
            GROUP BY b.tgl_booking ORDER BY b.tgl_booking ASC LIMIT 7
        """, (id_user,))
        chart_line = cursor.fetchall()

        cursor.execute("""
            SELECT b.tgl_booking, b.jam_booking, pr.nama_lengkap as pelanggan, 
                   pr.no_hp, l.nama_layanan, b.status
            FROM booking b
            JOIN pelayan p ON b.id_pelayan = p.id_pelayan
            JOIN profil_pelanggan pr ON b.id_user = pr.id_user
            JOIN layanan l ON b.id_layanan = l.id_layanan
            WHERE p.id_user = %s AND b.status IN ('Menunggu', 'Diterima')
            ORDER BY b.tgl_booking ASC, b.jam_booking ASC LIMIT 5
        """, (id_user,))
        recent_bookings = cursor.fetchall()

        db.close()
        return {
            'stats': stats,
            'line_labels': [row['label'].strftime('%d %b') if row['label'] else '-' for row in chart_line],
            'line_data': [row['value'] for row in chart_line],
            'antrian': recent_bookings
        }

    # ==========================================================
    # 4. MASTER DATA MANAGEMENT
    # ==========================================================

    @staticmethod
    def get_all_pelayan():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pelayan")
        data = cursor.fetchall()
        db.close()
        return data

    @staticmethod
    def get_all_layanan():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM layanan")
        data = cursor.fetchall()
        db.close()
        return data

    @staticmethod
    def get_all_pelanggan():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id_user, u.username, p.nama_lengkap, p.no_hp, p.alamat 
            FROM users u JOIN profil_pelanggan p ON u.id_user = p.id_user 
            WHERE u.role = 'pelanggan'
        """)
        data = cursor.fetchall()
        db.close()
        return data

    @staticmethod
    def update_pelayan_status(id_pelayan, status):
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE pelayan SET status_aktif = %s WHERE id_pelayan = %s", (status, id_pelayan))
        db.commit()
        db.close()

    # ==========================================================
    # 5. BOOKING & TRANSAKSI LOGIC
    # ==========================================================

    @staticmethod
    def get_all_bookings():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, p.nama_lengkap as pelanggan, p.no_hp, l.nama_layanan, l.harga, pl.nama_pelayan
            FROM booking b
            JOIN profil_pelanggan p ON b.id_user = p.id_user
            JOIN layanan l ON b.id_layanan = l.id_layanan
            JOIN pelayan pl ON b.id_pelayan = pl.id_pelayan
            ORDER BY b.tgl_input DESC
        """)
        data = cursor.fetchall()
        db.close()
        return data

    # PERBAIKAN LOGIKA STATUS DITOLAK AGAR PEMBAYARAN KOSONG 
    @staticmethod
    def update_booking_status(id_booking, status, metode='Tunai', bayar=0, kembali=0):
        db = get_db_connection()
        cursor = db.cursor()
        try:
            # Jika status selesai, simpan data pembayaran asli
            if status == 'Selesai':
                cursor.execute("""
                    SELECT l.harga FROM layanan l JOIN booking b ON l.id_layanan = b.id_layanan 
                    WHERE b.id_booking = %s
                """, (id_booking,))
                res = cursor.fetchone()
                harga = res[0] if res else 0
                
                cursor.execute("""
                    UPDATE booking SET status = %s, total_bayar = %s, metode_bayar = %s, 
                    uang_bayar = %s, kembalian = %s WHERE id_booking = %s
                """, (status, harga, metode, bayar, kembali, id_booking))
            
            # Jika status Ditolak, paksa kolom pembayaran menjadi 0 dan NULL
            elif status == 'Ditolak':
                cursor.execute("""
                    UPDATE booking SET status = %s, total_bayar = 0, metode_bayar = NULL, 
                    uang_bayar = 0, kembalian = 0 WHERE id_booking = %s
                """, (status, id_booking))
            
            # Jika status Menunggu atau Diterima, pastikan metode tetap NULL
            else:
                cursor.execute("UPDATE booking SET status = %s, metode_bayar = NULL WHERE id_booking = %s", (status, id_booking))
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    def create_booking(id_user, id_layanan, id_pelayan, tgl, jam):
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO booking (id_user, id_layanan, id_pelayan, tgl_booking, jam_booking, status) VALUES (%s, %s, %s, %s, %s, 'Menunggu')",
                           (id_user, id_layanan, id_pelayan, tgl, jam))
            db.commit()
            return True
        except:
            db.rollback()
            return False
        finally:
            db.close()

    # ==========================================================
    # 6. REPORTS & HISTORY
    # ==========================================================

    @staticmethod
    def get_laporan_data():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, p.nama_lengkap, l.nama_layanan, pl.nama_pelayan
            FROM booking b
            JOIN profil_pelanggan p ON b.id_user = p.id_user
            JOIN layanan l ON b.id_layanan = l.id_layanan
            JOIN pelayan pl ON b.id_pelayan = pl.id_pelayan
            WHERE b.status = 'Selesai' ORDER BY b.tgl_booking DESC, b.jam_booking DESC
        """)
        data = cursor.fetchall()
        db.close()
        return data

    @staticmethod
    def get_pendapatan_per_pelayan():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.nama_pelayan, p.spesialisasi, p.foto_pelayan, 
                   COUNT(b.id_booking) as jumlah_layanan,
                   SUM(COALESCE(b.total_bayar, 0)) as omzet_dihasilkan
            FROM pelayan p 
            LEFT JOIN booking b ON p.id_pelayan = b.id_pelayan AND b.status = 'Selesai'
            GROUP BY p.id_pelayan 
            ORDER BY omzet_dihasilkan DESC
        """)
        data = cursor.fetchall()
        db.close()
        return data

    @staticmethod
    def get_riwayat_booking():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, p.nama_lengkap, l.nama_layanan, pl.nama_pelayan
            FROM booking b
            JOIN profil_pelanggan p ON b.id_user = p.id_user
            JOIN layanan l ON b.id_layanan = l.id_layanan
            JOIN pelayan pl ON b.id_pelayan = pl.id_pelayan
            WHERE b.status IN ('Selesai', 'Ditolak')
            ORDER BY b.tgl_booking DESC, b.jam_booking DESC
        """)
        data = cursor.fetchall()
        db.close()
        return data

    @staticmethod
    def get_user_profile(id_user):
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM profil_pelanggan WHERE id_user = %s", (id_user,))
        data = cursor.fetchone()
        db.close()
        return data

    @staticmethod
    def get_user_bookings(id_user):
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, l.nama_layanan, l.kategori, pl.nama_pelayan, pl.foto_pelayan, pl.spesialisasi, l.harga
            FROM booking b
            JOIN layanan l ON b.id_layanan = l.id_layanan
            JOIN pelayan pl ON b.id_pelayan = pl.id_pelayan
            WHERE b.id_user = %s ORDER BY b.tgl_input DESC
        """, (id_user,))
        data = cursor.fetchall()
        db.close()
        return data