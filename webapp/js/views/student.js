/**
 * Student View Renderer (5 tabs: Home, Grades, Homework, Schedule, Profile)
 */
import { api } from '../api.js';
import { i18n } from '../i18n.js';

export const StudentView = {
  async renderHome(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const data = await api.getStudentDashboard();
      const s = data.student || {};

      container.innerHTML = `
        <div class="hero-card">
          <div class="hero-greeting">Добро пожаловать в Lumina 👋</div>
          <div class="hero-name">${s.name || 'Ученик'}</div>
          <div class="hero-stats">
            <div class="stat-box">
              <span class="stat-label">Класс</span>
              <span class="stat-val">${s.class_name || '7-А'}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Уровень / XP</span>
              <span class="stat-val">Lvl ${s.level || 1} (${s.xp || 0} XP)</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Дедлайны</span>
              <span class="stat-val">${data.urgent_homework_count || 0}</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="calendar" aria-hidden="true"></i>
              <span>Уроки на сегодня</span>
            </div>
            <span class="badge badge-info">${data.today_lessons.length} уроков</span>
          </div>
          <div class="card-body">
            ${data.today_lessons.length === 0 ? '<p class="empty-text">Сегодня уроков нет</p>' : data.today_lessons.map(l => `
              <div class="lesson-card">
                <div class="lesson-period">${l.period}</div>
                <div class="lesson-details">
                  <div class="lesson-subject">${l.subject}</div>
                  <div class="lesson-meta">
                    <span><i data-lucide="map-pin" style="width:12px;height:12px;display:inline;"></i> Каб. ${l.room || '—'}</span>
                    <span class="badge ${l.status === 'SCHEDULED' ? 'badge-success' : 'badge-warning'}">${l.status}</span>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        ${data.latest_grade ? `
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                <i data-lucide="award" aria-hidden="true"></i>
                <span>Последняя оценка</span>
              </div>
              <div class="grade-pill grade-${Math.floor(data.latest_grade.value)}">${data.latest_grade.raw_display}</div>
            </div>
            <p style="font-size:13px;color:var(--text-secondary);">${data.latest_grade.type}: ${data.latest_grade.comment || 'Без комментария'}</p>
          </div>
        ` : ''}
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">Не удалось загрузить данные дашборда: ${e.message}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderGrades(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const data = await api.getStudentGrades();
      container.innerHTML = `
        <div class="card" style="background:var(--color-primary-subtle);border-color:var(--color-primary);">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-size:12px;font-weight:700;color:var(--color-primary);text-transform:uppercase;">Общий средний балл</div>
              <div style="font-size:28px;font-weight:800;color:var(--text-primary);margin-top:2px;">${data.overall_gpa}</div>
            </div>
            <div class="grade-pill grade-${Math.floor(data.overall_gpa)}">${data.overall_gpa}</div>
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:12px;">
          ${data.subjects.length === 0 ? '<p class="empty-text">Оценок пока нет</p>' : data.subjects.map(s => `
            <div class="card">
              <div class="card-header">
                <div class="card-title">
                  <i data-lucide="book-open" aria-hidden="true"></i>
                  <span>${s.subject}</span>
                </div>
                <div class="badge badge-info">Ср: ${s.average}</div>
              </div>
              <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:4px;">
                ${s.grades.map(g => `
                  <div class="grade-pill grade-${Math.floor(g.value)}" title="${g.type_name} (${g.date}) - ${g.comment || ''}">
                    ${g.raw_display}
                  </div>
                `).join('')}
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${e.message}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderHomework(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const hwList = await api.getStudentHomework();
      container.innerHTML = `
        <div class="card-header">
          <h2 style="font-size:18px;font-weight:700;">Домашние задания</h2>
          <span class="badge badge-info">${hwList.length} заданий</span>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${hwList.length === 0 ? '<p class="empty-text">Заданий нет!</p>' : hwList.map(hw => `
            <div class="hw-item ${hw.status === 'DONE' ? 'done' : ''}" id="hw-${hw.id}">
              <div class="hw-checkbox ${hw.status === 'DONE' ? 'checked' : ''}" data-id="${hw.id}" data-status="${hw.status}">
                ${hw.status === 'DONE' ? '<i data-lucide="check" style="width:14px;height:14px;"></i>' : ''}
              </div>
              <div class="hw-content">
                <div style="font-size:11px;font-weight:700;color:var(--color-primary);text-transform:uppercase;">${hw.subject}</div>
                <div class="hw-title">${hw.title}</div>
                <p style="font-size:12px;color:var(--text-secondary);margin-top:2px;">${hw.description}</p>
                <div class="hw-date">Срок: ${hw.due_date}</div>
              </div>
            </div>
          `).join('')}
        </div>
      `;

      container.querySelectorAll('.hw-checkbox').forEach(box => {
        box.addEventListener('click', async (e) => {
          const hwId = box.getAttribute('data-id');
          const curStatus = box.getAttribute('data-status');
          const newStatus = curStatus === 'DONE' ? 'TODO' : 'DONE';
          try {
            await api.toggleHomework(hwId, newStatus);
            StudentView.renderHomework(container);
          } catch (err) {
            alert(err.message);
          }
        });
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${e.message}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderSchedule(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const lessons = await api.getStudentSchedule();
      container.innerHTML = `
        <div class="card-header">
          <h2 style="font-size:18px;font-weight:700;">Расписание занятий</h2>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${lessons.length === 0 ? '<p class="empty-text">Расписание пусто</p>' : lessons.map(l => `
            <div class="lesson-card">
              <div class="lesson-period">${l.period}</div>
              <div class="lesson-details">
                <div class="lesson-subject">${l.subject}</div>
                <div class="lesson-meta">
                  <span>${l.date}</span>
                  <span>Кабинет ${l.room || '—'}</span>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${e.message}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderProfile(container) {
    const user = await api.getMe();
    container.innerHTML = `
      <div class="card" style="align-items:center;text-align:center;padding:24px;">
        <div style="width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,var(--color-primary),#0284c7);color:#fff;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:800;margin-bottom:12px;">
          ${user.first_name[0]}
        </div>
        <h2 style="font-size:18px;font-weight:700;">${user.first_name} ${user.last_name || ''}</h2>
        <span class="role-badge" style="margin-top:6px;">${user.role} • ${user.class_name || '7-А'}</span>
      </div>

      <div class="card">
        <div class="card-title">
          <i data-lucide="settings" aria-hidden="true"></i>
          <span>Настройки</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border-color);">
          <span style="font-size:14px;font-weight:600;">Язык приложения</span>
          <button class="lang-btn" id="profileLangBtn">Сменить (RU/UZ)</button>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;">
          <span style="font-size:14px;font-weight:600;">Темная тема</span>
          <button class="btn btn-subtle" id="themeToggleBtn" style="padding:6px 12px;font-size:12px;">Переключить</button>
        </div>
      </div>
    `;

    document.getElementById('profileLangBtn')?.addEventListener('click', async () => {
      await i18n.toggleLanguage();
      StudentView.renderProfile(container);
    });

    document.getElementById('themeToggleBtn')?.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
    });

    lucide.createIcons();
  }
};
