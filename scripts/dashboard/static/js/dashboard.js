// Dashboard functionality
let charts = {};

// Initialize charts
function initializeCharts() {
    const chartConfigs = {
        'strategy-chart': {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Active Strategies',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            }
        },
        'optimization-chart': {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Optimization Score',
                    data: [],
                    borderColor: 'rgb(153, 102, 255)',
                    tension: 0.1
                }]
            }
        },
        'execution-chart': {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Execution Success Rate',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }]
            }
        }
    };

    Object.entries(chartConfigs).forEach(([id, config]) => {
        const ctx = document.getElementById(id).getContext('2d');
        charts[id] = new Chart(ctx, config);
    });
}

// Update dashboard data
async function refreshData() {
    try {
        // Update metrics
        const metricsResponse = await fetch('/api/metrics');
        const metrics = await metricsResponse.json();
        updateMetrics(metrics.data);

        // Update agent status
        const statusResponse = await fetch('/api/agents/status');
        const status = await statusResponse.json();
        updateAgentStatus(status.data);

        // Update executions
        const executionsResponse = await fetch('/api/executions');
        const executions = await executionsResponse.json();
        updateExecutionsTable(executions.data);

        // Update strategies
        const strategiesResponse = await fetch('/api/strategies');
        const strategies = await strategiesResponse.json();
        updateStrategiesTable(strategies.data);

        // Update charts
        updateCharts(metrics.data);

    } catch (error) {
        console.error('Error refreshing data:', error);
        showError('Failed to refresh dashboard data');
    }
}

// Update metrics display
function updateMetrics(metrics) {
    document.getElementById('active-strategies').textContent =
        metrics.strategies.active || 0;
    document.getElementById('success-rate').textContent =
        `${((metrics.executions.successful / metrics.executions.total) * 100).toFixed(1)}%`;
    document.getElementById('total-executions').textContent =
        metrics.executions.total || 0;
}

// Update agent status
function updateAgentStatus(agents) {
    agents.forEach(agent => {
        const statusElement = document.getElementById(`${agent.agent_type}-status`);
        if (statusElement) {
            statusElement.className = `badge ${agent.status === 'active' ? 'bg-success' : 'bg-danger'} float-end`;
            statusElement.textContent = agent.status;
        }
    });
}

// Update executions table
function updateExecutionsTable(executions) {
    const tbody = document.querySelector('#executions-table tbody');
    tbody.innerHTML = '';

    executions.forEach(execution => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${new Date(execution.execution_time).toLocaleString()}</td>
            <td>${execution.strategy}</td>
            <td><span class="badge ${execution.status === 'completed' ? 'bg-success' : 'bg-warning'}">${execution.status}</span></td>
            <td>${execution.result || '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Update strategies table
function updateStrategiesTable(strategies) {
    const tbody = document.querySelector('#strategies-table tbody');
    tbody.innerHTML = '';

    strategies.forEach(strategy => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${strategy.name}</td>
            <td><span class="badge ${strategy.status === 'active' ? 'bg-success' : 'bg-secondary'}">${strategy.status}</span></td>
            <td>${new Date(strategy.created_at).toLocaleString()}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="toggleStrategy(${strategy.id})">
                    ${strategy.status === 'active' ? 'Disable' : 'Enable'}
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Update charts
function updateCharts(metrics) {
    Object.values(charts).forEach(chart => {
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }

        const now = new Date().toLocaleTimeString();
        chart.data.labels.push(now);
        chart.update();
    });
}

// Show error message
function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container-fluid').prepend(alert);
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    refreshData();
    setInterval(refreshData, 30000); // Refresh every 30 seconds
}); 