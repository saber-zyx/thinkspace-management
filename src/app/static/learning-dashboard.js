document.addEventListener('DOMContentLoaded', () => {
    const learningNav = document.querySelector('[data-target="learningDashboardView"]');
    const refreshButton = document.getElementById('refreshLearningDashboardBtn');
    const tabButtons = document.querySelectorAll('.learning-tab');
    const tabPanels = {
        overview: document.getElementById('learningOverviewPanel'),
        team: document.getElementById('learningTeamPanel'),
        individual: document.getElementById('learningIndividualPanel')
    };
    const modal = document.getElementById('activityDetailModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');

    let overviewLoaded = false;
    let teamLoaded = false;
    let individualLoaded = false;
    let learningStatusChart = null;
    let learningTeamStatusChart = null;
    let learningActivityTypeChart = null;

    if (learningNav) {
        learningNav.addEventListener('click', () => {
            window.setTimeout(() => loadLearningOverview(), 0);
        });
    }

    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            overviewLoaded = false;
            teamLoaded = false;
            individualLoaded = false;
            loadCurrentLearningTab();
        });
    }

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }

    if (modal) {
        modal.addEventListener('click', event => {
            if (event.target === modal) closeModal();
        });
    }

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.learningTab;
            tabButtons.forEach(item => item.classList.remove('active'));
            button.classList.add('active');

            Object.values(tabPanels).forEach(panel => panel.classList.remove('active'));
            tabPanels[tabName]?.classList.add('active');
            loadCurrentLearningTab();
        });
    });

    function loadCurrentLearningTab() {
        const activeTab = document.querySelector('.learning-tab.active')?.dataset.learningTab || 'overview';
        if (activeTab === 'team') return loadTeamSummary();
        if (activeTab === 'individual') return loadIndividualSummary();
        return loadLearningOverview();
    }

    async function loadLearningOverview() {
        if (overviewLoaded) return;
        try {
            setLearningUpdatedText('Đang tải tổng quan...');
            const data = await fetchJson('/api/v1/moodle-logs/learning-dashboard-overview');
            overviewLoaded = true;
            renderOverviewKpis(data);
            renderOverviewCharts(data);
            renderActivityLists(data);
            renderSubmissionTables(data);
            setLearningUpdatedText(`Cập nhật: ${formatDateTime(new Date().toISOString())}`);
        } catch (error) {
            console.error('Lỗi tải tổng quan bảng học tập', error);
            setLearningUpdatedText('Không tải được dữ liệu tổng quan');
        }
    }

    async function loadTeamSummary() {
        if (teamLoaded) return;
        try {
            setLearningUpdatedText('Đang tải dữ liệu đội...');
            const data = await fetchJson('/api/v1/moodle-logs/gold-team-summary');
            teamLoaded = true;
            renderTeamTable(data);
            setLearningUpdatedText(`Cập nhật: ${formatDateTime(new Date().toISOString())}`);
        } catch (error) {
            console.error('Lỗi tải dữ liệu đội', error);
            setLearningUpdatedText('Không tải được dữ liệu đội');
        }
    }

    async function loadIndividualSummary() {
        if (individualLoaded) return;
        try {
            setLearningUpdatedText('Đang tải dữ liệu cá nhân...');
            const data = await fetchJson('/api/v1/moodle-logs/gold-individual-summary');
            individualLoaded = true;
            renderIndividualTable(data);
            setLearningUpdatedText(`Cập nhật: ${formatDateTime(new Date().toISOString())}`);
        } catch (error) {
            console.error('Lỗi tải dữ liệu cá nhân', error);
            setLearningUpdatedText('Không tải được dữ liệu cá nhân');
        }
    }

    async function fetchJson(url) {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    }

    function renderOverviewKpis(data) {
        const registered = data.registered_summary || {};
        const teams = data.team_summary || {};

        setText('learningTotalUsers', registered.total_registered_users);
        setText('learningAccessedUsers', `${numberValue(registered.accessed_users)} đã học`);
        setText('learningNotStartedUsers', registered.not_started_users);
        setText('learningActiveTeams', teams.active_teams);
        setText('learningTotalTeams', `${numberValue(teams.total_teams)} đội tổng`);
        setText('learningSubmittedUsers', registered.submitted_users);
        setText('learningSubmittedTeams', `${numberValue(teams.submitted_teams)} đội đã nộp bài`);
    }

    function renderOverviewCharts(data) {
        const registered = data.registered_summary || {};
        const teams = data.team_summary || {};
        const activityTypes = data.activity_type_summary || [];

        learningStatusChart = renderDoughnutChart({
            currentInstance: learningStatusChart,
            canvasId: 'learningStatusChart',
            labels: ['Đã học', 'Chưa bắt đầu', 'Đã nộp bài'],
            values: [
                Math.max(numberValue(registered.accessed_users) - numberValue(registered.submitted_users), 0),
                numberValue(registered.not_started_users),
                numberValue(registered.submitted_users)
            ],
            colors: ['#254385', '#f29d76', '#10b981']
        });

        learningTeamStatusChart = renderDoughnutChart({
            currentInstance: learningTeamStatusChart,
            canvasId: 'learningTeamStatusChart',
            labels: ['Đang hoạt động', 'Chưa bắt đầu', 'Đã nộp bài'],
            values: [
                Math.max(numberValue(teams.active_teams) - numberValue(teams.submitted_teams), 0),
                numberValue(teams.not_started_teams),
                numberValue(teams.submitted_teams)
            ],
            colors: ['#254385', '#f29d76', '#10b981']
        });

        learningActivityTypeChart = renderBarChart({
            currentInstance: learningActivityTypeChart,
            canvasId: 'learningActivityTypeChart',
            labels: activityTypes.map(item => activityTypeLabel(item.activity_type)),
            values: activityTypes.map(item => numberValue(item.unique_viewers)),
            label: 'Người học đã xem'
        });
    }

    function renderActivityLists(data) {
        renderDataList({
            containerId: 'topViewedActivitiesList',
            rows: data.top_viewed_activities || [],
            title: row => row.activity_name || 'Không xác định',
            meta: row => `${activityTypeLabel(row.activity_type)} · ${numberValue(row.access_event_count)} lượt xem · ${formatDateTime(row.last_access_at)}`,
            value: row => `${numberValue(row.unique_viewers)} người`
        });

        renderDataList({
            containerId: 'lowAttentionActivitiesList',
            rows: data.low_attention_activities || [],
            title: row => row.activity_name || 'Không xác định',
            meta: row => `${activityTypeLabel(row.activity_type)} · ${numberValue(row.access_event_count)} lượt xem`,
            value: row => `${numberValue(row.unique_viewers)} người`
        });
    }

    function renderSubmissionTables(data) {
        const body = document.getElementById('submissionActivitiesTable');
        if (!body) return;

        const rows = data.submission_activities || [];
        body.innerHTML = rows.length
            ? rows.map(row => `
                <tr>
                    <td>${escapeHtml(row.activity_name || 'Không xác định')}</td>
                    <td>${numberValue(row.unique_viewers)}</td>
                    <td>${numberValue(row.unique_submitters)}</td>
                    <td>${escapeHtml(formatDateTime(row.latest_submission_at))}</td>
                </tr>
            `).join('')
            : '<tr><td colspan="4">Chưa có dữ liệu nộp bài.</td></tr>';

        renderDataList({
            containerId: 'submittedTeamsList',
            rows: data.submitted_teams || [],
            title: row => row.team_name || 'Không có tên đội',
            meta: row => `${numberValue(row.submitted_users)} người nộp · ${numberValue(row.submitted_activity_count)} hoạt động nộp bài`,
            value: row => formatDateTime(row.latest_submission_at)
        });
    }

    function renderTeamTable(data) {
        const body = document.getElementById('teamLearningTable');
        const summary = document.getElementById('teamPanelSummary');
        const rows = data.teams || [];

        if (summary) {
            summary.textContent = `${numberValue(data.active_teams)} đội đã hoạt động / ${numberValue(data.total_teams)} đội`;
        }

        if (!body) return;
        body.innerHTML = rows.length
            ? rows.map(row => `
                <tr>
                    <td>
                        <div class="table-primary-text">${escapeHtml(row.team_name || 'Không có tên đội')}</div>
                    </td>
                    <td>${numberValue(row.registered_users)}</td>
                    <td>${numberValue(row.accessed_users)}</td>
                    <td>${numberValue(row.not_started_users)}</td>
                    <td>${numberValue(row.submitted_users)}</td>
                    <td>${numberValue(row.viewed_activity_count)}</td>
                    <td><span class="status-pill ${statusClass(row.current_team_learning_status)}">${statusLabel(row.current_team_learning_status)}</span></td>
                    <td>${escapeHtml(formatDateTime(row.last_access_at))}</td>
                    <td>
                        <button class="table-action-btn" type="button" data-team-key="${escapeHtml(row.team_name_key || '')}">
                            Chi tiết
                        </button>
                    </td>
                </tr>
            `).join('')
            : '<tr><td colspan="9">Chưa có dữ liệu đội.</td></tr>';

        body.querySelectorAll('[data-team-key]').forEach(button => {
            button.addEventListener('click', () => openTeamActivityDetail(button.dataset.teamKey));
        });
    }

    function renderIndividualTable(data) {
        const body = document.getElementById('individualLearningTable');
        const summary = document.getElementById('individualPanelSummary');
        const rows = data.individuals || [];

        if (summary) {
            summary.textContent = `${numberValue(data.accessed_individuals)} cá nhân đã học / ${numberValue(data.total_individuals)} cá nhân`;
        }

        if (!body) return;
        body.innerHTML = rows.length
            ? rows.map(row => `
                <tr>
                    <td>
                        <div class="table-primary-text">${escapeHtml(row.full_name || 'Không có tên')}</div>
                    </td>
                    <td>${escapeHtml(row.email || '')}</td>
                    <td>${escapeHtml(row.moodle_group_name || 'Chưa có nhóm Moodle')}</td>
                    <td>${numberValue(row.viewed_activity_count)}</td>
                    <td>${numberValue(row.submitted_activity_count)}</td>
                    <td><span class="status-pill ${statusClass(row.current_learning_status)}">${statusLabel(row.current_learning_status)}</span></td>
                    <td>${escapeHtml(formatDateTime(row.last_access_at))}</td>
                    <td>
                        <button class="table-action-btn" type="button" data-individual-email="${escapeHtml(row.email || '')}">
                            Chi tiết
                        </button>
                    </td>
                </tr>
            `).join('')
            : '<tr><td colspan="8">Chưa có dữ liệu cá nhân.</td></tr>';

        body.querySelectorAll('[data-individual-email]').forEach(button => {
            button.addEventListener('click', () => openIndividualActivityDetail(button.dataset.individualEmail));
        });
    }

    async function openTeamActivityDetail(teamKey) {
        if (!teamKey) return;
        openModal('Chi tiết hoạt động theo đội');
        try {
            const data = await fetchJson(`/api/v1/moodle-logs/team-activities-detail?team_name_key=${encodeURIComponent(teamKey)}`);
            renderModalTeamActivities(data);
        } catch (error) {
            console.error('Lỗi tải chi tiết hoạt động đội', error);
            setModalError('Không tải được dữ liệu chi tiết của đội.');
        }
    }

    async function openIndividualActivityDetail(email) {
        if (!email) return;
        openModal('Chi tiết hoạt động cá nhân');
        try {
            const data = await fetchJson(`/api/v1/moodle-logs/individual-activities-detail?email=${encodeURIComponent(email)}`);
            renderModalIndividualActivities(data);
        } catch (error) {
            console.error('Lỗi tải chi tiết hoạt động cá nhân', error);
            setModalError('Không tải được dữ liệu chi tiết của cá nhân.');
        }
    }

    function renderModalTeamActivities(data) {
        const teamName = data.team?.team_name || data.team_name_key || 'Đội';
        modalTitle.textContent = `Đội: ${teamName}`;

        if (!data.members || data.members.length === 0) {
            modalContent.innerHTML = '<p class="empty-state">Không có thành viên nào trong dữ liệu đăng ký.</p>';
            return;
        }

        modalContent.innerHTML = data.members.map(member => renderMemberActivityBlock(member)).join('');
    }

    function renderModalIndividualActivities(data) {
        modalTitle.textContent = `Cá nhân: ${data.full_name || data.email || 'Không có tên'}`;
        modalContent.innerHTML = renderMemberActivityBlock(data);
    }

    function renderMemberActivityBlock(member) {
        return `
            <div class="member-detail-block">
                <div class="member-detail-header">
                    <div>
                        <h3>${escapeHtml(member.full_name || 'Không có tên')}</h3>
                        <div class="member-detail-meta">${escapeHtml(member.email || '')}</div>
                    </div>
                    <span class="status-pill ${statusClass(member.current_learning_status)}">${statusLabel(member.current_learning_status)}</span>
                </div>
                <div class="member-metrics">
                    <span>${numberValue(member.viewed_activity_count)} hoạt động đã xem</span>
                    <span>${numberValue(member.learning_event_count)} sự kiện học</span>
                    <span>${numberValue(member.submitted_activity_count)} hoạt động nộp bài</span>
                    <span>Lần học cuối: ${escapeHtml(formatDateTime(member.last_access_at))}</span>
                </div>
                ${renderActivitiesList(member.activities)}
            </div>
        `;
    }

    function renderActivitiesList(activities) {
        if (!activities || activities.length === 0) {
            return '<div class="empty-state">Chưa có hoạt động nào được ghi nhận cho người dùng này.</div>';
        }

        return `
            <div class="activity-list">
                ${activities.map(activity => `
                    <div class="activity-item">
                        <div class="activity-info">
                            <span class="activity-name">${escapeHtml(activity.activity_name || 'Không xác định')}</span>
                            <span class="activity-type">${escapeHtml(activityTypeLabel(activity.activity_type))} · module ${escapeHtml(activity.moodle_course_module_id || 'N/A')}</span>
                        </div>
                        <div class="activity-status">
                            ${renderActivityMetricChips(activity)}
                            <span class="activity-time">Lần cuối: ${escapeHtml(formatDateTime(activity.last_access_at))}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    function openModal(title) {
        if (!modal || !modalTitle || !modalContent) return;
        modalTitle.textContent = title;
        modalContent.innerHTML = '<div class="empty-state">Đang tải dữ liệu...</div>';
        modal.classList.add('active');
    }

    function closeModal() {
        modal?.classList.remove('active');
    }

    function setModalError(message) {
        if (modalContent) modalContent.innerHTML = `<div class="empty-state error-text">${escapeHtml(message)}</div>`;
    }

    function renderDoughnutChart({ currentInstance, canvasId, labels, values, colors }) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || typeof Chart === 'undefined') return currentInstance;
        if (currentInstance) currentInstance.destroy();

        return new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '58%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 14, padding: 16 }
                    }
                }
            }
        });
    }

    function renderBarChart({ currentInstance, canvasId, labels, values, label }) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || typeof Chart === 'undefined') return currentInstance;
        if (currentInstance) currentInstance.destroy();

        return new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label,
                    data: values,
                    backgroundColor: '#254385',
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: { padding: { top: 8, right: 16, bottom: 2, left: 2 } },
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#64748b' }
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

    function renderDataList({ containerId, rows, title, meta, value }) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = rows.length
            ? rows.map(row => `
                <div class="data-list-item">
                    <div>
                        <div class="data-list-title">${escapeHtml(title(row))}</div>
                        <div class="data-list-meta">${escapeHtml(meta(row))}</div>
                    </div>
                    <div class="data-list-value">${escapeHtml(value(row))}</div>
                </div>
            `).join('')
            : '<p class="empty-state">Chưa có dữ liệu.</p>';
    }

    function setText(id, value) {
        const element = document.getElementById(id);
        if (element) element.textContent = value ?? 0;
    }

    function setLearningUpdatedText(value) {
        setText('learningLastUpdated', value);
    }

    function numberValue(value) {
        const number = Number(value || 0);
        return Number.isFinite(number) ? number : 0;
    }

    function formatDateTime(value) {
        if (!value) return 'Chưa có';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return 'Chưa có';
        return date.toLocaleString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function statusLabel(value) {
        const labels = {
            active: 'Đang học',
            inactive: 'Tạm ngưng',
            not_started: 'Chưa bắt đầu',
            submitted: 'Đã nộp bài'
        };
        return labels[value] || 'Chưa xác định';
    }

    function statusClass(value) {
        if (value === 'submitted') return 'status-submitted';
        if (value === 'active') return 'status-active';
        if (value === 'inactive') return 'status-inactive';
        return 'status-not-started';
    }

    function activityTypeLabel(value) {
        return value || 'Không xác định';
    }

    function renderActivityMetricChips(activity) {
        const chips = [
            `${numberValue(activity.access_event_count)} lượt view`,
            `${numberValue(activity.event_count)} sự kiện`
        ];
        const submissionActions = numberValue(activity.submission_event_count);
        const finalSubmissions = numberValue(activity.submission_final_event_count);

        if (submissionActions > 0) {
            chips.push(`${submissionActions} thao tác nộp bài`);
        }
        if (finalSubmissions > 0) {
            chips.push(`${finalSubmissions} đã nộp bài`);
        }

        return `
            <div class="activity-metric-list">
                ${chips.map(chip => `<span class="activity-metric">${escapeHtml(chip)}</span>`).join('')}
            </div>
        `;
    }

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
