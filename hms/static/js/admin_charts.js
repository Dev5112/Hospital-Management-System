/**
 * Admin Dashboard Charts Initialization
 * Handles all chart setup and data fetching for admin dashboard
 */

let adminCharts = {};

/**
 * Initialize all admin dashboard charts and KPIs
 */
async function initializeAdminDashboard() {
    try {
        // Load KPI statistics
        await loadAdminKPIs();

        // Load all charts
        await initAppointmentsTrendChart();
        await initStatusBreakdownChart();
        await initSpecializationsChart();
        await initGenderChart();
        await initOccupancyChart();
        await initRevenueChart();
        await initAdmissionsTrendChart();
        await initDiagnosesChart();

        // Set up period toggle
        setupPeriodToggle();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showToast('Failed to load dashboard data', 'error');
    }
}

/**
 * Load admin KPI statistics
 */
async function loadAdminKPIs() {
    try {
        showLoading('appointmentsTrendChart');
        const data = await fetchChartData('/api/charts/admin/overview');

        countUp('kpiTotalDoctors', data.total_doctors, 1500);
        countUp('kpiTotalPatients', data.total_patients, 1500);
        countUp('kpiTodaysAppointments', data.todays_appointments, 1500);
        countUp('kpiTotalRevenue', data.total_revenue, 1500);

        hideLoading('appointmentsTrendChart');
    } catch (error) {
        console.error('Error loading KPIs:', error);
    }
}

/**
 * Initialize appointments trend chart with period selector
 */
async function initAppointmentsTrendChart() {
    try {
        showLoading('appointmentsTrendChart');
        const period = document.querySelector('.chart-control-btn.active')?.dataset.period || '30d';

        const data = await fetchChartData('/api/charts/admin/appointments-trend', { period });

        destroyChart('appointmentsTrendChart');

        const canvas = document.getElementById('appointmentsTrendChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'line',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                plugins: {
                    ...DEFAULT_CHART_OPTIONS.plugins,
                    filler: {
                        propagate: true
                    }
                },
                scales: {
                    ...DEFAULT_CHART_OPTIONS.scales,
                    y: {
                        ...DEFAULT_CHART_OPTIONS.scales.y,
                        beginAtZero: true
                    }
                }
            }
        });

        adminCharts['appointmentsTrendChart'] = chart;
        hideLoading('appointmentsTrendChart');
    } catch (error) {
        console.error('Error initializing appointments trend chart:', error);
        hideLoading('appointmentsTrendChart');
    }
}

/**
 * Initialize appointment status breakdown (doughnut) chart
 */
async function initStatusBreakdownChart() {
    try {
        showLoading('statusBreakdownChart');
        const data = await fetchChartData('/api/charts/admin/status-breakdown');

        destroyChart('statusBreakdownChart');

        const canvas = document.getElementById('statusBreakdownChart');
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

        adminCharts['statusBreakdownChart'] = chart;
        hideLoading('statusBreakdownChart');
    } catch (error) {
        console.error('Error initializing status breakdown chart:', error);
        hideLoading('statusBreakdownChart');
    }
}

/**
 * Initialize top specializations (horizontal bar) chart
 */
async function initSpecializationsChart() {
    try {
        showLoading('specializationsChart');
        const data = await fetchChartData('/api/charts/admin/specializations');

        destroyChart('specializationsChart');

        const canvas = document.getElementById('specializationsChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'bar',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                indexAxis: 'y',
                plugins: {
                    ...DEFAULT_CHART_OPTIONS.plugins,
                    legend: {
                        display: false
                    }
                }
            }
        });

        adminCharts['specializationsChart'] = chart;
        hideLoading('specializationsChart');
    } catch (error) {
        console.error('Error initializing specializations chart:', error);
        hideLoading('specializationsChart');
    }
}

/**
 * Initialize patient gender split (pie) chart
 */
async function initGenderChart() {
    try {
        showLoading('genderChart');
        const data = await fetchChartData('/api/charts/admin/gender');

        destroyChart('genderChart');

        const canvas = document.getElementById('genderChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'pie',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                plugins: {
                    ...DEFAULT_CHART_OPTIONS.plugins,
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        adminCharts['genderChart'] = chart;
        hideLoading('genderChart');
    } catch (error) {
        console.error('Error initializing gender chart:', error);
        hideLoading('genderChart');
    }
}

/**
 * Initialize bed occupancy by ward (radar) chart
 */
async function initOccupancyChart() {
    try {
        showLoading('occupancyChart');
        const data = await fetchChartData('/api/charts/admin/occupancy');

        destroyChart('occupancyChart');

        const canvas = document.getElementById('occupancyChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'radar',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { stepSize: 20 }
                    }
                }
            }
        });

        adminCharts['occupancyChart'] = chart;
        hideLoading('occupancyChart');
    } catch (error) {
        console.error('Error initializing occupancy chart:', error);
        hideLoading('occupancyChart');
    }
}

/**
 * Initialize monthly revenue (bar) chart
 */
async function initRevenueChart() {
    try {
        showLoading('revenueChart');
        const data = await fetchChartData('/api/charts/admin/revenue');

        destroyChart('revenueChart');

        const canvas = document.getElementById('revenueChart');
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
                    ...DEFAULT_CHART_OPTIONS.scales,
                    y: {
                        ...DEFAULT_CHART_OPTIONS.scales.y,
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₹' + (value / 100000).toFixed(1) + 'L';
                            }
                        }
                    }
                }
            }
        });

        adminCharts['revenueChart'] = chart;
        hideLoading('revenueChart');
    } catch (error) {
        console.error('Error initializing revenue chart:', error);
        hideLoading('revenueChart');
    }
}

/**
 * Initialize admissions vs discharges trend (multi-line) chart
 */
async function initAdmissionsTrendChart() {
    try {
        showLoading('admissionsTrendChart');
        const data = await fetchChartData('/api/charts/admin/admissions-trend');

        destroyChart('admissionsTrendChart');

        const canvas = document.getElementById('admissionsTrendChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'line',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                scales: {
                    ...DEFAULT_CHART_OPTIONS.scales,
                    y: {
                        ...DEFAULT_CHART_OPTIONS.scales.y,
                        beginAtZero: true
                    }
                }
            }
        });

        adminCharts['admissionsTrendChart'] = chart;
        hideLoading('admissionsTrendChart');
    } catch (error) {
        console.error('Error initializing admissions trend chart:', error);
        hideLoading('admissionsTrendChart');
    }
}

/**
 * Initialize top diagnoses (horizontal bar) chart
 */
async function initDiagnosesChart() {
    try {
        showLoading('diagnosesChart');
        const data = await fetchChartData('/api/charts/admin/diagnoses');

        destroyChart('diagnosesChart');

        const canvas = document.getElementById('diagnosesChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'bar',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                indexAxis: 'y',
                plugins: {
                    ...DEFAULT_CHART_OPTIONS.plugins,
                    legend: {
                        display: false
                    }
                }
            }
        });

        adminCharts['diagnosesChart'] = chart;
        hideLoading('diagnosesChart');
    } catch (error) {
        console.error('Error initializing diagnoses chart:', error);
        hideLoading('diagnosesChart');
    }
}

/**
 * Setup period toggle buttons for appointments trend chart
 */
function setupPeriodToggle() {
    document.querySelectorAll('.chart-control-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            // Update active state
            document.querySelectorAll('.chart-control-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');

            // Re-initialize chart with new period
            await initAppointmentsTrendChart();
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializeAdminDashboard);
