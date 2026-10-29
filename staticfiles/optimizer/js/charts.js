/**
 * Charts module using Chart.js
 * Visualizes Genetic Algorithm convergence history and route distance comparisons.
 * Dynamically adapts typography, contrast, and colors to Dark and Light glassmorphic themes.
 */

let convergenceChartInstance = null;
let comparisonChartInstance = null;

function getChartThemeColors() {
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  if (isLight) {
    return {
      textColor: '#1e293b',
      mutedText: '#475569',
      gridColor: 'rgba(14, 165, 233, 0.12)',
      tooltipBg: 'rgba(255, 255, 255, 0.96)',
      tooltipText: '#0f172a',
      tooltipBorder: 'rgba(2, 132, 199, 0.35)',
      primaryLine: '#0284c7',
      primaryGradientTop: 'rgba(2, 132, 199, 0.3)',
      avgLine: 'rgba(100, 116, 139, 0.7)'
    };
  } else {
    return {
      textColor: '#cbd5e1',
      mutedText: '#94a3b8',
      gridColor: 'rgba(56, 189, 248, 0.08)',
      tooltipBg: 'rgba(11, 20, 38, 0.95)',
      tooltipText: '#ffffff',
      tooltipBorder: 'rgba(0, 240, 255, 0.35)',
      primaryLine: '#00f0ff',
      primaryGradientTop: 'rgba(0, 240, 255, 0.35)',
      avgLine: 'rgba(148, 163, 184, 0.5)'
    };
  }
}

function renderConvergenceChart(historyData) {
  const canvas = document.getElementById('convergenceChart');
  if (!canvas || !historyData || historyData.length === 0) return;

  const ctx = canvas.getContext('2d');
  if (convergenceChartInstance) {
    convergenceChartInstance.destroy();
  }

  const colors = getChartThemeColors();

  // Downsample if generations count is large for crisp rendering
  let displayData = historyData;
  if (historyData.length > 300) {
    const step = Math.ceil(historyData.length / 150);
    displayData = historyData.filter((_, idx) => idx % step === 0 || idx === historyData.length - 1);
  }

  const labels = displayData.map(d => d.generation);
  const bestValues = displayData.map(d => d.best_distance);
  const avgValues = displayData.map(d => d.average_distance || d.best_distance);

  // Gradient fill for line
  const gradient = ctx.createLinearGradient(0, 0, 0, 250);
  gradient.addColorStop(0, colors.primaryGradientTop);
  gradient.addColorStop(1, 'rgba(0, 240, 255, 0.0)');

  convergenceChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Best Tour Distance (km)',
          data: bestValues,
          borderColor: colors.primaryLine,
          backgroundColor: gradient,
          fill: true,
          tension: 0.25,
          borderWidth: 2.5,
          pointRadius: displayData.length > 60 ? 0 : 2,
          pointHoverRadius: 5,
        },
        {
          label: 'Population Average (km)',
          data: avgValues,
          borderColor: colors.avgLine,
          borderDash: [4, 4],
          borderWidth: 1.5,
          fill: false,
          tension: 0.2,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: colors.textColor, font: { size: 11 } }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: colors.tooltipBg,
          titleColor: colors.primaryLine,
          bodyColor: colors.tooltipText,
          borderColor: colors.tooltipBorder,
          borderWidth: 1
        }
      },
      scales: {
        x: {
          title: { display: true, text: 'Generation', color: colors.mutedText, font: { size: 11 } },
          ticks: { color: colors.mutedText, maxTicksLimit: 10 },
          grid: { color: colors.gridColor }
        },
        y: {
          title: { display: true, text: 'Distance (km)', color: colors.mutedText, font: { size: 11 } },
          ticks: { color: colors.mutedText },
          grid: { color: colors.gridColor }
        }
      }
    }
  });
}

function renderComparisonChart(initialDist, optDist, savedDist) {
  const canvas = document.getElementById('comparisonChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (comparisonChartInstance) {
    comparisonChartInstance.destroy();
  }

  const colors = getChartThemeColors();

  comparisonChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Initial Route', 'Optimized Route', 'Saved Km'],
      datasets: [{
        label: 'Distance (km)',
        data: [initialDist, optDist, savedDist],
        backgroundColor: [
          'rgba(239, 68, 68, 0.78)',   // Red
          'rgba(16, 185, 129, 0.78)',  // Emerald Green
          colors.primaryLine           // Theme Accent
        ],
        borderColor: [
          '#ef4444',
          '#10b981',
          colors.primaryLine
        ],
        borderWidth: 1.5,
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: colors.tooltipBg,
          bodyColor: colors.tooltipText,
          borderColor: colors.tooltipBorder,
          borderWidth: 1
        }
      },
      scales: {
        x: {
          ticks: { color: colors.textColor },
          grid: { display: false }
        },
        y: {
          title: { display: true, text: 'Total Kilometers', color: colors.mutedText, font: { size: 11 } },
          ticks: { color: colors.mutedText },
          grid: { color: colors.gridColor }
        }
      }
    }
  });
}
