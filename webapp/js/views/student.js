/**
 * Student View Renderer (5 tabs: Home, Grades, Homework, Schedule, Profile)
 */
import { api } from '../api.js';
import { i18n } from '../i18n.js';
import { escapeHtml, triggerHaptic, showToast } from '../utils.js';

export const StudentView = {
  async renderHome(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const data = await api.getStudentDashboard();
      const s = data.student || {};

      container.innerHTML = `
        <div class="hero-card">
          <div class="hero-greeting">${escapeHtml(i18n.t('student.greeting', 'Добро пожаловать в Lumina 👋'))}</div>
          <div class="hero-name">${escapeHtml(s.name || 'Ученик')}</div>
          <div class="hero-stats">
            <div class="stat-box">
              <span class="stat-label">${escapeHtml(i18n.t('student.class', 'Класс'))}</span>
              <span class="stat-val">${escapeHtml(s.class_name || '—')}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">${escapeHtml(i18n.t('student.level', 'Уровень / XP'))}</span>
              <span class="stat-val">Lvl ${escapeHtml(String(s.level || 1))} (${escapeHtml(String(s.xp || 0))} XP)</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">${escapeHtml(i18n.t('student.urgent_hw', 'Дедлайны'))}</span>
              <span class="stat-val">${data.urgent_homework_count || 0}</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="calendar" aria-hidden="true"></i>
              <span>${escapeHtml(i18n.t('student.today_lessons', 'Уроки на сегодня'))}</span>
            </div>
            <span class="badge badge-info">${data.today_lessons.length} ${escapeHtml(i18n.t('common.lessons', 'уроков'))}</span>
          </div>
          <div class="card-body">
            ${data.today_lessons.length === 0 ? `<p class="empty-text">${escapeHtml(i18n.t('student.no_lessons_today', 'Сегодня уроков нет'))}</p>` : data.today_lessons.map(l => `
              <div class="lesson-card">
                <div class="lesson-period">${escapeHtml(String(l.period))}</div>
                <div class="lesson-details">
                  <div class="lesson-subject">${escapeHtml(l.subject)}</div>
                  <div class="lesson-meta">
                    <span><i data-lucide="map-pin" style="width:12px;height:12px;display:inline;"></i> ${escapeHtml(l.room || '—')}</span>
                    <span class="badge ${l.status === 'SCHEDULED' ? 'badge-success' : 'badge-warning'}">${escapeHtml(l.status)}</span>
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
                <span>${escapeHtml(i18n.t('student.latest_grade', 'Последняя оценка'))}</span>
              </div>
              <div class="grade-pill grade-${Math.floor(data.latest_grade.value)}">${escapeHtml(data.latest_grade.raw_display)}</div>
            </div>
            <p style="font-size:13px;color:var(--text-secondary);">${escapeHtml(data.latest_grade.type)}: ${escapeHtml(data.latest_grade.comment || i18n.t('student.no_comment', 'Без комментария'))}</p>
          </div>
        ` : ''}
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
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
              <div style="font-size:12px;font-weight:700;color:var(--color-primary);text-transform:uppercase;">${escapeHtml(i18n.t('student.gpa', 'Общий средний балл'))}</div>
              <div style="font-size:28px;font-weight:800;color:var(--text-primary);margin-top:2px;">${escapeHtml(String(data.overall_gpa))}</div>
            </div>
            <div class="grade-pill grade-${Math.floor(data.overall_gpa)}">${escapeHtml(String(data.overall_gpa))}</div>
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:12px;">
          ${data.subjects.length === 0 ? `<p class="empty-text">${escapeHtml(i18n.t('student.no_grades', 'Оценок пока нет'))}</p>` : data.subjects.map(s => `
            <div class="card">
              <div class="card-header">
                <div class="card-title">
                  <i data-lucide="book-open" aria-hidden="true"></i>
                  <span>${escapeHtml(s.subject)}</span>
                </div>
                <div class="badge badge-info">${escapeHtml(i18n.t('common.avg', 'Ср'))}: ${escapeHtml(String(s.average))}</div>
              </div>
              <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:4px;">
                ${s.grades.map(g => `
                  <div class="grade-pill grade-${Math.floor(g.value)}" title="${escapeHtml(g.type_name)} (${escapeHtml(g.date)}) - ${escapeHtml(g.comment || '')}">
                    ${escapeHtml(g.raw_display)}
                  </div>
                `).join('')}
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
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
          <h2 style="font-size:18px;font-weight:700;">${escapeHtml(i18n.t('student.homework', 'Домашние задания'))}</h2>
          <span class="badge badge-info">${hwList.length} ${escapeHtml(i18n.t('common.tasks', 'заданий'))}</span>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${hwList.length === 0 ? `<p class="empty-text">${escapeHtml(i18n.t('student.no_homework', 'Заданий нет!'))}</p>` : hwList.map(hw => `
            <div class="hw-item ${hw.status === 'DONE' ? 'done' : ''}" id="hw-${hw.id}">
              <div class="hw-checkbox ${hw.status === 'DONE' ? 'checked' : ''}" data-id="${hw.id}" data-status="${hw.status}">
                ${hw.status === 'DONE' ? '<i data-lucide="check" style="width:14px;height:14px;"></i>' : ''}
              </div>
              <div class="hw-content">
                <div style="font-size:11px;font-weight:700;color:var(--color-primary);text-transform:uppercase;">${escapeHtml(hw.subject)}</div>
                <div class="hw-title">${escapeHtml(hw.title)}</div>
                <p style="font-size:12px;color:var(--text-secondary);margin-top:2px;">${escapeHtml(hw.description || '')}</p>
                <div class="hw-date">${escapeHtml(i18n.t('common.deadline', 'Срок'))}: ${escapeHtml(hw.due_date)}</div>
              </div>
            </div>
          `).join('')}
        </div>
      `;

      container.querySelectorAll('.hw-checkbox').forEach(box => {
        box.addEventListener('click', async () => {
          const hwId = box.getAttribute('data-id');
          const curStatus = box.getAttribute('data-status');
          const newStatus = curStatus === 'DONE' ? 'TODO' : 'DONE';
          try {
            triggerHaptic('impact', 'light');
            await api.toggleHomework(hwId, newStatus);
            showToast(newStatus === 'DONE' ? i18n.t('homework.marked_done', 'Задание выполнено!') : i18n.t('homework.marked_todo', 'Задание возвращено в работу'), 'success');
            StudentView.renderHomework(container);
          } catch (err) {
            triggerHaptic('notification', 'error');
            showToast(err.message, 'error');
          }
        });
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
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
          <h2 style="font-size:18px;font-weight:700;">${escapeHtml(i18n.t('student.schedule', 'Расписание занятий'))}</h2>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${lessons.length === 0 ? `<p class="empty-text">${escapeHtml(i18n.t('student.no_schedule', 'Расписание пусто'))}</p>` : lessons.map(l => `
            <div class="lesson-card">
              <div class="lesson-period">${escapeHtml(String(l.period))}</div>
              <div class="lesson-details">
                <div class="lesson-subject">${escapeHtml(l.subject)}</div>
                <div class="lesson-meta">
                  <span>${escapeHtml(l.date)}</span>
                  <span>${escapeHtml(i18n.t('common.room', 'Кабинет'))} ${escapeHtml(l.room || '—')}</span>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderProfile(container) {
    try {
      const user = await api.getMe();
      const initial = (user.first_name || 'U')[0].toUpperCase();
      container.innerHTML = `
        <div class="card" style="align-items:center;text-align:center;padding:24px;">
          <div style="width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,var(--color-primary),#0284c7);color:#fff;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:800;margin-bottom:12px;">
            ${escapeHtml(initial)}
          </div>
          <h2 style="font-size:18px;font-weight:700;">${escapeHtml(user.first_name)} ${escapeHtml(user.last_name || '')}</h2>
          <span class="role-badge" style="margin-top:6px;">${escapeHtml(user.role)} • ${escapeHtml(user.class_name || '—')}</span>
        </div>

        <div class="card">
          <div class="card-title">
            <i data-lucide="settings" aria-hidden="true"></i>
            <span>${escapeHtml(i18n.t('common.settings', 'Настройки'))}</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border-color);">
            <span style="font-size:14px;font-weight:600;">${escapeHtml(i18n.t('settings.language', 'Язык приложения'))}</span>
            <button class="lang-btn" id="profileLangBtn">Сменить (RU/UZ)</button>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;">
            <span style="font-size:14px;font-weight:600;">${escapeHtml(i18n.t('settings.dark_mode', 'Темная тема'))}</span>
            <button class="btn btn-subtle" id="themeToggleBtn" style="padding:6px 12px;font-size:12px;">${escapeHtml(i18n.t('settings.toggle', 'Переключить'))}</button>
          </div>
        </div>
      `;

      document.getElementById('profileLangBtn')?.addEventListener('click', async () => {
        triggerHaptic('impact', 'light');
        await i18n.toggleLanguage();
        StudentView.renderProfile(container);
      });

      document.getElementById('themeToggleBtn')?.addEventListener('click', () => {
        triggerHaptic('impact', 'light');
        document.body.classList.toggle('dark-mode');
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  }
};
