document.addEventListener('DOMContentLoaded', () => {
    const navBtns = document.querySelectorAll('.nav-btn');
    const viewSections = document.querySelectorAll('.view-section');

    navBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            navBtns.forEach(b => b.classList.remove('active'));
            viewSections.forEach(v => v.classList.remove('active'));

            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');

            if (targetId === 'dashboardView') {
                loadDashboardStats();
            }
        });
    });

    let dailyChartInstance = null;
    let ratioChartInstance = null;
    let uniChartInstance = null;
    let sourceChartInstance = null;

    async function loadDashboardStats() {
        try {
            const res = await fetch('/api/v1/dashboard/stats');
            if (!res.ok) return;

            const data = await res.json();
            const charts = data.charts || {};

            document.getElementById('dashTotalUsers').textContent = data.summary.total_users;
            document.getElementById('dashTotalTeams').textContent = data.summary.total_projects;
            document.getElementById('dashTeamProjects').textContent = data.summary.total_teams;
            document.getElementById('dashTotalIndiv').textContent = data.summary.total_individuals;

            dailyChartInstance = renderDailyTrendChart(
                dailyChartInstance,
                charts.daily_trend?.labels || [],
                charts.daily_trend?.data || []
            );

            ratioChartInstance = renderRatioChart(
                ratioChartInstance,
                data.summary.total_teams,
                data.summary.total_individuals
            );

            sourceChartInstance = renderHorizontalBarChart({
                canvasId: 'sourceChart',
                currentInstance: sourceChartInstance,
                labels: charts.source_distribution?.labels || [],
                data: charts.source_distribution?.data || [],
                color: '#254385',
                maxItems: 14,
                labelWidth: 30,
                tooltipSuffix: 'đăng ký'
            });

            uniChartInstance = renderHorizontalBarChart({
                canvasId: 'uniChart',
                currentInstance: uniChartInstance,
                labels: charts.university_distribution?.labels || [],
                data: charts.university_distribution?.data || [],
                color: '#ee6f35',
                maxItems: 20,
                labelWidth: 32,
                tooltipSuffix: 'đăng ký'
            });

            renderD3BubbleChart(
                'bubbleChartContainer',
                charts.project_domain_distribution?.labels || [],
                charts.project_domain_distribution?.data || []
            );
        } catch (err) {
            console.error('Lỗi tải bảng điều khiển', err);
        }
    }

    function renderDailyTrendChart(currentInstance, labels, data) {
        const ctxDaily = document.getElementById('dailyTrendChart').getContext('2d');
        if (currentInstance) currentInstance.destroy();

        const items = pairChartData(labels, data)
            .sort((a, b) => parseDateValue(a.label) - parseDateValue(b.label));
        const chartLabels = items.length ? items.map(item => item.label) : ['Chưa có dữ liệu'];
        const chartData = items.length ? items.map(item => item.value) : [0];

        return new Chart(ctxDaily, {
            type: 'line',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'Số lượng đăng ký',
                    data: chartData,
                    borderColor: '#d60000',
                    backgroundColor: 'rgba(214, 0, 0, 0.12)',
                    borderWidth: 2,
                    pointRadius: 3.5,
                    pointHoverRadius: 5,
                    fill: true,
                    tension: 0.25
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: { padding: { top: 4, right: 14, bottom: 4, left: 4 } },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: { boxWidth: 34, usePointStyle: false }
                    },
                    tooltip: {
                        callbacks: {
                            label: context => `${context.parsed.y} đăng ký`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(37, 67, 133, 0.08)' },
                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 10,
                            maxRotation: 0,
                            minRotation: 0
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: 'rgba(37, 67, 133, 0.12)' }
                    }
                }
            }
        });
    }

    function renderRatioChart(currentInstance, teamUsers, individualUsers) {
        const ctxRatio = document.getElementById('ratioChart').getContext('2d');
        if (currentInstance) currentInstance.destroy();

        return new Chart(ctxRatio, {
            type: 'doughnut',
            data: {
                labels: ['Dự án theo đội', 'Dự án cá nhân'],
                datasets: [{
                    data: [teamUsers, individualUsers],
                    backgroundColor: ['#254385', '#f29d76'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '52%',
                radius: '78%',
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { boxWidth: 38, padding: 18 }
                    }
                }
            }
        });
    }

    function renderHorizontalBarChart({ canvasId, currentInstance, labels, data, color, maxItems, labelWidth, tooltipSuffix }) {
        const canvas = document.getElementById(canvasId);
        const ctx = canvas.getContext('2d');
        if (currentInstance) currentInstance.destroy();

        const compactChart = window.innerWidth < 520 || canvas.clientWidth < 420;
        const compactLimit = canvasId === 'sourceChart' ? 10 : 14;
        const items = topItems(labels, data, compactChart ? Math.min(maxItems, compactLimit) : maxItems);
        const chartItems = items.length ? items : [{ label: 'Chưa có dữ liệu', value: 0 }];
        const maxValue = Math.max(...chartItems.map(item => item.value), 0);

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartItems.map(item => wrapLabel(item.label, compactChart ? 18 : labelWidth, compactChart ? 3 : 2)),
                datasets: [{
                    data: chartItems.map(item => item.value),
                    backgroundColor: color,
                    borderRadius: 5,
                    borderSkipped: false,
                    barPercentage: 0.72,
                    categoryPercentage: 0.76
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                layout: { padding: { top: 2, right: 28, bottom: 4, left: 2 } },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: items => chartItems[items[0].dataIndex]?.label || '',
                            label: context => `${context.parsed.x} ${tooltipSuffix}`
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        suggestedMax: maxValue ? Math.ceil(maxValue * 1.12) : 1,
                        ticks: { precision: 0 },
                        grid: { color: 'rgba(37, 67, 133, 0.12)' }
                    },
                    y: {
                        ticks: {
                            autoSkip: false,
                            color: '#5f6673',
                            font: { size: compactChart ? 10 : 12 },
                            padding: 8
                        },
                        grid: { display: false },
                        afterFit: scale => {
                            const compact = scale.chart.width < 520;
                            const minWidth = compact ? 156 : 210;
                            const maxWidth = compact ? 184 : 330;
                            scale.width = Math.min(Math.max(scale.width, minWidth), maxWidth);
                        }
                    }
                }
            }
        });
    }

    loadDashboardStats();

    const fileInput = document.getElementById('fileInput');
    const dropArea = document.getElementById('dropArea');
    const fileMsg = document.querySelector('.file-msg');
    const form = document.getElementById('syncForm');

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) fileMsg.textContent = fileInput.files[0].name;
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add('is-active'));
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove('is-active'));
    });

    dropArea.addEventListener('drop', (e) => {
        fileInput.files = e.dataTransfer.files;
        if (fileInput.files.length > 0) fileMsg.textContent = fileInput.files[0].name;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (fileInput.files.length === 0) return alert('Vui lòng chọn file Excel!');

        const courseId = document.getElementById('courseId').value;
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('course_id', courseId);
        formData.append('file', file);

        const btn = document.getElementById('submitBtn');
        const loader = document.getElementById('btnLoader');
        const btnText = document.querySelector('.btn-text');

        btn.disabled = true;
        loader.style.display = 'block';
        btnText.textContent = 'Đang Đồng Bộ...';

        const resultSection = document.getElementById('resultSection');
        const logOutput = document.getElementById('logOutput');

        resultSection.classList.add('hidden');
        logOutput.innerHTML = '';

        try {
            const response = await fetch('/api/v1/sync/msforms', { method: 'POST', body: formData });
            const data = await response.json();
            if (response.ok) {
                displayResults(data.data);
            } else {
                throw new Error(data.detail || 'Lỗi từ server');
            }
        } catch (error) {
            alert('Lỗi: ' + error.message);
        } finally {
            btn.disabled = false;
            loader.style.display = 'none';
            btnText.textContent = 'Bắt Đầu Đồng Bộ';
        }
    });

    function displayResults(report) {
        document.getElementById('resultSection').classList.remove('hidden');
        document.getElementById('statTotal').textContent = report.total_rows;
        document.getElementById('statSuccess').textContent = report.success_count;
        document.getElementById('statFail').textContent = report.fail_count;

        const logOutput = document.getElementById('logOutput');
        report.logs.forEach(log => {
            const div = document.createElement('div');
            div.className = `log-item log-${log.type}`;
            div.textContent = log.msg;
            logOutput.appendChild(div);
        });

        logOutput.scrollTop = logOutput.scrollHeight;

        const downloadBtn = document.getElementById('downloadNewUsersBtn');
        if (report.excel_base64) {
            downloadBtn.classList.remove('hidden');
            downloadBtn.onclick = () => {
                const a = document.createElement('a');
                a.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,' + report.excel_base64;
                a.download = 'New_Users.xlsx';
                a.click();
            };
        } else {
            downloadBtn.classList.add('hidden');
        }
    }
});

function pairChartData(labels = [], data = []) {
    return labels
        .map((label, index) => ({
            label: cleanChartLabel(label),
            value: Number(data[index] || 0)
        }))
        .filter(item => item.label && Number.isFinite(item.value));
}

function topItems(labels = [], data = [], limit = 12) {
    return pairChartData(labels, data)
        .filter(item => item.value > 0)
        .sort((a, b) => b.value - a.value || a.label.localeCompare(b.label, 'vi'))
        .slice(0, limit);
}

function cleanChartLabel(label) {
    return String(label || '')
        .replace(/\s+/g, ' ')
        .trim();
}

function parseDateValue(label) {
    const parsed = Date.parse(`${label}T00:00:00`);
    return Number.isNaN(parsed) ? Date.parse(label) || 0 : parsed;
}

function wrapLabel(label, maxChars = 24, maxLines = 2) {
    const text = cleanChartLabel(label) || 'Không xác định';
    const words = text.split(' ');
    const lines = [];
    let currentLine = '';

    words.forEach(word => {
        const safeWord = word.length > maxChars ? `${word.slice(0, maxChars - 1)}…` : word;
        const candidate = currentLine ? `${currentLine} ${safeWord}` : safeWord;

        if (candidate.length <= maxChars) {
            currentLine = candidate;
        } else {
            if (currentLine) lines.push(currentLine);
            currentLine = safeWord;
        }
    });

    if (currentLine) lines.push(currentLine);
    if (lines.length > maxLines) {
        const visible = lines.slice(0, maxLines);
        visible[maxLines - 1] = truncateText(visible[maxLines - 1], maxChars);
        return visible;
    }

    return lines;
}

function truncateText(text, maxChars = 30) {
    const value = cleanChartLabel(text);
    return value.length > maxChars ? `${value.slice(0, Math.max(maxChars - 1, 1))}…` : value;
}

function renderD3BubbleChart(containerId, labels, data) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    const nodesData = pairChartData(labels, data)
        .filter(item => item.value > 0)
        .sort((a, b) => b.value - a.value || a.label.localeCompare(b.label, 'vi'));

    if (nodesData.length === 0) {
        container.innerHTML = '<p style="color:#666;">Chưa có dữ liệu Lĩnh vực</p>';
        return;
    }

    const width = Math.max(container.clientWidth || 900, 600);
    const height = Math.max(container.clientHeight || 500, 420);

    const root = d3.hierarchy({ children: nodesData })
        .sum(d => d.value)
        .sort((a, b) => b.value - a.value);

    const leaves = d3.pack()
        .size([width, height])
        .padding(8)(root)
        .leaves();

    const bubbleNodes = leaves.map(leaf => ({
        label: leaf.data.label,
        value: leaf.data.value,
        r: leaf.r,
        x: leaf.x,
        y: leaf.y
    }));

    const colorScale = d3.scaleOrdinal()
        .domain(nodesData.map(item => item.label))
        .range(['#d60000', '#f29d76', '#ee6f35', '#254385', '#20b2aa', '#3b5998', '#8a2be2', '#4e79a7', '#59a14f', '#e15759']);

    const tooltip = d3.select(container)
        .append('div')
        .attr('class', 'bubble-tooltip');

    const svg = d3.select(container)
        .append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .attr('width', '100%')
        .attr('height', '100%');

    const node = svg.append('g')
        .selectAll('g')
        .data(bubbleNodes)
        .join('g')
        .attr('class', 'bubble-node')
        .attr('transform', d => `translate(${d.x},${d.y})`)
        .on('mouseenter', (event, d) => showBubbleTooltip(event, d, tooltip))
        .on('mousemove', (event, d) => showBubbleTooltip(event, d, tooltip))
        .on('mouseleave', () => tooltip.classed('is-visible', false));

    node.append('circle')
        .attr('r', d => d.r)
        .style('fill', d => colorScale(d.label))
        .style('fill-opacity', 0.84)
        .style('stroke', '#fff')
        .style('stroke-width', 2);

    node.append('text')
        .attr('class', 'bubble-count')
        .attr('text-anchor', 'middle')
        .attr('dy', d => d.r >= 26 ? '-0.55em' : '0.35em')
        .style('fill', '#fff')
        .style('font-weight', '800')
        .style('font-size', d => `${Math.max(10, Math.min(17, d.r * 0.32))}px`)
        .text(d => d.value);

    node.filter(d => d.r >= 20)
        .append('text')
        .attr('class', 'bubble-label')
        .attr('text-anchor', 'middle')
        .attr('dy', d => d.r >= 26 ? '0.65em' : '0.35em')
        .style('fill', '#fff')
        .style('font-weight', '700')
        .style('font-size', d => `${Math.max(7, Math.min(11, d.r * 0.2))}px`)
        .style('pointer-events', 'none')
        .selectAll('tspan')
        .data(d => getBubbleLabelLines(d))
        .join('tspan')
        .attr('x', 0)
        .attr('dy', (line, index) => index === 0 ? 0 : '1.1em')
        .text(line => line);

    node.append('title')
        .text(d => `${d.label}: ${d.value} dự án`);

    const simulation = d3.forceSimulation(bubbleNodes)
        .alpha(0.2)
        .alphaDecay(0.08)
        .force('x', d3.forceX(width / 2).strength(0.018))
        .force('y', d3.forceY(height / 2).strength(0.018))
        .force('collide', d3.forceCollide(d => d.r + 4).strength(0.86).iterations(2))
        .on('tick', () => {
            node.attr('transform', d => {
                d.x = Math.max(d.r, Math.min(width - d.r, d.x));
                d.y = Math.max(d.r, Math.min(height - d.r, d.y));
                return `translate(${d.x},${d.y})`;
            });
        });

    node.call(d3.drag()
        .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.18).restart();
            d.fx = d.x;
            d.fy = d.y;
        })
        .on('drag', (event, d) => {
            d.fx = Math.max(d.r, Math.min(width - d.r, event.x));
            d.fy = Math.max(d.r, Math.min(height - d.r, event.y));
        })
        .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }));
}

function getBubbleLabelLines(d) {
    if (d.r < 24) return [truncateText(d.label, 8)];
    if (d.r < 36) return [truncateText(d.label, 10)];
    return wrapLabel(d.label, d.r >= 58 ? 14 : 11, d.r >= 58 ? 2 : 1);
}

function showBubbleTooltip(event, d, tooltip) {
    tooltip
        .classed('is-visible', true)
        .style('left', `${event.offsetX + 14}px`)
        .style('top', `${event.offsetY + 14}px`)
        .html(`<strong>${d.label}</strong><span>${d.value} dự án</span>`);
}
