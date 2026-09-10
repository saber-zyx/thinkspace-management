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
    let learningDailyInteractionChart = null;

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
            renderKeyActivitySpotlights(data);
            renderUehLmsEnrollmentSpotlight(data);
            renderPreProgramGateSummary(data);
            renderFoundationCourseSummary(data);
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
        const dailyInteractions = data.daily_interactions || [];

        learningDailyInteractionChart = renderLineChart({
            currentInstance: learningDailyInteractionChart,
            canvasId: 'learningDailyInteractionChart',
            labels: dailyInteractions.map(item => formatDateLabel(item.event_date)),
            datasets: [
                {
                    label: 'Tổng tương tác',
                    data: dailyInteractions.map(item => numberValue(item.total_interactions)),
                    borderColor: '#e53217',
                    backgroundColor: 'rgba(229, 50, 23, 0.12)'
                },
                {
                    label: 'Lượt xem',
                    data: dailyInteractions.map(item => numberValue(item.access_interactions)),
                    borderColor: '#254385',
                    backgroundColor: 'rgba(37, 67, 133, 0.1)'
                },
                {
                    label: 'Người học',
                    data: dailyInteractions.map(item => numberValue(item.active_users)),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)'
                }
            ]
        });

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

    function renderKeyActivitySpotlights(data) {
        const container = document.getElementById('keyActivitySpotlights');
        if (!container) return;

        const rows = data.key_activity_spotlights || [];
        container.innerHTML = rows.length
            ? rows.map(row => {
                const hasSystemOnlyLog = numberValue(row.unique_viewers) === 0 && numberValue(row.total_moodle_log_rows) > 0;
                const lastLearnerInteraction = row.last_interaction_at
                    ? `lần cuối ${formatDateTime(row.last_interaction_at)}`
                    : 'chưa có thí sinh truy cập';
                const systemLogNote = hasSystemOnlyLog
                    ? ` · có ${numberValue(row.total_moodle_log_rows)} log hệ thống, mới nhất ${formatDateTime(row.last_moodle_log_at)}`
                    : '';

                return `
                <div class="spotlight-card">
                    <div class="spotlight-label">${escapeHtml(row.spotlight_label || row.activity_name || 'Hoạt động')}</div>
                    <div class="spotlight-title">${escapeHtml(row.activity_name || row.spotlight_label || 'Không xác định')}</div>
                    <div class="spotlight-metrics">
                        <span><strong>${numberValue(row.unique_viewers)}</strong> người xem</span>
                        <span><strong>${numberValue(row.access_event_count)}</strong> lượt xem</span>
                        <span><strong>${numberValue(row.viewer_rate).toFixed(1)}%</strong> thí sinh</span>
                    </div>
                    <div class="spotlight-meta">
                        ${escapeHtml(activityTypeLabel(row.activity_type))} · module ${escapeHtml(row.moodle_course_module_id || 'N/A')} · ${escapeHtml(lastLearnerInteraction)}${escapeHtml(systemLogNote)}
                    </div>
                </div>
            `;
            }).join('')
            : '<p class="empty-state">Chưa có dữ liệu hoạt động trọng yếu.</p>';
    }

    function renderUehLmsEnrollmentSpotlight(data) {
        const container = document.getElementById('keyActivitySpotlights');
        if (!container) return;

        const summary = data.ueh_lms_entrepreneurship_enrollment_summary || {};
        const enrolledUsers = numberValue(summary.enrolled_registered_users);
        const totalUsers = numberValue(summary.total_registered_users);
        const enrollmentRate = numberValue(summary.enrollment_rate);
        const card = document.createElement('div');
        card.className = 'spotlight-card spotlight-card-action';
        card.innerHTML = `
            <div class="spotlight-label">ĐĂNG KÝ UEH LMS ENTREPRENEURSHIP</div>
            <div class="spotlight-title">Đã đăng ký khóa entrepreneurship</div>
            <div class="spotlight-metrics">
                <span><strong>${enrolledUsers}</strong> user</span>
                <span><strong>${totalUsers}</strong> đăng ký</span>
                <span><strong>${enrollmentRate.toFixed(1)}%</strong> hoàn tất</span>
            </div>
            <div class="spotlight-meta">${enrolledUsers}/${totalUsers} user đã đăng ký trên UEH LMS</div>
            <button class="spotlight-detail-btn" type="button">Chi tiết</button>
        `;

        card.querySelector('.spotlight-detail-btn')?.addEventListener('click', openUehLmsEnrollmentDetail);
        container.appendChild(card);
    }

    function renderPreProgramGateSummary(data) {
        const container = document.getElementById('preProgramGateSummary');
        if (!container) return;

        const summary = data.pre_program_gate_summary || {};
        const rows = [
            {
                label: 'Đã xem Pre-Program Survey',
                value: summary.survey_page_viewers,
                help: 'Dấu hiệu người học mở trang Pre-Program Survey đang hiển thị trên Moodle.'
            },
            {
                label: 'Đã vào nội dung khác sau survey',
                value: summary.post_survey_content_users,
                help: 'Dấu hiệu người học đã có log ở nội dung khác sau khi mở trang survey.'
            },
            {
                label: 'Xem survey nhưng chưa vào nội dung khác',
                value: summary.viewed_survey_but_no_later_content,
                help: 'Nhóm này đã mở survey nhưng chưa thấy log học tập tiếp theo trong dữ liệu hiện có.'
            }
        ];

        container.innerHTML = rows.map(row => `
            <div class="gate-summary-item">
                <strong>${numberValue(row.value)}</strong>
                <span>${escapeHtml(row.label)}</span>
                <small>${escapeHtml(row.help)}</small>
            </div>
        `).join('');
    }

    function renderFoundationCourseSummary(data) {
        const container = document.getElementById('foundationCourseSummary');
        if (!container) return;

        const summary = data.foundation_course_summary || {};
        const rows = [
            {
                label: 'Đã đọc UEH LMS Registration Guideline (FMC3)',
                value: summary.fmc3_guideline_viewers,
                help: 'Dấu hiệu người học mở page hướng dẫn đăng ký LMS của riêng khóa Foundations/FMC3.'
            },
            {
                label: 'Đã vào Certificate Submission',
                value: summary.foundation_submission_users,
                help: 'Dấu hiệu người học đã truy cập activity nộp bài module 716 của Foundations/FMC3.'
            },
            {
                label: 'Đội đã hoạt động trong FMC3',
                value: summary.foundation_active_teams,
                help: 'Số đội có ít nhất một thành viên đọc guideline hoặc vào Certificate Submission.'
            },
            {
                label: 'Bỏ guideline FMC3 nhưng vẫn vào submission',
                value: summary.skipped_fmc3_guideline_but_accessed_content,
                help: 'Người học chưa mở guideline FMC3 nhưng đã truy cập Certificate Submission.'
            },
            {
                label: 'Đọc guideline FMC3 nhưng chưa vào submission',
                value: summary.viewed_fmc3_guideline_but_no_content_access,
                help: 'Người học đã mở guideline FMC3 nhưng chưa có log truy cập Certificate Submission.'
            }
        ];

        container.innerHTML = rows.map(row => `
            <div class="gate-summary-item">
                <strong>${numberValue(row.value)}</strong>
                <span>${escapeHtml(row.label)}</span>
                <small>${escapeHtml(row.help)}</small>
            </div>
        `).join('');
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

    async function openUehLmsEnrollmentDetail() {
        openModal('User đã đăng ký khóa entrepreneurship');
        try {
            const data = await fetchJson('/api/v1/moodle-logs/ueh-lms-entrepreneurship-enrollments-detail');
            renderModalUehLmsEnrollments(data);
        } catch (error) {
            console.error('Lỗi tải chi tiết đăng ký UEH LMS', error);
            setModalError('Không tải được danh sách user đã đăng ký khóa entrepreneurship.');
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

    function renderModalUehLmsEnrollments(data) {
        const summary = data.summary || {};
        const users = data.users || [];
        const total = numberValue(summary.total_registered_users);
        const matched = numberValue(summary.enrolled_registered_users);
        modalContent.innerHTML = `
            <div class="modal-summary-strip">
                <span><strong>${matched}</strong> user match email đăng ký</span>
                <span><strong>${total}</strong> user trong database hiện tại</span>
                <span><strong>${numberValue(summary.source_enrolled_emails)}</strong> email nguồn UEH LMS</span>
            </div>
            ${users.length ? `
                <div class="data-table-wrap">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Họ tên</th>
                                <th>Email</th>
                                <th>Đội</th>
                                <th>Trạng thái UEH LMS</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${users.map(user => `
                                <tr>
                                    <td>${escapeHtml(user.full_name || 'Không có tên')}</td>
                                    <td>${escapeHtml(user.email || '')}</td>
                                    <td>${escapeHtml(user.team_name || 'Cá nhân / chưa có đội')}</td>
                                    <td>${escapeHtml(user.enrollment_status || 'enrolled')}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : '<div class="empty-state">Chưa có email UEH LMS nào match với danh sách đăng ký hiện tại. Khi pipeline UEH LMS đổ dữ liệu vào bảng raw, danh sách này sẽ tự hiện.</div>'}
        `;
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

    function renderLineChart({ currentInstance, canvasId, labels, datasets }) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || typeof Chart === 'undefined') return currentInstance;
        if (currentInstance) currentInstance.destroy();

        return new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels,
                datasets: datasets.map(dataset => ({
                    ...dataset,
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    fill: false,
                    tension: 0.28
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                layout: { padding: { top: 8, right: 16, bottom: 2, left: 2 } },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 14, padding: 16 }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(37, 67, 133, 0.08)' },
                        ticks: {
                            color: '#64748b',
                            maxRotation: 45,
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

    function formatDateLabel(value) {
        if (!value) return '';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleDateString('vi-VN', {
            day: '2-digit',
            month: '2-digit'
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
