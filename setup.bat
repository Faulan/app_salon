@echo off
echo ==================================================
echo   GENERATE STRUKTUR PROYEK GLAMOUR SALON
echo ==================================================

:: Membuat folder utama
mkdir static
mkdir static\css
mkdir static\js
mkdir static\img
mkdir templates
mkdir templates\admin
mkdir templates\user
mkdir templates\components

:: Membuat file utama (kosong)
type nul > app.py
type nul > config.py
type nul > models.py
type nul > static\css\style.css
type nul > static\js\chart_logic.js
type nul > static\js\script.js
type nul > templates\layout.html
type nul > templates\login.html
type nul > templates\register.html
type nul > templates\profile.html
type nul > templates\admin\dashboard.html
type nul > templates\admin\pelanggan.html
type nul > templates\admin\layanan.html
type nul > templates\admin\pelayan.html
type nul > templates\admin\booking.html
type nul > templates\admin\laporan.html
type nul > templates\user\dashboard.html
type nul > templates\user\katalog.html
type nul > templates\user\riwayat.html
type nul > templates\components\struk_modal.html

echo.
echo [SUKSES] Struktur folder dan file telah dibuat!
echo Silakan mulai koding di app.py dan models.py.
echo ==================================================
pause

