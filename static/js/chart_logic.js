/**
 * 1. FUNGSI UNTUK DASHBOARD ADMIN
 * Menampilkan performa semua staf (Bar) dan status booking global (Doughnut)
 */
function renderCharts(stafLabels, stafData, statusLabels, statusData) {
  const colors = {
    purpleMain: "#6a1b9a", // Diterima
    purpleLight: "#9c4dcc",
    pinkMain: "#ad1457", // Selesai (Aksen)
    yellowMain: "#fbc02d", // Menunggu
    redMain: "#c62828", // Ditolak
    tealMain: "#4db6ac",
    greenMain: "#198754", // Selesai (Status)
  };

  // BAR CHART - ADMIN (Performa Beban Kerja)
  const ctxBar = document.getElementById("barChart").getContext("2d");
  new Chart(ctxBar, {
    type: "bar",
    data: {
      labels: stafLabels,
      datasets: [
        {
          label: "Total Layanan",
          data: stafData,
          backgroundColor: colors.purpleMain,
          hoverBackgroundColor: colors.purpleLight,
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: "#f0f0f0" } },
        x: { grid: { display: false } },
      },
    },
  });

  // PIE/DOUGHNUT CHART - ADMIN (Global Status)
  const statusColorMapping = {
    Selesai: colors.greenMain,
    Diterima: colors.purpleMain,
    Menunggu: colors.yellowMain,
    Ditolak: colors.redMain,
  };

  const backgroundColors = statusLabels.map(
    (label) => statusColorMapping[label] || colors.tealMain,
  );
  const ctxPie = document.getElementById("pieChart").getContext("2d");
  new Chart(ctxPie, {
    type: "doughnut",
    data: {
      labels: statusLabels,
      datasets: [
        {
          data: statusData,
          backgroundColor: backgroundColors,
          borderWidth: 3,
          borderColor: "#ffffff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { usePointStyle: true, padding: 25 },
        },
      },
    },
  });
}

/**
 * 2. FUNGSI UNTUK DASHBOARD STAFF (SINKRON 4 STATUS & GELOMBANG)
 * Menampilkan statistik harian pendapatan pribadi (Garis/Wave)
 * dan Rasio 4 Status Layanan (Doughnut)
 */
function renderStaffCharts(
  incomeLabels,
  incomeData,
  totalSelesai,
  totalDitolak,
  totalDiterima,
  totalMenunggu,
) {
  const salonColors = {
    purple: "#6a1b9a", // Diterima
    pink: "#ad1457", // Aksen/Titik
    green: "#198754", // Selesai
    red: "#c62828", // Ditolak
    yellow: "#fbc02d", // Menunggu
  };

  // --- LINE CHART - STATISTIK PENDAPATAN DENGAN EFEK GELOMBANG (WAVE) ---
  const ctxLine = document
    .getElementById("staffRevenueLineChart")
    .getContext("2d");

  // Gradient Fill di bawah garis (Memberikan efek kedalaman seperti foto referensi Anda)
  const gradient = ctxLine.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, "rgba(106, 27, 154, 0.4)");
  gradient.addColorStop(1, "rgba(106, 27, 154, 0.0)");

  new Chart(ctxLine, {
    type: "line",
    data: {
      labels: incomeLabels,
      datasets: [
        {
          label: "Pendapatan (Rp)",
          data: incomeData,
          borderColor: salonColors.purple,
          backgroundColor: gradient,
          borderWidth: 4,
          fill: true,
          // PENGATURAN GELOMBANG (SANGAT PENTING)
          tension: 0.5, // Menaikkan tension agar lekukan lebih "luwes"
          cubicInterpolationMode: "monotone", // Menghasilkan kurva yang halus antar titik data
          pointRadius: 6,
          pointBackgroundColor: salonColors.pink,
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
          pointHoverRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(0,0,0,0.8)",
          callbacks: {
            label: function (context) {
              return " Pendapatan: Rp " + context.raw.toLocaleString("id-ID");
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "#f0f0f0", drawBorder: false },
          ticks: { callback: (v) => "Rp " + v.toLocaleString("id-ID") },
        },
        x: { grid: { display: false } },
      },
      animation: {
        duration: 2500, // Animasi lebih lambat agar transisi gelombang terlihat cantik
        easing: "easeInOutQuart",
      },
    },
  });

  // --- DOUGHNUT CHART - KONTRIBUSI LAYANAN (SINKRON 4 STATUS LENGKAP) ---
  const ctxStaffPie = document
    .getElementById("staffStatusPieChart")
    .getContext("2d");
  new Chart(ctxStaffPie, {
    type: "doughnut",
    data: {
      labels: ["Menunggu", "Diterima", "Selesai", "Ditolak"],
      datasets: [
        {
          data: [totalMenunggu, totalDiterima, totalSelesai, totalDitolak],
          backgroundColor: [
            salonColors.yellow, // Menunggu
            salonColors.purple, // Diterima
            salonColors.green, // Selesai
            salonColors.red, // Ditolak
          ],
          hoverOffset: 15,
          borderWidth: 4,
          borderColor: "#ffffff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "75%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            usePointStyle: true,
            padding: 20,
            font: { family: "'Poppins', sans-serif", size: 12 },
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage =
                total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
              return ` ${context.label}: ${context.raw} (${percentage}%)`;
            },
          },
        },
      },
      animation: { animateScale: true, animateRotate: true },
    },
  });
}
