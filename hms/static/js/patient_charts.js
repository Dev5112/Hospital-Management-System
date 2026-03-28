/**
 * Patient Dashboard Charts Initialization
 * Handles all chart setup and data fetching for patient dashboard
 */

let patientCharts = {};

/**
 * Initialize all patient dashboard charts
 * @param {number} patientId - The patient's ID
 */
async function initializePatientDashboard(patientId) {
    try {
        // Load KPIs and charts with patient_id parameter
        await loadPatientKPIs(patientId);
        await initPatientTreatmentTimeline(patientId);
        await initPatientBillingHistory(patientId);
        await initPatientVisitFrequency(patientId);
        await initPatientDiagnosisBreakdown(patientId);
        await initPatientAppointmentStatus(patientId);

        // Setup timeline filters
        setupTimelineFilters();
    } catch (error) {
        console.error('Error initializing patient dashboard:', error);
        showToast('Failed to load dashboard data', 'error');
    }
}

/**
 * Load patient KPI metrics
 */
async function loadPatientKPIs(patientId) {
    try {
        const data = await fetchChartData('/api/charts/patient/kpi', { patient_id: patientId });

        countUp('kpiTotalVisits', data.total_visits, 1500);
        countUp('kpiOutstandingBalance', data.outstanding_balance, 1500);

        const lastVisit = data.last_visit ? formatDate(data.last_visit, 'long') : 'N/A';
        document.getElementById('kpiLastVisit').textContent = lastVisit;
    } catch (error) {
        console.error('Error loading patient KPIs:', error);
    }
}

/**
 * Initialize patient treatment history timeline
 */
async function initPatientTreatmentTimeline(patientId) {
    try {
        const timelineData = await fetchChartData('/api/charts/patient/timeline', { patient_id: patientId });

        renderTimeline(timelineData.events);
    } catch (error) {
        console.error('Error initializing treatment timeline:', error);
    }
}

/**
 * Render timeline from events data
 */
function renderTimeline(events) {
    const timelineEl = document.getElementById('treatmentTimeline');
    if (!timelineEl) return;

    timelineEl.innerHTML = '';

    if (!events || events.length === 0) {
        timelineEl.innerHTML = '<li style="text-align: center; color: #999; padding: 2rem;">No events found</li>';
        return;
    }

    events.forEach(event => {
        const li = document.createElement('li');
        li.className = `timeline-item ${event.type}`;
        li.dataset.type = event.type;

        const dotClass = event.type === 'appointment' ? 'appointment' : 'admission';
        const statusBadgeClass = event.type === 'appointment'
            ? `timeline-badge ${event.status || 'scheduled'}`
            : `timeline-badge ${event.status || 'admitted'}`;

        let detailsHtml = '';
        if (event.type === 'appointment') {
            detailsHtml = `<div class="timeline-description">
                <strong>Doctor:</strong> ${event.doctor || 'N/A'}<br>
                <small>${event.description || 'Appointment'}</small>
            </div>`;
        } else {
            detailsHtml = `<div class="timeline-description">
                <strong>Ward:</strong> ${event.ward || 'N/A'}<br>
                <strong>Diagnosis:</strong> ${event.description || 'N/A'}<br>
                ${event.duration_days ? `<small>Duration: ${event.duration_days} day(s)</small>` : ''}
            </div>`;
        }

        li.innerHTML = `
            <div class="timeline-dot ${dotClass}"></div>
            <div class="timeline-content">
                <div class="timeline-date">${formatDate(event.date, 'long')}</div>
                <div class="timeline-title">${event.description}</div>
                ${detailsHtml}
                <span class="${statusBadgeClass}">${event.status ? event.status.toUpperCase() : 'N/A'}</span>
            </div>
        `;

        timelineEl.appendChild(li);
    });
}

/**
 * Setup timeline filter buttons
 */
function setupTimelineFilters() {
    document.querySelectorAll('.timeline-filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Update active state
            document.querySelectorAll('.timeline-filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');

            // Filter timeline
            const filterType = e.target.dataset.filter;
            filterTimeline(filterType);
        });
    });
}

/**
 * Filter timeline by type
 */
function filterTimeline(filterType) {
    document.querySelectorAll('.timeline-item').forEach(item => {
        if (filterType === 'all') {
            item.classList.remove('hidden');
        } else {
            item.classList.toggle('hidden', item.dataset.type !== filterType);
        }
    });
}

/**
 * Initialize patient billing history chart
 */
async function initPatientBillingHistory(patientId) {
    try {
        showLoading('billingHistoryChart');
        const data = await fetchChartData('/api/charts/patient/billing', { patient_id: patientId });

        destroyChart('billingHistoryChart');

        const canvas = document.getElementById('billingHistoryChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'line',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                scales: {
                    y: {
                        ...DEFAULT_CHART_OPTIONS.scales.y,
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatINR(value);
                            }
                        }
                    }
                }
            }
        });

        patientCharts['billingHistoryChart'] = chart;
        hideLoading('billingHistoryChart');
    } catch (error) {
        console.error('Error initializing billing history chart:', error);
        hideLoading('billingHistoryChart');
    }
}

/**
 * Initialize patient visit frequency chart
 */
async function initPatientVisitFrequency(patientId) {
    try {
        showLoading('visitFrequencyChart');
        const data = await fetchChartData('/api/charts/patient/visits', { patient_id: patientId });

        destroyChart('visitFrequencyChart');

        const canvas = document.getElementById('visitFrequencyChart');
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

        patientCharts['visitFrequencyChart'] = chart;
        hideLoading('visitFrequencyChart');
    } catch (error) {
        console.error('Error initializing visit frequency chart:', error);
        hideLoading('visitFrequencyChart');
    }
}

/**
 * Initialize patient diagnosis breakdown chart
 */
async function initPatientDiagnosisBreakdown(patientId) {
    try {
        showLoading('diagnosisBreakdownChart');
        const data = await fetchChartData('/api/charts/patient/diagnoses', { patient_id: patientId });

        destroyChart('diagnosisBreakdownChart');

        const canvas = document.getElementById('diagnosisBreakdownChart');
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

        patientCharts['diagnosisBreakdownChart'] = chart;
        hideLoading('diagnosisBreakdownChart');
    } catch (error) {
        console.error('Error initializing diagnosis breakdown chart:', error);
        hideLoading('diagnosisBreakdownChart');
    }
}

/**
 * Initialize patient appointment status chart
 * Note: This could be implemented as a stacked bar based on available data
 */
async function initPatientAppointmentStatus(patientId) {
    try {
        showLoading('appointmentStatusChart');

        // For now, we'll create a simple chart from available data
        // In production, you might fetch additional data or calculate from existing data
        const data = {
            labels: ['Q1', 'Q2', 'Q3', 'Q4'],
            datasets: [
                {
                    label: 'Completed',
                    data: [0, 0, 0, 0],
                    backgroundColor: 'rgba(34, 197, 94, 0.7)',
                    borderColor: 'rgb(34, 197, 94)',
                    borderWidth: 1
                },
                {
                    label: 'Scheduled',
                    data: [0, 0, 0, 0],
                    backgroundColor: 'rgba(79, 156, 249, 0.7)',
                    borderColor: 'rgb(79, 156, 249)',
                    borderWidth: 1
                },
                {
                    label: 'Cancelled',
                    data: [0, 0, 0, 0],
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    borderColor: 'rgb(239, 68, 68)',
                    borderWidth: 1
                }
            ]
        };

        destroyChart('appointmentStatusChart');

        const canvas = document.getElementById('appointmentStatusChart');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'bar',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }
        });

        patientCharts['appointmentStatusChart'] = chart;
        hideLoading('appointmentStatusChart');
    } catch (error) {
        console.error('Error initializing appointment status chart:', error);
        hideLoading('appointmentStatusChart');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const patientId = window.userData?.userId;
    if (patientId) {
        initializePatientDashboard(patientId);
    }
});
