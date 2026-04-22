/* ============================================
   IOT DATA AGGREGATION - FRONTEND APPLICATION
   ============================================ */

// Configuration
const API_BASE_URL = window.IOT_API_BASE_URL || '/api';
const AUTO_REFRESH_INTERVAL = 5000; // 5 seconds

// Global State
let appState = {
  currentSection: 'dashboard',
  autoRefresh: true,
  refreshInterval: null,
  allData: [],
  charts: {},
};

// ============================================
// DOM INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  initializeEventListeners();
  switchToSection('dashboard');
  loadDashboardData();
  setupAutoRefresh();
});

function initializeEventListeners() {
  // Navigation
  document.querySelectorAll('.nav-link').forEach((link) => {
    link.addEventListener('click', (e) => {
      const section = e.target.dataset.section;
      switchToSection(section);
    });
  });

  // Controls
  document.getElementById('refreshBtn').addEventListener('click', refreshCurrentSection);
  document.getElementById('autoRefreshToggle').addEventListener('change', toggleAutoRefresh);

  // Form Submission
  document.getElementById('dataForm').addEventListener('submit', (e) => {
    e.preventDefault();
    submitSensorData();
  });

  // Data Type Toggle
  document.getElementById('dataType').addEventListener('change', (e) => {
    const manualInput = document.getElementById('manualInput');
    const fileInput = document.getElementById('fileInput');
    if (e.target.value === 'manual') {
      manualInput.style.display = 'block';
      fileInput.style.display = 'none';
      document.getElementById('values').required = true;
      document.getElementById('csvFile').required = false;
    } else {
      manualInput.style.display = 'none';
      fileInput.style.display = 'block';
      document.getElementById('values').required = false;
      document.getElementById('csvFile').required = true;
    }
  });

  // File Upload
  const csvFile = document.getElementById('csvFile');
  const fileUpload = document.querySelector('.file-upload');
  fileUpload.addEventListener('click', () => csvFile.click());
  fileUpload.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUpload.style.background = 'rgba(0, 212, 255, 0.2)';
  });
  fileUpload.addEventListener('dragleave', () => {
    fileUpload.style.background = '';
  });
  fileUpload.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUpload.style.background = '';
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      csvFile.files = files;
      updateFileUploadLabel(files[0].name);
    }
  });

  // Analytics
  document.getElementById('searchSummaryBtn').addEventListener('click', searchSummary);
  document.getElementById('summarySearchId').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchSummary();
  });

  // History
  document.getElementById('statusFilter').addEventListener('change', loadHistoryData);
  document.getElementById('exportBtn').addEventListener('click', exportData);

  // Values Input Preview
  document.getElementById('values').addEventListener('input', updatePreview);
}

// ============================================
// SECTION NAVIGATION
// ============================================

function switchToSection(sectionId) {
  // Hide all sections
  document.querySelectorAll('.section').forEach((section) => {
    section.classList.remove('active');
  });

  // Show selected section
  const selectedSection = document.getElementById(`${sectionId}-section`);
  if (selectedSection) {
    selectedSection.classList.add('active');
  }

  // Update nav links
  document.querySelectorAll('.nav-link').forEach((link) => {
    link.classList.toggle('active', link.dataset.section === sectionId);
  });

  appState.currentSection = sectionId;

  // Load section-specific data
  switch (sectionId) {
    case 'dashboard':
      loadDashboardData();
      break;
    case 'analytics':
      loadAnalyticsData();
      break;
    case 'history':
      loadHistoryData();
      break;
  }
}

// ============================================
// DASHBOARD
// ============================================

async function loadDashboardData() {
  try {
    showSpinner(true);
    const data = await fetchFromAPI('/list');
    appState.allData = data.data || [];

    updateStatistics();
    updateActivityFeed();
    renderCharts();
  } catch (error) {
    showToast('Error loading dashboard data', error.message, 'error');
  } finally {
    showSpinner(false);
  }
}

function updateStatistics() {
  const data = appState.allData;

  const stats = {
    total: data.length,
    pending: data.filter((d) => d.status === 'pending').length,
    processing: data.filter((d) => d.status === 'processing').length,
    done: data.filter((d) => d.status === 'done').length,
    failed: data.filter((d) => d.status === 'failed').length,
  };

  document.getElementById('totalSubmissions').textContent = stats.total;
  document.getElementById('processingCount').textContent =
    stats.processing + stats.pending;
  document.getElementById('completedCount').textContent = stats.done;
  document.getElementById('failedCount').textContent = stats.failed;
}

function updateActivityFeed() {
  const activityList = document.getElementById('activityList');
  const data = appState.allData.slice(-10).reverse();

  if (data.length === 0) {
    activityList.innerHTML = '<div class="empty-state">No data available. Submit sensor data to get started.</div>';
    return;
  }

  activityList.innerHTML = data
    .map(
      (item) => `
    <div class="activity-item">
      <div class="activity-time">${formatTime(item.timestamp)}</div>
      <div class="activity-text">
        <strong>${item.sensor_id}</strong> • ${truncateId(item.data_id)}
      </div>
      <span class="activity-status ${getStatusClass(item.status)}">${item.status}</span>
    </div>
  `
    )
    .join('');
}

function renderCharts() {
  renderStatusChart();
  renderSubmissionsChart();
}

function renderStatusChart() {
  const ctx = document.getElementById('statusChart')?.getContext('2d');
  if (!ctx) return;

  const data = appState.allData;
  const statuses = {
    pending: data.filter((d) => d.status === 'pending').length,
    processing: data.filter((d) => d.status === 'processing').length,
    done: data.filter((d) => d.status === 'done').length,
    failed: data.filter((d) => d.status === 'failed').length,
  };

  if (appState.charts.statusChart) {
    appState.charts.statusChart.destroy();
  }

  appState.charts.statusChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Pending', 'Processing', 'Done', 'Failed'],
      datasets: [
        {
          data: [
            statuses.pending,
            statuses.processing,
            statuses.done,
            statuses.failed,
          ],
          backgroundColor: [
            '#f59e0b',
            '#00d4ff',
            '#10b981',
            '#ef4444',
          ],
          borderColor: '#1e293b',
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          labels: {
            color: '#cbd5e1',
            font: {
              size: 12,
              weight: '600',
            },
          },
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.8)',
          titleColor: '#00d4ff',
          bodyColor: '#cbd5e1',
          borderColor: '#00d4ff',
          borderWidth: 1,
        },
      },
    },
  });
}

function renderSubmissionsChart() {
  const ctx = document.getElementById('submissionsChart')?.getContext('2d');
  if (!ctx) return;

  // Group data by hour of submission
  const hourlyData = Array(24).fill(0);
  appState.allData.forEach((item) => {
    const date = new Date(item.timestamp);
    const hour = date.getHours();
    hourlyData[hour]++;
  });

  if (appState.charts.submissionsChart) {
    appState.charts.submissionsChart.destroy();
  }

  appState.charts.submissionsChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: Array.from({ length: 24 }, (_, i) => `${i}:00`),
      datasets: [
        {
          label: 'Submissions',
          data: hourlyData,
          borderColor: '#00d4ff',
          backgroundColor: 'rgba(0, 212, 255, 0.1)',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#00d4ff',
          pointBorderColor: '#1e293b',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          labels: {
            color: '#cbd5e1',
          },
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.8)',
          titleColor: '#00d4ff',
          bodyColor: '#cbd5e1',
          borderColor: '#00d4ff',
          borderWidth: 1,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            color: '#cbd5e1',
          },
          grid: {
            color: '#334155',
          },
        },
        x: {
          ticks: {
            color: '#cbd5e1',
          },
          grid: {
            color: '#334155',
          },
        },
      },
    },
  });
}

// ============================================
// SUBMIT DATA
// ============================================

async function submitSensorData() {
  try {
    const sensorId = document.getElementById('sensorId').value.trim();
    const dataType = document.getElementById('dataType').value;

    if (!sensorId) {
      showToast('Validation Error', 'Sensor ID is required', 'error');
      return;
    }

    showSpinner(true);

    let payload;
    if (dataType === 'manual') {
      const valuesStr = document.getElementById('values').value.trim();
      if (!valuesStr) {
        throw new Error('Please enter sensor values');
      }

      const values = valuesStr
        .split(',')
        .map((v) => parseFloat(v.trim()))
        .filter((v) => !isNaN(v));

      if (values.length === 0) {
        throw new Error('No valid numeric values found');
      }

      payload = { sensor_id: sensorId, values };
    } else {
      const file = document.getElementById('csvFile').files[0];
      if (!file) {
        throw new Error('Please select a file');
      }

      const content = await file.text();
      let values = [];

      if (file.name.endsWith('.json')) {
        const json = JSON.parse(content);
        values = Array.isArray(json)
          ? json.map((v) => (typeof v === 'number' ? v : parseFloat(v)))
          : json.values || [];
      } else {
        values = content
          .split('\n')
          .filter((line) => line.trim())
          .map((line) => parseFloat(line.trim()))
          .filter((v) => !isNaN(v));
      }

      if (values.length === 0) {
        throw new Error('No valid numeric values found in file');
      }

      payload = { sensor_id: sensorId, values };
    }

    const response = await fetchFromAPI('/data', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    const result = response.data;

    const resultContainer = document.getElementById('submitResult');
    resultContainer.innerHTML = `
      <div class="result-json result-success">
        <strong>✓ Success!</strong><br/>
        Data ID: <code>${result.data_id}</code><br/>
        Status: <strong>${result.status}</strong>
      </div>
    `;
    resultContainer.classList.add('active');

    showToast('Success', 'Sensor data submitted for processing!', 'success');

    // Reset form
    document.getElementById('dataForm').reset();
    document.getElementById('previewData').innerHTML =
      '<div class="empty-state">Enter values to see preview</div>';

    // Refresh data after a short delay
    setTimeout(loadDashboardData, 1000);
  } catch (error) {
    const resultContainer = document.getElementById('submitResult');
    resultContainer.innerHTML = `
      <div class="result-json result-error">
        <strong>✗ Error</strong><br/>
        ${error.message}
      </div>
    `;
    resultContainer.classList.add('active');
    showToast('Submission Failed', error.message, 'error');
  } finally {
    showSpinner(false);
  }
}

function updatePreview() {
  const values = document.getElementById('values').value
    .split(',')
    .map((v) => parseFloat(v.trim()))
    .filter((v) => !isNaN(v));

  const previewData = document.getElementById('previewData');

  if (values.length === 0) {
    previewData.innerHTML =
      '<div class="empty-state">Enter values to see preview</div>';
    return;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const avg = (values.reduce((a, b) => a + b) / values.length).toFixed(2);

  previewData.innerHTML = `
    <div>
      <strong>Values Entered:</strong> ${values.length}<br/>
      ${values.map((v) => `<div class="preview-value">${v}</div>`).join('')}
    </div>
    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
      <strong>Preview Statistics:</strong><br/>
      Min: <span style="color: var(--primary-color);">${min}</span><br/>
      Max: <span style="color: var(--primary-color);">${max}</span><br/>
      Avg: <span style="color: var(--primary-color);">${avg}</span>
    </div>
  `;
}

function updateFileUploadLabel(fileName) {
  const label = document.querySelector('.file-upload-label span');
  label.textContent = fileName;
}

// ============================================
// ANALYTICS
// ============================================

async function loadAnalyticsData() {
  try {
    showSpinner(true);
    const data = await fetchFromAPI('/list');
    const completed = (data.data || []).filter((d) => d.status === 'done');
    renderSummaries(completed);
  } catch (error) {
    showToast('Error loading analytics', error.message, 'error');
  } finally {
    showSpinner(false);
  }
}

async function searchSummary() {
  try {
    const dataId = document.getElementById('summarySearchId').value.trim();
    if (!dataId) {
      showToast('Validation Error', 'Please enter a Data ID', 'error');
      return;
    }

    showSpinner(true);
    const response = await fetchFromAPI(`/summary?id=${encodeURIComponent(dataId)}`);
    renderSummaries([response.data]);
  } catch (error) {
    showToast('Error searching summary', error.message, 'error');
  } finally {
    showSpinner(false);
  }
}

function renderSummaries(summaries) {
  const container = document.getElementById('summaryResult');

  if (summaries.length === 0) {
    container.innerHTML = '<div class="empty-state">No completed summaries found</div>';
    return;
  }

  container.innerHTML = summaries
    .map(
      (item) => `
    <div class="summary-card">
      <div class="summary-header">
        <div>
          <div class="summary-id">${item.data_id}</div>
          <div class="summary-sensor">${item.sensor_id}</div>
        </div>
        <span class="summary-status ${getStatusClass(item.status)}">${item.status}</span>
      </div>
      <div class="summary-stats">
        ${
          item.summary
            ? `
          <div class="stat-item">
            <div class="stat-label">Min Value</div>
            <div class="stat-value-lg">${item.summary.min?.toFixed(2) || 'N/A'}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Max Value</div>
            <div class="stat-value-lg">${item.summary.max?.toFixed(2) || 'N/A'}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Average</div>
            <div class="stat-value-lg">${item.summary.avg?.toFixed(2) || 'N/A'}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Count</div>
            <div class="stat-value-lg">${item.summary.count || 'N/A'}</div>
          </div>
        `
            : '<div class="empty-state">Summary not yet available</div>'
        }
      </div>
      <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color); font-size: 0.85rem; color: var(--text-tertiary);">
        Submitted: ${formatTime(item.timestamp)}
      </div>
    </div>
  `
    )
    .join('');
}

// ============================================
// HISTORY
// ============================================

async function loadHistoryData() {
  try {
    showSpinner(true);
    const data = await fetchFromAPI('/list');
    let records = data.data || [];

    // Filter by status
    const statusFilter = document.getElementById('statusFilter').value;
    if (statusFilter) {
      records = records.filter((r) => r.status === statusFilter);
    }

    // Sort by timestamp descending
    records.sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    renderHistoryTable(records);
  } catch (error) {
    showToast('Error loading history', error.message, 'error');
  } finally {
    showSpinner(false);
  }
}

function renderHistoryTable(records) {
  const tbody = document.getElementById('historyTableBody');

  if (records.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="6" class="text-center">No records found</td></tr>';
    return;
  }

  tbody.innerHTML = records
    .map(
      (record) => `
    <tr>
      <td class="data-id-cell" title="${record.data_id}">${truncateId(record.data_id)}</td>
      <td>${record.sensor_id}</td>
      <td><span class="summary-status ${getStatusClass(record.status)}">${record.status}</span></td>
      <td>${formatDateTime(record.timestamp)}</td>
      <td>
        ${
          record.summary
            ? `
          <div style="font-size: 0.85rem;">
            Min: ${record.summary.min?.toFixed(2)} | 
            Max: ${record.summary.max?.toFixed(2)} | 
            Avg: ${record.summary.avg?.toFixed(2)}
          </div>
        `
            : '<span style="color: var(--text-tertiary);">Pending</span>'
        }
      </td>
      <td>
        <div class="table-actions">
          <button class="btn btn-small btn-secondary" onclick="viewDetailSummary('${record.data_id}')">
            View Summary
          </button>
        </div>
      </td>
    </tr>
  `
    )
    .join('');
}

function viewDetailSummary(dataId) {
  switchToSection('analytics');
  document.getElementById('summarySearchId').value = dataId;
  searchSummary();
}

function exportData() {
  try {
    const records = appState.allData;
    const csv = [
      ['Data ID', 'Sensor ID', 'Status', 'Timestamp', 'Min', 'Max', 'Avg', 'Count'],
      ...records.map((r) => [
        r.data_id,
        r.sensor_id,
        r.status,
        r.timestamp,
        r.summary?.min || '',
        r.summary?.max || '',
        r.summary?.avg || '',
        r.summary?.count || '',
      ]),
    ]
      .map((row) => row.map((cell) => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `iot-data-export-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    showToast('Success', 'Data exported to CSV', 'success');
  } catch (error) {
    showToast('Export Failed', error.message, 'error');
  }
}

// ============================================
// API UTILITIES
// ============================================

async function fetchFromAPI(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...((options.headers) || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || `HTTP Error: ${response.status}`);
  }

  // Normalize response format
  if (!data.hasOwnProperty('data')) {
    return { data };
  }

  return data;
}

// ============================================
// AUTO REFRESH
// ============================================

function setupAutoRefresh() {
  if (appState.autoRefresh) {
    appState.refreshInterval = setInterval(refreshCurrentSection, AUTO_REFRESH_INTERVAL);
  }
}

function toggleAutoRefresh(e) {
  appState.autoRefresh = e.target.checked;

  if (appState.refreshInterval) {
    clearInterval(appState.refreshInterval);
  }

  if (appState.autoRefresh) {
    setupAutoRefresh();
    showToast('Auto-refresh enabled', 'Data will refresh every 5 seconds', 'success');
  } else {
    showToast('Auto-refresh disabled', 'Manual refresh only', 'warning');
  }
}

function refreshCurrentSection() {
  switch (appState.currentSection) {
    case 'dashboard':
      loadDashboardData();
      break;
    case 'analytics':
      loadAnalyticsData();
      break;
    case 'history':
      loadHistoryData();
      break;
  }
}

// ============================================
// UI HELPERS
// ============================================

function showSpinner(show) {
  const spinner = document.getElementById('loadingSpinner');
  if (show) {
    spinner.classList.add('active');
  } else {
    spinner.classList.remove('active');
  }
}

function showToast(title, message, type = 'info') {
  const container = document.getElementById('toastContainer');

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </button>
  `;

  container.appendChild(toast);

  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => {
    toast.remove();
  });

  // Auto-remove after 5 seconds
  setTimeout(() => {
    toast.remove();
  }, 5000);
}

function truncateId(id) {
  return id.substring(0, 8) + '...' + id.substring(id.length - 8);
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;

  return date.toLocaleDateString();
}

function formatDateTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

function getStatusClass(status) {
  switch (status) {
    case 'pending':
      return 'status-pending';
    case 'processing':
      return 'status-processing';
    case 'done':
      return 'status-done';
    case 'failed':
      return 'status-failed';
    default:
      return '';
  }
}

