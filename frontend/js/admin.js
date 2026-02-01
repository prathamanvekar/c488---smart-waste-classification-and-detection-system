/**
 * Admin Dashboard JavaScript
 * Handles analytics visualization and admin functionality
 */

// API Configuration
const API_BASE_URL = "http://localhost:5001/api";

// Chart instances
let trendsChart, classDistributionChart, dailyStatsChart, confidenceChart;

// DOM Elements
let notification, notificationText;

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  initializeElements();
  setupEventListeners();
  loadAnalytics();
});

/**
 * Initialize DOM elements
 */
function initializeElements() {
  notification = document.getElementById("notification");
  notificationText = document.getElementById("notificationText");
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  const refreshButton = document.getElementById("refreshButton");
  if (refreshButton) {
    refreshButton.addEventListener("click", () => {
      showNotification("Refreshing analytics...", "info");
      loadAnalytics();
    });
  }

  const resetButton = document.getElementById("resetButton");
  if (resetButton) {
    resetButton.addEventListener("click", handleResetAnalytics);
  }
}

/**
 * Load analytics data from backend
 */
async function loadAnalytics() {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/stats`);
    const data = await response.json();

    if (data.success) {
      updateSummaryStats(data.summary);
      renderDetectionTrendsChart(data.trends);
      renderClassDistributionChart(data.class_distribution);
      renderDailyStatsChart(data.daily_stats);
      renderConfidenceChart(data.accuracy_metrics);
      renderTopClasses(data.top_classes);
      renderRecentDetections(data.recent_detections);

      showNotification("Analytics loaded successfully!", "success");
    } else {
      showNotification("Failed to load analytics", "error");
    }
  } catch (error) {
    console.error("Error loading analytics:", error);
    showNotification(
      "Network error. Please check if backend is running.",
      "error",
    );
  }
}

/**
 * Update summary statistics cards
 */
function updateSummaryStats(summary) {
  document.getElementById("adminTotalDetections").textContent =
    summary.total_detections || 0;
  document.getElementById("adminTotalEcoPoints").textContent =
    summary.total_eco_points || 0;
  document.getElementById("adminAvgConfidence").textContent =
    ((summary.avg_confidence || 0) * 100).toFixed(1) + "%";
  document.getElementById("adminUniqueClasses").textContent =
    summary.unique_classes || 0;
}

/**
 * Render detection trends chart (Line Chart)
 */
function renderDetectionTrendsChart(trends) {
  const ctx = document.getElementById("trendsChart");

  // Destroy existing chart if it exists
  if (trendsChart) {
    trendsChart.destroy();
  }

  const labels = trends.map((t) => t.period);
  const data = trends.map((t) => t.count);
  const avgConfData = trends.map((t) => (t.avg_confidence * 100).toFixed(1));

  trendsChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Detections",
          data: data,
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: true,
          yAxisID: "y",
        },
        {
          label: "Avg Confidence (%)",
          data: avgConfData,
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.4,
          fill: true,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: {
        mode: "index",
        intersect: false,
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          title: {
            display: true,
            text: "Detections",
            color: "#94a3b8",
          },
          ticks: { color: "#94a3b8" },
          grid: { color: "#334155" },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          title: {
            display: true,
            text: "Confidence (%)",
            color: "#94a3b8",
          },
          ticks: { color: "#94a3b8" },
          grid: { drawOnChartArea: false },
        },
        x: {
          ticks: { color: "#94a3b8" },
          grid: { color: "#334155" },
        },
      },
      plugins: {
        legend: {
          labels: { color: "#f1f5f9" },
        },
      },
    },
  });
}

/**
 * Render class distribution chart (Doughnut Chart)
 */
function renderClassDistributionChart(classDistribution) {
  const ctx = document.getElementById("classDistributionChart");

  if (classDistributionChart) {
    classDistributionChart.destroy();
  }

  const labels = classDistribution.map((c) => c.waste_class);
  const data = classDistribution.map((c) => c.count);

  // Generate colors
  const colors = generateColors(labels.length);

  classDistributionChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          data: data,
          backgroundColor: colors,
          borderColor: "#1e293b",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: "right",
          labels: {
            color: "#f1f5f9",
            padding: 15,
            font: { size: 12 },
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const label = context.label || "";
              const value = context.parsed || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((value / total) * 100).toFixed(1);
              return `${label}: ${value} (${percentage}%)`;
            },
          },
        },
      },
    },
  });
}

/**
 * Render daily stats chart (Bar Chart)
 */
function renderDailyStatsChart(dailyStats) {
  const ctx = document.getElementById("dailyStatsChart");

  if (dailyStatsChart) {
    dailyStatsChart.destroy();
  }

  const labels = dailyStats.map((d) => d.date);
  const counts = dailyStats.map((d) => d.count);
  const points = dailyStats.map((d) => d.total_points || 0);

  dailyStatsChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Detections",
          data: counts,
          backgroundColor: "rgba(16, 185, 129, 0.8)",
          borderColor: "#10b981",
          borderWidth: 1,
          yAxisID: "y",
        },
        {
          label: "Eco-Points",
          data: points,
          backgroundColor: "rgba(245, 158, 11, 0.8)",
          borderColor: "#f59e0b",
          borderWidth: 1,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          title: {
            display: true,
            text: "Detections",
            color: "#94a3b8",
          },
          ticks: { color: "#94a3b8" },
          grid: { color: "#334155" },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          title: {
            display: true,
            text: "Eco-Points",
            color: "#94a3b8",
          },
          ticks: { color: "#94a3b8" },
          grid: { drawOnChartArea: false },
        },
        x: {
          ticks: { color: "#94a3b8" },
          grid: { color: "#334155" },
        },
      },
      plugins: {
        legend: {
          labels: { color: "#f1f5f9" },
        },
      },
    },
  });
}

/**
 * Render confidence distribution chart (Bar Chart)
 */
function renderConfidenceChart(accuracyMetrics) {
  const ctx = document.getElementById("confidenceChart");

  if (confidenceChart) {
    confidenceChart.destroy();
  }

  const confDist = accuracyMetrics.confidence_distribution || [];
  const labels = confDist.map((c) => c.confidence_range);
  const data = confDist.map((c) => c.count);

  confidenceChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Number of Detections",
          data: data,
          backgroundColor: [
            "rgba(16, 185, 129, 0.8)",
            "rgba(59, 130, 246, 0.8)",
            "rgba(245, 158, 11, 0.8)",
            "rgba(239, 68, 68, 0.8)",
            "rgba(139, 92, 246, 0.8)",
            "rgba(236, 72, 153, 0.8)",
          ],
          borderColor: "#1e293b",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Count",
            color: "#94a3b8",
          },
          ticks: { color: "#94a3b8" },
          grid: { color: "#334155" },
        },
        x: {
          title: {
            display: true,
            text: "Confidence Range",
            color: "#94a3b8",
          },
          ticks: { color: "#94a3b8" },
          grid: { color: "#334155" },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });
}

/**
 * Render top classes list
 */
function renderTopClasses(topClasses) {
  const container = document.getElementById("topClassesList");
  container.innerHTML = "";

  if (!topClasses || topClasses.length === 0) {
    container.innerHTML =
      '<p style="color: var(--text-secondary);">No data available</p>';
    return;
  }

  topClasses.forEach((item, index) => {
    const classItem = document.createElement("div");
    classItem.className = "top-class-item";

    const rank = index + 1;
    const medal =
      rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : `${rank}.`;

    classItem.innerHTML = `
      <div class="class-rank">${medal}</div>
      <div class="class-info">
        <div class="class-name">${item.waste_class}</div>
        <div class="class-count">${item.count} detections</div>
      </div>
      <div class="class-confidence">${(item.avg_confidence * 100).toFixed(1)}% avg</div>
    `;

    container.appendChild(classItem);
  });
}

/**
 * Render recent detections table
 */
function renderRecentDetections(recentDetections) {
  const tbody = document.getElementById("detectionsTableBody");
  tbody.innerHTML = "";

  if (!recentDetections || recentDetections.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="5" style="text-align: center; color: var(--text-secondary);">No recent detections</td></tr>';
    return;
  }

  recentDetections.forEach((detection) => {
    const row = document.createElement("tr");

    const timestamp = new Date(detection.timestamp).toLocaleString();
    const confidence = (detection.confidence * 100).toFixed(1) + "%";

    row.innerHTML = `
      <td>${detection.id}</td>
      <td>${timestamp}</td>
      <td><span class="class-badge">${detection.waste_class}</span></td>
      <td>${confidence}</td>
      <td class="eco-points-cell">${detection.eco_points}</td>
    `;

    tbody.appendChild(row);
  });
}

/**
 * Generate distinct colors for charts
 */
function generateColors(count) {
  const colors = [
    "#10b981",
    "#3b82f6",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#ec4899",
    "#06b6d4",
    "#84cc16",
    "#f97316",
    "#14b8a6",
    "#6366f1",
    "#a855f7",
    "#f43f5e",
    "#22c55e",
    "#eab308",
  ];

  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length]);
  }
  return result;
}

/**
 * Handle reset analytics with confirmation
 */
async function handleResetAnalytics() {
  // Show confirmation dialog
  const confirmed = confirm(
    "⚠️ WARNING: This will permanently delete ALL analytics data!\n\n" +
      "This includes:\n" +
      "• All detection records\n" +
      "• All eco-points history\n" +
      "• All statistics and charts\n\n" +
      "This action CANNOT be undone!\n\n" +
      "Are you sure you want to reset all data?",
  );

  if (!confirmed) {
    showNotification("Reset cancelled", "info");
    return;
  }

  // Double confirmation for safety
  const doubleConfirm = confirm(
    "🚨 FINAL CONFIRMATION 🚨\n\n" +
      "Are you ABSOLUTELY SURE you want to delete all data?\n\n" +
      "Type 'YES' in your mind and click OK to proceed.",
  );

  if (!doubleConfirm) {
    showNotification("Reset cancelled", "info");
    return;
  }

  try {
    showNotification("Resetting all analytics data...", "info");

    // Call backend reset endpoint
    const response = await fetch(`${API_BASE_URL}/analytics/reset`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (data.success) {
      showNotification("✅ All analytics data has been reset!", "success");

      // Reload analytics after a short delay
      setTimeout(() => {
        loadAnalytics();
      }, 1000);
    } else {
      showNotification(
        `Failed to reset data: ${data.error || "Unknown error"}`,
        "error",
      );
    }
  } catch (error) {
    console.error("Error resetting analytics:", error);
    showNotification(
      "Network error. Please check if backend is running.",
      "error",
    );
  }
}

/**
 * Show notification toast
 */
function showNotification(message, type = "info") {
  notificationText.textContent = message;
  notification.className = "notification show";

  if (type === "error") {
    notification.classList.add("error");
  } else if (type === "success") {
    notification.classList.add("success");
  }

  setTimeout(() => {
    notification.classList.remove("show");
  }, 3000);
}

// Auto-refresh analytics every 60 seconds
setInterval(loadAnalytics, 60000);
