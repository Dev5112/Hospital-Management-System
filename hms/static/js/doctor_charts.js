/**
 * Doctor Dashboard Charts Initialization
 * Handles all chart setup and data fetching for doctor dashboard
 */

let doctorCharts = {};

/**
 * Initialize all doctor dashboard charts
 * @param {number} doctorId - The doctor's ID
 */
async function initializeDoctorDashboard(doctorId) {
    try {
        // Load charts with doctor_id parameter
        await initDoctorAppointmentDistribution(doctorId);
        await initDoctorStatusBreakdown(doctorId);
        await initDoctorWeeklyHeatmap(doctorId);
        await initDoctorMonthlyPatients(doctorId);
        await initDoctorTopDiagnoses(doctorId);
    } catch (error) {
        console.error('Error initializing doctor dashboard:', error);
        showToast('Failed to load dashboard data', 'error');
    }
}

/**
 * Initialize appointment distribution by day of week
 */
async function initDoctorAppointmentDistribution(doctorId) {
    try {
        showLoading('appointmentDistributionChart');
        const data = await fetchChartData('/api/charts/doctor/appointment-distribution', { doctor_id: doctorId });

        destroyChart('appointmentDistributionChart');

        const canvas = document.getElementById('appointmentDistributionChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'bar',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                plugins: {
                    ...DEFAULT_CHART_OPTIONS.plugins,
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        ...DEFAULT_CHART_OPTIONS.scales.y,
                        beginAtZero: true
                    }
                }
            }
        });

        doctorCharts['appointmentDistributionChart'] = chart;
        hideLoading('appointmentDistributionChart');
    } catch (error) {
        console.error('Error initializing appointment distribution chart:', error);
        hideLoading('appointmentDistributionChart');
    }
}

/**
 * Initialize doctor's appointment status breakdown
 */
async function initDoctorStatusBreakdown(doctorId) {
    try {
        showLoading('doctor-statusBreakdownChart');
        const data = await fetchChartData('/api/charts/doctor/status-breakdown', { doctor_id: doctorId });

        destroyChart('doctor-statusBreakdownChart');

        const canvas = document.getElementById('doctor-statusBreakdownChart');
        if (!canvas) return;

        // Calculate total for center text
        const total = data.datasets[0].data.reduce((a, b) => a + b, 0);

        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                plugins: {
                    ...DEFAULT_CHART_OPTIONS.plugins,
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        ...DEFAULT_CHART_OPTIONS.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed.y;
                            }
                        }
                    }
                }
            },
            plugins: [{
                id: 'centerText',
                beforeDatasetsDraw(chart) {
                    const width = chart.width;
                    const height = chart.height;
                    const ctx = chart.ctx;

                    ctx.restore();
                    const fontSize = (height / 200).toFixed(2);
                    ctx.font = fontSize + "em sans-serif";
                    ctx.textBaseline = "middle";
                    ctx.fillStyle = "#6B7280";

                    const text = total + " Total";
                    const textX = Math.round((width - ctx.measureText(text).width) / 2);
                    const textY = height / 2;

                    ctx.fillText(text, textX, textY);
                    ctx.save();
                }
            }]
        });

        doctorCharts['doctor-statusBreakdownChart'] = chart;
        hideLoading('doctor-statusBreakdownChart');
    } catch (error) {
        console.error('Error initializing status breakdown chart:', error);
        hideLoading('doctor-statusBreakdownChart');
    }
}

/**
 * Initialize weekly schedule heatmap
 */
async function initDoctorWeeklyHeatmap(doctorId) {
    try {
        showLoading('weeklyHeatmap');
        const heatmapData = await fetchChartData('/api/charts/doctor/weekly-heatmap', { doctor_id: doctorId });

        renderHeatmapTable(heatmapData);
        hideLoading('weeklyHeatmap');
    } catch (error) {
        console.error('Error initializing weekly heatmap:', error);
        hideLoading('weeklyHeatmap');
    }
}

/**
 * Render heatmap table from data
 */
function renderHeatmapTable(heatmapData) {
    const tableEl = document.getElementById('weeklyHeatmap');
    if (!tableEl) return;

    tableEl.innerHTML = '';

    const { days, hours, data, patients } = heatmapData;

    // Create header row
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    const emptyHeader = document.createElement('th');
    emptyHeader.textContent = 'Time';
    headerRow.appendChild(emptyHeader);

    days.forEach(day => {
        const th = document.createElement('th');
        th.textContent = day.substring(0, 3);
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    tableEl.appendChild(thead);

    // Create body rows
    const tbody = document.createElement('tbody');

    hours.forEach((hour, hourIndex) => {
        const row = document.createElement('tr');

        const timeCell = document.createElement('td');
        timeCell.innerHTML = `<strong>${hour}</strong>`;
        timeCell.style.background = '#f0f0f0';
        timeCell.style.textAlign = 'center';
        row.appendChild(timeCell);

        days.forEach((day, dayIndex) => {
            const cell = document.createElement('td');
            const isBooked = data[dayIndex][hourIndex] === 1;
            const patientId = patients[dayIndex][hourIndex];

            cell.className = `heatmap-cell ${isBooked ? 'booked' : 'available'}`;
            cell.innerHTML = isBooked ? '<i class="fas fa-user"></i>' : '';

            if (isBooked && patientId) {
                cell.innerHTML += `<div class="heatmap-tooltip">Patient #${patientId}</div>`;
            }

            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    tableEl.appendChild(tbody);
}

/**
 * Initialize doctor's monthly patient count
 */
async function initDoctorMonthlyPatients(doctorId) {
    try {
        showLoading('monthlyPatientsChart');
        const data = await fetchChartData('/api/charts/doctor/monthly-patients', { doctor_id: doctorId });

        destroyChart('monthlyPatientsChart');

        const canvas = document.getElementById('monthlyPatientsChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'line',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                plugins: {
                    ...DEFAULT_CHART_OPTIONS.plugins,
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        ...DEFAULT_CHART_OPTIONS.scales.y,
                        beginAtZero: true
                    }
                }
            }
        });

        doctorCharts['monthlyPatientsChart'] = chart;
        hideLoading('monthlyPatientsChart');
    } catch (error) {
        console.error('Error initializing monthly patients chart:', error);
        hideLoading('monthlyPatientsChart');
    }
}

/**
 * Initialize doctor's top diagnoses
 */
async function initDoctorTopDiagnoses(doctorId) {
    try {
        showLoading('topDiagnosesChart');
        const data = await fetchChartData('/api/charts/doctor/top-diagnoses', { doctor_id: doctorId });

        destroyChart('topDiagnosesChart');

        const canvas = document.getElementById('topDiagnosesChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                plugins: {
                    ...DEFAULT_CHART_OPTIONS.plugins,
                    legend: {
                        position: 'right'
                    }
                }
            }
        });

        doctorCharts['topDiagnosesChart'] = chart;
        hideLoading('topDiagnosesChart');
    } catch (error) {
        console.error('Error initializing top diagnoses chart:', error);
        hideLoading('topDiagnosesChart');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const doctorId = window.userData?.userId;
    if (doctorId) {
        initializeDoctorDashboard(doctorId);
    }
});
