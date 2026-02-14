/**
 * GLAMOUR SALON - Core UI Scripts
 * Menangani Validasi, Pencarian, dan Interaksi UI
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. AUTO-FADE FLASH MESSAGES
  // Menghilangkan notifikasi sukses/gagal secara otomatis setelah 3 detik
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 3000);
  });

  // 2. LIVE SEARCH PELANGGAN (Di halaman admin/pelanggan.html)
  const customerSearch = document.getElementById("customerSearch");
  if (customerSearch) {
    customerSearch.addEventListener("keyup", function () {
      let filter = this.value.toLowerCase();
      let rows = document.querySelectorAll("#customerTable tbody tr");

      rows.forEach((row) => {
        let text = row.innerText.toLowerCase();
        row.style.display = text.includes(filter) ? "" : "none";
      });
    });
  }

  // 3. VALIDASI FORM REGISTER
  // Memastikan password dan konfirmasi password sama
  const regForm = document.getElementById("regForm");
  if (regForm) {
    regForm.addEventListener("submit", function (e) {
      const pass = document.querySelector('input[name="password"]').value;
      // Jika kamu menambah field confirm_password nantinya
      const confirmPass = document.querySelector(
        'input[name="confirm_password"]',
      )?.value;

      if (confirmPass && pass !== confirmPass) {
        e.preventDefault();
        alert("Password tidak cocok!");
      }
    });
  }

  // 4. PREVIEW GAMBAR (Untuk Admin saat upload foto layanan)
  const imageInput = document.querySelector('input[type="file"]');
  if (imageInput) {
    imageInput.addEventListener("change", function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          // Jika ada elemen img dengan id 'preview', update src-nya
          const preview = document.getElementById("preview");
          if (preview) preview.src = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    });
  }
});

// 5. PRINT STRUK FUNCTION
// Fungsi untuk mencetak struk secara rapi
function printStruk() {
  const prtContent = document.getElementById("strukArea");
  if (!prtContent) return;

  const WinPrint = window.open(
    "",
    "",
    "left=0,top=0,width=800,height=900,toolbar=0,scrollbars=0,status=0",
  );
  WinPrint.document.write(`
        <html>
            <head>
                <title>Cetak Struk - Glamour Salon</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body { font-family: 'Courier New', Courier, monospace; padding: 20px; }
                    .struk-border { border: 1px dashed #000; padding: 15px; max-width: 400px; margin: auto; }
                </style>
            </head>
            <body onload="window.print();window.close()">
                <div class="struk-border">
                    ${prtContent.innerHTML}
                </div>
            </body>
        </html>
    `);
  WinPrint.document.close();
  WinPrint.focus();
}
