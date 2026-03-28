/**
 * Shared chart utilities and helpers for HMS dashboards
 */

// ============================================================================
// CONFIGURATION & CONSTANTS
// ============================================================================

const HMS_COLORS = {
    primary: "#4F9CF9",
    success: "#22C55E",
    danger: "#EF4444",
    warning: "#F59E0B",
    purple: "#A855F7",
    navy: "#1E293B",
    lightGray: "#F8FAFC",
    darkGray: "#DBDFE6",
    palette: ["#4F9CF9", "#22C55E", "#F59E0B", "#EF4444", "#A855F7", "#14B8A6", "#F97316", "#EC4899"]
};

const DEFAULT_CHART_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: "bottom",
            labels: {
                usePointStyle: true,
                padding: 15,
                font: { size: 12, family: 'Inter, sans-serif' }
            }
        },
        tooltip: {
            mode: "index",
            intersect: false,
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            titleFont: { size: 13, weight: 'bold' },
            bodyFont: { size: 12 },
            padding: 12,
            cornerRadius: 8
        }
    },
    scales: {
        x: {
            grid: { display: false },
            ticks: { font: { size: 11 } }
        },
        y: {
            grid: { color: "rgba(0, 0, 0, 0.05)" },
            ticks: { font: { size: 11 } }
        }
    }
};

// ============================================================================
// API & FETCH UTILITIES
// ============================================================================

/**
 * Fetch chart data from API with authentication
 * @param {string} endpoint - API endpoint path
 * @param {object} params - URL query parameters
 * @returns {Promise<object>} - Chart data or throws error
 */
async function fetchChartData(endpoint, params = {}) {
    try {
        const url = new URL(endpoint, window.location.origin);

        // Add query parameters
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });

        // Get token from localStorage
        const token = localStorage.getItem('authToken');
        const headers = {
            'Content-Type': 'application/json'
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(url.toString(), { headers });

        if (!response.ok) {
            if (response.status === 401) {
                // Token expired - redirect to login
                window.location.href = '/login';
                throw new Error('Session expired. Please login again.');
            }
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        const jsonData = await response.json();

        if (jsonData.status === 'error') {
            throw new Error(jsonData.message || 'API Error');
        }

        return jsonData.data;
    } catch (error) {
        console.error('Fetch error:', error);
        showToast(`Error loading data: ${error.message}`, 'error');
        throw error;
    }
}

// ============================================================================
// FORMATTING UTILITIES
// ============================================================================

/**
 * Format number as Indian Rupees with commas
 * @param {number} amount - Amount to format
 * @returns {string} - Formatted string like "₹1,24,500"
 */
function formatINR(amount) {
    if (amount === null || amount === undefined) return '₹0';

    const num = Math.abs(Math.round(amount));
    let result = '';

    // Handle first 3 digits from right
    let remainder = num % 100;
    result = remainder < 10 ? '0' + remainder : remainder;

    // Handle remaining digits with commas every 2 digits
    let quotient = Math.floor(num / 100);
    while (quotient > 0) {
        remainder = quotient % 100;
        result = (remainder < 10 ? '0' + remainder : remainder) + ',' + result;
        quotient = Math.floor(quotient / 100);
    }

    // Handle sign
    const sign = amount < 0 ? '-' : '';
    return `${sign}₹${result}`;
}

/**
 * Format date string to readable format
 * @param {string} dateStr - ISO date string
 * @param {string} format - Format type: 'short', 'long', 'time'
 * @returns {string} - Formatted date
 */
function formatDate(dateStr, format = 'short') {
    if (!dateStr) return '-';

    const date = new Date(dateStr);
    const options = {
        short: { year: '2-digit', month: '2-digit', day: '2-digit' },
        long: { year: 'numeric', month: 'long', day: 'numeric' },
        time: { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }
    };

    return date.toLocaleString('en-IN', options[format] || options.short);
}

/**
 * Get month name from month number
 * @param {number} month - Month number (1-12)
 * @returns {string} - Month name
 */
function getMonthName(month) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[month - 1] || '';
}

// ============================================================================
// ANIMATION UTILITIES
// ============================================================================

/**
 * Animate number count-up from 0 to target value
 * @param {string} elementId - ID of element to update
 * @param {number} target - Target value
 * @param {number} duration - Animation duration in ms
 */
function countUp(elementId, target, duration = 1500) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const start = 0;
    const increment = target / (duration / 16); // 60fps
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }

        if (element.classList.contains('currency')) {
            element.textContent = formatINR(Math.round(current));
        } else {
            element.textContent = Math.round(current).toLocaleString('en-IN');
        }
    }, 16);
}

/**
 * Show loading spinner overlay on chart container
 * @param {string} canvasId - ID of canvas element
 */
function showLoading(canvasId) {
    const container = document.getElementById(canvasId)?.parentElement;
    if (!container) return;

    const spinner = document.createElement('div');
    spinner.className = 'chart-loading';
    spinner.innerHTML = '<div class="spinner"></div>';
    container.style.position = 'relative';
    container.appendChild(spinner);
}

/**
 * Hide loading spinner
 * @param {string} canvasId - ID of canvas element
 */
function hideLoading(canvasId) {
    const container = document.getElementById(canvasId)?.parentElement;
    if (!container) return;

    const spinner = container.querySelector('.chart-loading');
    if (spinner) spinner.remove();
}

// ============================================================================
// CHART MANAGEMENT UTILITIES
// ============================================================================

// Global chart instances storage
const chartInstances = {};

/**
 * Destroy existing chart before creating new one
 * @param {string} chartId - ID of chart instance
 */
function destroyChart(chartId) {
    if (chartInstances[chartId]) {
        chartInstances[chartId].destroy();
        delete chartInstances[chartId];
    }
}

/**
 * Store chart instance for later reference
 * @param {string} chartId - Unique chart ID
 * @param {Chart} instance - Chart.js instance
 */
function storeChart(chartId, instance) {
    chartInstances[chartId] = instance;
}

/**
 * Retrieve stored chart instance
 * @param {string} chartId - Chart ID
 * @returns {Chart|null} - Chart instance or null
 */
function getChart(chartId) {
    return chartInstances[chartId] || null;
}

/**
 * Create a line chart
 * @param {string} canvasId - Canvas element ID
 * @param {object} chartData - Chart.js compatible data object
 * @param {string} chartId - Unique chart identifier for storage
 * @returns {Chart} - Chart.js instance
 */
function createLineChart(canvasId, chartData, chartId) {
    destroyChart(chartId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas element ${canvasId} not found`);
        return null;
    }

    const config = {
        type: 'line',
        data: chartData,
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
    };

    const chart = new Chart(canvas, config);
    storeChart(chartId, chart);
    return chart;
}

/**
 * Create a bar chart
 * @param {string} canvasId - Canvas element ID
 * @param {object} chartData - Chart.js compatible data object
 * @param {string} chartId - Unique chart identifier
 * @param {boolean} indexAxis - Set to 'y' for horizontal bars
 * @returns {Chart} - Chart.js instance
 */
function createBarChart(canvasId, chartData, chartId, indexAxis = 'x') {
    destroyChart(chartId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const config = {
        type: 'bar',
        data: chartData,
        options: {
            ...DEFAULT_CHART_OPTIONS,
            indexAxis: indexAxis,
            scales: {
                x: indexAxis === 'y' ? {} : DEFAULT_CHART_OPTIONS.scales.x,
                y: indexAxis === 'y' ? {} : DEFAULT_CHART_OPTIONS.scales.y
            }
        }
    };

    const chart = new Chart(canvas, config);
    storeChart(chartId, chart);
    return chart;
}

/**
 * Create a pie/doughnut chart
 * @param {string} canvasId - Canvas element ID
 * @param {object} chartData - Chart.js compatible data object
 * @param {string} chartId - Unique chart identifier
 * @param {string} type - 'pie' or 'doughnut'
 * @returns {Chart} - Chart.js instance
 */
function createPieChart(canvasId, chartData, chartId, type = 'doughnut') {
    destroyChart(chartId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const config = {
        type: type,
        data: chartData,
        options: {
            ...DEFAULT_CHART_OPTIONS,
            plugins: {
                ...DEFAULT_CHART_OPTIONS.plugins,
                legend: {
                    position: 'right',
                    labels: DEFAULT_CHART_OPTIONS.plugins.legend.labels
                }
            }
        }
    };

    const chart = new Chart(canvas, config);
    storeChart(chartId, chart);
    return chart;
}

/**
 * Create a radar chart
 * @param {string} canvasId - Canvas element ID
 * @param {object} chartData - Chart.js compatible data object
 * @param {string} chartId - Unique chart identifier
 * @returns {Chart} - Chart.js instance
 */
function createRadarChart(canvasId, chartData, chartId) {
    destroyChart(chartId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const config = {
        type: 'radar',
        data: chartData,
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
    };

    const chart = new Chart(canvas, config);
    storeChart(chartId, chart);
    return chart;
}

// ============================================================================
// NOTIFICATION UTILITIES
// ============================================================================

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - 'success', 'error', 'info', 'warning'
 * @param {number} duration - Display duration in ms
 */
function showToast(message, type = 'success', duration = 2500) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        console.error('Toast container not found');
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${getToastIcon(type)}</span>
            <span class="toast-message">${message}</span>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Get icon for toast type
 * @param {string} type - Toast type
 * @returns {string} - Icon HTML
 */
function getToastIcon(type) {
    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
        warning: '⚠'
    };
    return icons[type] || '•';
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Parse JWT token and extract payload
 * @param {string} token - JWT token
 * @returns {object|null} - Parsed token or null
 */
function parseJWT(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

/**
 * Check if current user is admin
 * @returns {boolean} - True if user is admin
 */
function isAdmin() {
    const token = localStorage.getItem('authToken');
    if (!token) return false;

    const payload = parseJWT(token);
    return payload && payload.role === 'admin';
}

/**
 * Check if current user is doctor
 * @returns {boolean} - True if user is doctor
 */
function isDoctor() {
    const token = localStorage.getItem('authToken');
    if (!token) return false;

    const payload = parseJWT(token);
    return payload && payload.role === 'doctor';
}

/**
 * Check if current user is patient
 * @returns {boolean} - True if user is patient
 */
function isPatient() {
    const token = localStorage.getItem('authToken');
    if (!token) return false;

    const payload = parseJWT(token);
    return payload && payload.role === 'patient';
}

/**
 * Get current user ID from token
 * @returns {number|null} - User ID or null
 */
function getCurrentUserId() {
    const token = localStorage.getItem('authToken');
    if (!token) return null;

    const payload = parseJWT(token);
    return payload ? payload.user_id : null;
}

/**
 * Get current user role from token
 * @returns {string|null} - User role or null
 */
function getCurrentUserRole() {
    const token = localStorage.getItem('authToken');
    if (!token) return null;

    const payload = parseJWT(token);
    return payload ? payload.role : null;
}

/**
 * Logout user and redirect to login
 */
function logout() {
    localStorage.removeItem('authToken');
    window.location.href = '/login';
}

// ============================================================================
// DOM UTILITIES
// ============================================================================

/**
 * Add event listener with error handling
 * @param {string|HTMLElement} selector - Element selector or element
 * @param {string} event - Event type
 * @param {function} handler - Event handler
 */
function addEventListener(selector, event, handler) {
    const element = typeof selector === 'string'
        ? document.querySelector(selector)
        : selector;

    if (!element) {
        console.warn(`Element not found: ${selector}`);
        return;
    }

    element.addEventListener(event, handler);
}

/**
 * Add multiple event listeners to elements
 * @param {string} selector - CSS selector
 * @param {string} event - Event type
 * @param {function} handler - Event handler
 */
function addEventListenerToAll(selector, event, handler) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(element => {
        element.addEventListener(event, handler);
    });
}

/**
 * Debounce function for resize/scroll events
 * @param {function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {function} - Debounced function
 */
function debounce(func, wait = 250) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
