from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import SalonModel
from config import get_db_connection
import os
import hashlib # Modul untuk hashing SHA-256
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_glamour_salon_2026'

# --- KONFIGURASI UPLOAD FOTO ---
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Pastikan folder upload ada saat aplikasi dijalankan
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- MIDDLEWARE: PENGECEKAN LOGIN ---
def is_loggedin():
    return 'loggedin' in session

# --- ROUTE: HALAMAN PUBLIK (LANDING PAGE) ---
@app.route('/')
def index():
    # Menampilkan 3 layanan teratas di landing page sebagai gerbang utama
    layanan_populer = SalonModel.get_all_layanan()[:3]
    return render_template('landing.html', layanan=layanan_populer)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_loggedin(): return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # PROSES SINKRONISASI: Ubah input password user menjadi SHA-256
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        user = SalonModel.get_user_by_username(username)
        
        # Cocokkan hasil hash input dengan hash yang tersimpan di database
        if user and user['password'] == hashed_password:
            session.update({
                'loggedin': True,
                'id_user': user['id_user'],
                'username': user['username'],
                'role': user['role']
            })
            flash(f'Selamat datang, {username}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Username atau Password salah!', 'danger')
    return render_template('login.html')

# --- LOGIKA RESET PASSWORD ---
@app.route('/reset_password', methods=['POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('username')
        new_password = request.form.get('new_password')
        
        # PROSES SINKRONISASI: Hash password baru sebelum disimpan
        hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Cek apakah username terdaftar
        cursor.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cursor.fetchone()
        
        if user:
            # Update password di database menggunakan format hash
            cursor.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_new_password, username))
            db.commit()
            flash('Password berhasil diperbarui! Silakan masuk dengan password baru.', 'success')
        else:
            flash('Gagal Reset! Username tidak ditemukan dalam sistem.', 'danger')
            
        db.close()
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        # Validasi pendaftaran admin & staff (Kode verifikasi internal)
        if data['role'] == 'admin' and data.get('secret_code') != 'SALON2026':
            flash('Kode Rahasia Admin Salah!', 'danger')
            return redirect(url_for('register'))
        
        # Catatan: SalonModel.register_user sudah menangani hashing password di dalamnya
        success = SalonModel.register_user(
            data['username'], data['password'], data['role'], 
            data['nama'], data['hp'], data['alamat']
        )
        if success:
            flash('Registrasi Berhasil!', 'success')
            if session.get('role') == 'admin':
                return redirect(url_for('admin_pelanggan'))
            return redirect(url_for('login'))
        flash('Registrasi Gagal! Username mungkin sudah ada.', 'danger')
    return render_template('register.html')

# --- ROUTE UTAMA DASHBOARD (SINKRONISASI 3 ROLE) ---
@app.route('/dashboard')
def dashboard():
    if not is_loggedin(): return redirect(url_for('login'))
    
    # 1. LOGIKA DASHBOARD ADMIN
    if session['role'] == 'admin':
        all_bookings = SalonModel.get_all_bookings()
        antrian_aktif_terbaru = [b for b in all_bookings if b['status'] in ['Menunggu', 'Diterima']][:5] 
        
        return render_template('admin/dashboard.html', 
            stats=SalonModel.get_admin_stats(),
            batang=SalonModel.get_staf_performance(),
            pie=SalonModel.get_booking_status_stats(),
            aktivitas=antrian_aktif_terbaru 
        )
    
    # 2. LOGIKA DASHBOARD STAFF (SINKRONISASI PENUH DENGAN GRAFIK 4 STATUS)
    elif session['role'] == 'staff':
        # Mengambil data dashboard khusus pelayan yang login
        data_staff = SalonModel.get_staff_dashboard_data(session['id_user'])
        return render_template('staff/dashboard.html', 
            stats=data_staff['stats'],
            line_labels=data_staff['line_labels'],
            line_data=data_staff['line_data'],
            antrian=data_staff['antrian']
        )
    
    # 3. LOGIKA DASHBOARD MEMBER/PELANGGAN
    riwayat = SalonModel.get_user_bookings(session['id_user'])
    stats_member = {
        'menunggu': len([r for r in riwayat if r['status'] == 'Menunggu']),
        'diterima': len([r for r in riwayat if r['status'] == 'Diterima']),
        'selesai': len([r for r in riwayat if r['status'] == 'Selesai']),
        'ditolak': len([r for r in riwayat if r['status'] == 'Ditolak'])
    }
    
    return render_template('user/dashboard.html', stats=stats_member)

# --- ADMIN: MANAJEMEN PELANGGAN ---
@app.route('/admin/pelanggan')
def admin_pelanggan():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    return render_template('admin/pelanggan.html', pelanggan=SalonModel.get_all_pelanggan())

@app.route('/admin/pelanggan/update', methods=['POST'])
def update_pelanggan():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    data = request.form
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE profil_pelanggan SET nama_lengkap=%s, no_hp=%s, alamat=%s WHERE id_user=%s",
                   (data['nama'], data['hp'], data['alamat'], data['id_user']))
    db.commit()
    db.close()
    flash('Data pelanggan berhasil diperbarui!', 'success')
    return redirect(url_for('admin_pelanggan'))

@app.route('/admin/pelanggan/delete/<int:id_user>')
def delete_pelanggan(id_user):
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM profil_pelanggan WHERE id_user = %s", (id_user,))
    cursor.execute("DELETE FROM users WHERE id_user = %s", (id_user,))
    db.commit()
    db.close()
    flash('Member pelanggan telah dihapus.', 'info')
    return redirect(url_for('admin_pelanggan'))

# --- ADMIN: MANAJEMEN LAYANAN ---
@app.route('/admin/layanan')
def admin_layanan():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    return render_template('admin/layanan.html', layanan=SalonModel.get_all_layanan())

@app.route('/admin/layanan/add', methods=['POST'])
def add_layanan():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    nama = request.form['nama']
    kategori = request.form['kategori']
    harga = request.form['harga']
    deskripsi = request.form['deskripsi']
    
    filename = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"srv_{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO layanan (nama_layanan, kategori, harga, deskripsi, foto_katalog) VALUES (%s, %s, %s, %s, %s)",
                   (nama, kategori, harga, deskripsi, filename))
    db.commit()
    db.close()
    
    flash('Layanan baru berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_layanan'))

@app.route('/admin/layanan/update', methods=['POST'])
def update_layanan():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    id_layanan = request.form['id_layanan']
    nama = request.form['nama']
    kategori = request.form['kategori']
    harga = request.form['harga']
    deskripsi = request.form['deskripsi']
    
    db = get_db_connection()
    cursor = db.cursor()

    if 'foto' in request.files and request.files['foto'].filename != '':
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"srv_upd_{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cursor.execute("UPDATE layanan SET nama_layanan=%s, kategori=%s, harga=%s, deskripsi=%s, foto_katalog=%s WHERE id_layanan=%s",
                           (nama, kategori, harga, deskripsi, filename, id_layanan))
    else:
        cursor.execute("UPDATE layanan SET nama_layanan=%s, kategori=%s, harga=%s, deskripsi=%s WHERE id_layanan=%s",
                       (nama, kategori, harga, deskripsi, id_layanan))
    
    db.commit()
    db.close()
    flash('Menu layanan berhasil diperbarui!', 'success')
    return redirect(url_for('admin_layanan'))

@app.route('/admin/layanan/delete/<int:id_layanan>')
def delete_layanan(id_layanan):
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM layanan WHERE id_layanan = %s", (id_layanan,))
    db.commit()
    db.close()
    flash('Layanan telah dihapus dari katalog.', 'info')
    return redirect(url_for('admin_layanan'))

# --- ADMIN: MANAJEMEN PELAYAN (STAF) ---
@app.route('/admin/pelayan')
def admin_pelayan():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    return render_template('admin/pelayan.html', pelayan=SalonModel.get_all_pelayan())

@app.route('/admin/pelayan/add', methods=['POST'])
def add_pelayan():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    nama = request.form['nama']
    spesialisasi = request.form['spesialisasi']
    status = request.form['status']
    
    filename = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"stf_{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO pelayan (nama_pelayan, spesialisasi, status_aktif, foto_pelayan) VALUES (%s, %s, %s, %s)",
                   (nama, spesialisasi, status, filename))
    db.commit()
    db.close()
    flash('Staf baru berhasil didaftarkan!', 'success')
    return redirect(url_for('admin_pelayan'))

@app.route('/admin/pelayan/update', methods=['POST'])
def update_pelayan():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    id_pelayan = request.form['id_pelayan']
    nama = request.form['nama']
    spesialisasi = request.form['spesialisasi']
    
    db = get_db_connection()
    cursor = db.cursor()

    if 'foto' in request.files and request.files['foto'].filename != '':
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"stf_upd_{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cursor.execute("UPDATE pelayan SET nama_pelayan=%s, spesialisasi=%s, foto_pelayan=%s WHERE id_pelayan=%s",
                           (nama, spesialisasi, filename, id_pelayan))
    else:
        cursor.execute("UPDATE pelayan SET nama_pelayan=%s, spesialisasi=%s WHERE id_pelayan=%s",
                       (nama, spesialisasi, id_pelayan))
    
    db.commit()
    db.close()
    flash('Data staf berhasil diperbarui!', 'success')
    return redirect(url_for('admin_pelayan'))

@app.route('/admin/pelayan/update_status/<int:id_pelayan>', methods=['POST'])
def update_pelayan_status_route(id_pelayan):
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    status = request.form['status_aktif']
    SalonModel.update_pelayan_status(id_pelayan, status)
    flash('Status staf diperbarui!', 'success')
    return redirect(url_for('admin_pelayan'))

@app.route('/admin/pelayan/delete/<int:id_pelayan>')
def delete_pelayan(id_pelayan):
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM pelayan WHERE id_pelayan = %s", (id_pelayan,))
    db.commit()
    db.close()
    flash('Data staf telah dihapus.', 'info')
    return redirect(url_for('admin_pelayan'))

# --- ADMIN: ANTRIAN, LAPORAN & RIWAYAT ---
@app.route('/admin/booking')
def admin_booking():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    all_data = SalonModel.get_all_bookings()
    antrian_aktif = [b for b in all_data if b['status'] in ['Menunggu', 'Diterima']]
    layanan = SalonModel.get_all_layanan()
    pelayan = SalonModel.get_all_pelayan()
    pelanggan = SalonModel.get_all_pelanggan() 
    return render_template('admin/booking.html', 
                            bookings=antrian_aktif, 
                            layanan=layanan, 
                            pelayan=pelayan,
                            daftar_pelanggan=pelanggan)

@app.route('/admin/laporan')
def laporan():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    data_laporan = SalonModel.get_laporan_data()
    total = sum(item['total_bayar'] for item in data_laporan if item.get('total_bayar'))
    return render_template('admin/laporan.html', 
        laporan=data_laporan, 
        total_omzet=total, 
        current_date=datetime.now().strftime('%d %B %Y')
    )

# Perbaikan Route Laporan Staf agar sinkron dengan detail & foto
@app.route('/admin/laporan_staff')
def admin_laporan_staff():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    # Fungsi ini sekarang mengambil foto pelayan juga
    laporan_staff = SalonModel.get_pendapatan_per_pelayan() 
    return render_template('admin/laporan_staff.html', laporan=laporan_staff)

@app.route('/admin/riwayat')
def admin_riwayat():
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('admin_riwayat'))
    data_riwayat = SalonModel.get_riwayat_booking()
    return render_template('admin/riwayat.html', riwayat=data_riwayat)

@app.route('/admin/booking/delete/<int:id_booking>')
def delete_booking(id_booking):
    if not is_loggedin() or session['role'] != 'admin': return redirect(url_for('login'))
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM booking WHERE id_booking = %s", (id_booking,))
    db.commit()
    db.close()
    flash('Data transaksi berhasil dihapus!', 'info')
    return redirect(request.referrer or url_for('admin_booking'))

# --- STAFF: OPERASIONAL (ANTRIAN, RIWAYAT, PENDAPATAN) ---
@app.route('/staff/antrian')
def staff_antrian():
    if not is_loggedin() or session['role'] != 'staff': return redirect(url_for('login'))
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id_pelayan FROM pelayan WHERE id_user = %s", (session['id_user'],))
    staff_info = cursor.fetchone()
    db.close()
    
    id_p = staff_info['id_pelayan'] if staff_info else 0
    all_data = SalonModel.get_all_bookings()
    antrian_saya = [b for b in all_data if b['id_pelayan'] == id_p and b['status'] in ['Menunggu', 'Diterima']]
    
    return render_template('staff/antrian_aktif.html', bookings=antrian_saya)

@app.route('/staff/riwayat')
def staff_riwayat():
    if not is_loggedin() or session['role'] != 'staff': return redirect(url_for('login'))
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id_pelayan FROM pelayan WHERE id_user = %s", (session['id_user'],))
    staff_info = cursor.fetchone()
    db.close()
    
    id_p = staff_info['id_pelayan'] if staff_info else 0
    riwayat_global = SalonModel.get_riwayat_booking()
    riwayat_saya = [r for r in riwayat_global if r['id_pelayan'] == id_p]
    
    return render_template('staff/riwayat_pelayanan.html', riwayat=riwayat_saya)

@app.route('/staff/pendapatan')
def staff_pendapatan():
    if not is_loggedin() or session['role'] != 'staff': return redirect(url_for('login'))
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # Menambahkan kolom metode_bayar, uang_bayar, dan kembalian agar tidak kosong
    cursor.execute("""
        SELECT b.tgl_booking, b.jam_booking, pr.nama_lengkap as pelanggan, l.nama_layanan, 
               b.total_bayar, b.metode_bayar, b.uang_bayar, b.kembalian
        FROM booking b
        JOIN pelayan p ON b.id_pelayan = p.id_pelayan
        JOIN profil_pelanggan pr ON b.id_user = pr.id_user
        JOIN layanan l ON b.id_layanan = l.id_layanan
        WHERE p.id_user = %s AND b.status = 'Selesai'
        ORDER BY b.tgl_booking DESC
    """, (session['id_user'],))
    data = cursor.fetchall()
    db.close()
    
    total = sum(d['total_bayar'] for d in data)
    return render_template('staff/pendapatan.html', riwayat=data, total_bulan_ini=total)

# --- PERBAIKAN LOGIKA VITAL: SINKRONISASI PEMBAYARAN KASIR (ADMIN & STAFF) ---
@app.route('/update_status/<int:id_booking>/<status>')
def update_status(id_booking, status):
    if not is_loggedin(): return redirect(url_for('login'))
    
    # Menangkap parameter kasir (Dari Panel Kasir Admin atau Staff)
    metode = request.args.get('metode', 'Tunai')
    bayar = request.args.get('bayar', 0)
    kembali = request.args.get('kembali', 0)
    
    success = SalonModel.update_booking_status(id_booking, status, metode, bayar, kembali)
    
    if success:
        if status == 'Selesai':
            flash(f'Pembayaran {metode} Berhasil! Transaksi telah diarsipkan.', 'success')
        else:
            flash(f'Status diperbarui menjadi {status}!', 'success')
    else:
        flash('Gagal memperbarui status transaksi.', 'danger')
        
    # LOGIKA REDIRECT PINTAR: Mengembalikan ke halaman asal berdasarkan role
    if session['role'] == 'admin':
        return redirect(url_for('admin_booking'))
    elif session['role'] == 'staff':
        return redirect(url_for('staff_antrian'))
    return redirect(url_for('dashboard'))

# --- LOGIKA TAMBAH BOOKING ---
@app.route('/process_booking', methods=['POST'])
def process_booking():
    if not is_loggedin(): return redirect(url_for('login'))
    id_user = request.form.get('id_user_manual') or session.get('id_user')
    success = SalonModel.create_booking(
        id_user, request.form['id_layanan'], 
        request.form['id_pelayan'], request.form['tgl'], request.form['jam']
    )
    if success:
        flash('Booking berhasil ditambahkan!', 'success')
    
    if session['role'] == 'admin':
        return redirect(url_for('admin_booking'))
    return redirect(url_for('user_riwayat'))

# --- USER/MEMBER: KATALOG & RIWAYAT ---
@app.route('/user/katalog')
def user_katalog():
    if not is_loggedin(): return redirect(url_for('login'))
    
    daftar_layanan = SalonModel.get_all_layanan()
    daftar_pelayan = SalonModel.get_all_pelayan()
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('user/katalog.html', 
                            layanan=daftar_layanan, 
                            pelayan=daftar_pelayan, 
                            current_date=today)

@app.route('/user/riwayat')
def user_riwayat():
    if not is_loggedin(): return redirect(url_for('login'))
    data_riwayat = SalonModel.get_user_bookings(session['id_user'])
    return render_template('user/riwayat.html', riwayat=data_riwayat)

# --- PROFILE & LOGOUT ---
@app.route('/profile')
def profile():
    if not is_loggedin(): return redirect(url_for('login'))
    
    # Ambil data dasar user
    bio = SalonModel.get_user_profile(session['id_user'])
    
    if bio is None:
        bio = {}

    # SINKRONISASI STAFF: Jika role staff, ambil data tambahan dari tabel pelayan agar tampil di profile.html
    if session['role'] == 'staff':
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pelayan WHERE id_user = %s", (session['id_user'],))
        staff_extra = cursor.fetchone()
        db.close()
        if staff_extra:
            # Gabungkan data bio dengan data staff (nama_pelayan, spesialisasi, status_aktif, foto_pelayan)
            bio.update(staff_extra)
            
    return render_template('profile.html', bio=bio)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if not is_loggedin(): return redirect(url_for('login'))
    
    data = request.form
    user_id = session['id_user']
    new_username = data.get('username')
    new_password_raw = data.get('password')
    
    # PROSES SINKRONISASI: Hash password hanya jika diisi oleh user
    new_password_hashed = hashlib.sha256(new_password_raw.encode()).hexdigest() if new_password_raw else None
    
    acc_success = SalonModel.update_account_settings(user_id, new_username, new_password_hashed)
    
    if acc_success:
        session['username'] = new_username
        
        # Update data profile berdasarkan role
        if session['role'] == 'pelanggan':
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("""
                UPDATE profil_pelanggan 
                SET nama_lengkap=%s, no_hp=%s, alamat=%s 
                WHERE id_user=%s
            """, (data['nama'], data['hp'], data['alamat'], user_id))
            db.commit()
            db.close()
        elif session['role'] == 'staff':
            # SINKRONISASI FOTO STAFF
            filename = None
            if 'foto' in request.files and request.files['foto'].filename != '':
                file = request.files['foto']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"profile_stf_{user_id}_{datetime.now().timestamp()}.jpg")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Memanggil fungsi baru di models.py untuk update data pelayan (termasuk foto)
            SalonModel.update_staff_profile(user_id, data['nama'], filename)
            
        flash('Data profil dan akun berhasil diperbarui!', 'success')
    else:
        flash('Gagal memperbarui akun. Username mungkin sudah digunakan.', 'danger')
        
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5002)