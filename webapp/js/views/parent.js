/**
 * Parent View Renderer (Overview, Grades, Attendance, Homework, Schedule, Absence Notes)
 * Full implementation with child switching and digital absence note submission.
 */
import { api } from '../api.js';
import { i18n } from '../i18n.js';
import { escapeHtml, triggerHaptic, showToast } from '../utils.js';

export const ParentView = {
  activeChildId: null,

  async getSelectedChildId() {
    if (this.activeChildId) return this.activeChildId;
    try {
      const children = await api.getParentChildren();
      if (children.length > 0) {
        this.activeChildId = children[0].student_id;
        return this.activeChildId;
      }
    } catch (e) {
      console.error('Failed to load children', e);
    }
    return null;
  },

  renderChildSelector(children, container, onSelect) {
    if (!children || children.length <= 1) return '';

    return `
      <div class="card" style="padding:10px 14px;margin-bottom:12px;background:var(--bg-subtle);">
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <span style="font-size:12px;font-weight:700;color:var(--text-secondary);">${i18n.t('parent.select_child')}:</span>
          <select id="parentChildSelect" style="background:var(--bg-surface);border:1px solid var(--border-color);border-radius:var(--radius-sm);padding:6px 10px;font-size:13px;font-weight:600;color:var(--text-primary);">
            ${children.map(c => `
              <option value="${c.student_id}" ${c.student_id === this.activeChildId ? 'selected' : ''}>
                ${escapeHtml(c.name)} (${escapeHtml(c.class_name || '')})
              </option>
            `).join('')}
          </select>
        </div>
      </div>
    `;
  },

  attachChildSelectorListener(container, reRenderFn) {
    const sel = container.querySelector('#parentChildSelect');
    if (sel) {
      sel.addEventListener('change', (e) => {
        this.activeChildId = e.target.value;
        triggerHaptic('selection');
        reRenderFn(container);
      });
    }
  },

  async renderOverview(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const children = await api.getParentChildren();
      if (!children || children.length === 0) {
        container.innerHTML = `
          <div class="card" style="text-align:center;padding:32px;">
            <i data-lucide="users" style="width:40px;height:40px;color:var(--text-muted);margin-bottom:12px;"></i>
            <h3 style="font-size:16px;font-weight:700;">Нет привязанных детей</h3>
            <p style="font-size:13px;color:var(--text-secondary);margin-top:6px;">
              Обратитесь к классному руководителю для получения персонального инвайта родителя.
            </p>
          </div>
        `;
        lucide.createIcons();
        return;
      }

      const childId = await this.getSelectedChildId();
      const currentChild = children.find(c => c.student_id === childId) || children[0];
      this.activeChildId = currentChild.student_id;

      const overview = await api.getChildOverview(this.activeChildId);

      container.innerHTML = `
        ${this.renderChildSelector(children, container, this.renderOverview.bind(this))}

        <div class="hero-card">
          <div class="hero-greeting">Кабинет родителя 👨‍👩‍👧‍👦</div>
          <div class="hero-name">${escapeHtml(currentChild.name)}</div>
          <div class="hero-stats">
            <div class="stat-box">
              <span class="stat-label">Класс</span>
              <span class="stat-val">${escapeHtml(currentChild.class_name || '—')}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Средний балл</span>
              <span class="stat-val">${overview.gpa || '0.0'}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Оценок</span>
              <span class="stat-val">${overview.recent_grades.length}</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="award" aria-hidden="true"></i>
              <span>${i18n.t('parent.recent_grades')}</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            ${overview.recent_grades.length === 0 ? '<p class="empty-text">Оценок пока нет</p>' : overview.recent_grades.map(g => `
              <div class="card" style="padding:10px 14px;background:var(--bg-subtle);">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <div>
                    <div style="font-weight:700;font-size:14px;">${escapeHtml(g.subject)}</div>
                    <span style="font-size:11px;color:var(--text-muted);">${escapeHtml(g.type)} • ${g.date}</span>
                  </div>
                  <div class="grade-pill grade-${Math.floor(g.value)}" style="width:32px;height:32px;font-size:13px;">
                    ${escapeHtml(g.raw_display)}
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;

      this.attachChildSelectorListener(container, this.renderOverview.bind(this));
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderGrades(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const children = await api.getParentChildren();
      if (!children.length) return;
      const childId = await this.getSelectedChildId();

      const grades = await api.getChildGrades(childId);

      // Group grades by subject
      const bySubject = {};
      grades.forEach(g => {
        if (!bySubject[g.subject]) bySubject[g.subject] = [];
        bySubject[g.subject].push(g);
      });

      container.innerHTML = `
        ${this.renderChildSelector(children, container, this.renderGrades.bind(this))}

        <div class="card-header">
          <h2 style="font-size:18px;font-weight:700;">${i18n.t('nav.grades')}</h2>
        </div>

        <div style="display:flex;flex-direction:column;gap:12px;">
          ${Object.keys(bySubject).length === 0 ? '<p class="empty-text">Оценок пока нет</p>' : Object.entries(bySubject).map(([sub, gList]) => {
            const avg = roundAvg(gList.map(item => item.value));
            return `
              <div class="card">
                <div class="card-header">
                  <div class="card-title">
                    <i data-lucide="book-open" aria-hidden="true"></i>
                    <span>${escapeHtml(sub)}</span>
                  </div>
                  <div class="badge badge-info">Ср: ${avg}</div>
                </div>
                <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;">
                  ${gList.map(g => `
                    <div class="grade-pill grade-${Math.floor(g.value)}" style="width:32px;height:32px;font-size:13px;" title="${escapeHtml(g.type)} (${g.date}) - ${escapeHtml(g.comment || '')}">
                      ${escapeHtml(g.raw_display)}
                    </div>
                  `).join('')}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;

      this.attachChildSelectorListener(container, this.renderGrades.bind(this));
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderAttendance(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const children = await api.getParentChildren();
      if (!children.length) return;
      const childId = await this.getSelectedChildId();

      const [records, notes] = await Promise.all([
        api.getChildAttendance(childId),
        api.getParentAbsenceNotes(),
      ]);

      container.innerHTML = `
        ${this.renderChildSelector(children, container, this.renderAttendance.bind(this))}

        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div style="font-weight:700;font-size:16px;">${i18n.t('attendance.title')}</div>
              <span style="font-size:12px;color:var(--text-muted);">История посещений и пропусков</span>
            </div>
            <button class="btn btn-primary" id="openAbsenceNoteModalBtn" style="font-size:12px;padding:6px 12px;">
              + Записка
            </button>
          </div>
        </div>

        ${notes.length > 0 ? `
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                <i data-lucide="file-text" aria-hidden="true"></i>
                <span>Поданные записки</span>
              </div>
            </div>
            <div style="display:flex;flex-direction:column;gap:8px;">
              ${notes.map(n => `
                <div class="card" style="padding:10px 14px;background:var(--bg-subtle);">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                      <div style="font-weight:700;font-size:13px;">${n.date_from} — ${n.date_to}</div>
                      <span style="font-size:11px;color:var(--text-secondary);">${escapeHtml(n.reason)}</span>
                    </div>
                    <span class="badge ${n.status === 'APPROVED' ? 'badge-success' : 'badge-warning'}">${n.status}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}

        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="calendar-check" aria-hidden="true"></i>
              <span>Записи уроков</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            ${records.length === 0 ? '<p class="empty-text">Записей о посещаемости нет</p>' : records.map(r => {
              let badgeClass = 'badge-success';
              if (r.status === 'ABSENT') badgeClass = 'badge-danger';
              else if (r.status === 'LATE') badgeClass = 'badge-warning';
              else if (r.status === 'EXCUSED') badgeClass = 'badge-info';

              return `
                <div class="card" style="padding:10px 14px;background:var(--bg-subtle);">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                      <div style="font-weight:700;font-size:14px;">${escapeHtml(r.subject)}</div>
                      <span style="font-size:11px;color:var(--text-muted);">${r.date} ${r.note ? '• ' + escapeHtml(r.note) : ''}</span>
                    </div>
                    <span class="badge ${badgeClass}">${r.status}</span>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;

      this.attachChildSelectorListener(container, this.renderAttendance.bind(this));

      container.querySelector('#openAbsenceNoteModalBtn')?.addEventListener('click', () => {
        ParentView.showAbsenceNoteModal(childId, container);
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  showAbsenceNoteModal(childId, mainContainer) {
    const today = new Date().toISOString().split('T')[0];

    const modal = document.createElement('div');
    modal.className = 'modal-backdrop';
    modal.innerHTML = `
      <div class="modal-content">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <h3 style="font-size:16px;font-weight:700;">Подать записку об отсутствии</h3>
          <button id="closeAbsenceModalBtn" style="background:none;border:none;cursor:pointer;color:var(--text-secondary);">
            <i data-lucide="x"></i>
          </button>
        </div>

        <div class="form-group">
          <label class="form-label">${i18n.t('attendance.date_from')}:</label>
          <input type="date" class="form-input" id="noteDateFrom" value="${today}">
        </div>

        <div class="form-group">
          <label class="form-label">${i18n.t('attendance.date_to')}:</label>
          <input type="date" class="form-input" id="noteDateTo" value="${today}">
        </div>

        <div class="form-group">
          <label class="form-label">${i18n.t('attendance.reason')}:</label>
          <textarea class="form-input" id="noteReason" rows="3" placeholder="Укажите уважительную причину (болезнь, семейные обстоятельства)..."></textarea>
        </div>

        <button class="btn btn-primary" id="submitNoteBtn" style="width:100%;margin-top:8px;">
          ${i18n.t('attendance.submit_note')}
        </button>
      </div>
    `;

    document.body.appendChild(modal);
    lucide.createIcons();

    modal.querySelector('#closeAbsenceModalBtn').addEventListener('click', () => modal.remove());

    modal.querySelector('#submitNoteBtn').addEventListener('click', async () => {
      const dateFrom = modal.querySelector('#noteDateFrom').value;
      const dateTo = modal.querySelector('#noteDateTo').value;
      const reason = modal.querySelector('#noteReason').value.trim();

      if (!reason) {
        alert('Пожалуйста, укажите причину отсутствия');
        return;
      }

      if (dateFrom > dateTo) {
        alert('Дата начала не может быть позже даты окончания');
        return;
      }

      try {
        await api.submitAbsenceNote({
          student_id: childId,
          date_from: dateFrom,
          date_to: dateTo,
          reason: reason,
        });
        modal.remove();
        showToast(i18n.t('parent.absence_success') || 'Записка отправлена', 'success');
        ParentView.renderAttendance(mainContainer);
      } catch (err) {
        alert(err.message);
      }
    });
  },

  async renderHomework(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const children = await api.getParentChildren();
      if (!children.length) return;
      const childId = await this.getSelectedChildId();

      const hwList = await api.getChildHomework(childId);

      container.innerHTML = `
        ${this.renderChildSelector(children, container, this.renderHomework.bind(this))}

        <div class="card-header">
          <h2 style="font-size:18px;font-weight:700;">${i18n.t('parent.child_homework')}</h2>
          <span class="badge badge-info">${hwList.length} заданий</span>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${hwList.length === 0 ? '<p class="empty-text">Заданий нет</p>' : hwList.map(hw => `
            <div class="hw-item ${hw.status === 'DONE' ? 'done' : ''}">
              <div class="hw-checkbox ${hw.status === 'DONE' ? 'checked' : ''}" style="cursor:default;">
                ${hw.status === 'DONE' ? '<i data-lucide="check" style="width:14px;height:14px;"></i>' : ''}
              </div>
              <div class="hw-content">
                <div style="font-size:11px;font-weight:700;color:var(--color-primary);text-transform:uppercase;">${escapeHtml(hw.subject)}</div>
                <div class="hw-title">${escapeHtml(hw.title)}</div>
                <p style="font-size:12px;color:var(--text-secondary);margin-top:2px;">${escapeHtml(hw.description)}</p>
                <div class="hw-date">Срок: ${hw.due_date} • <span class="badge ${hw.status === 'DONE' ? 'badge-success' : (hw.status === 'OVERDUE' ? 'badge-danger' : 'badge-warning')}">${hw.status}</span></div>
              </div>
            </div>
          `).join('')}
        </div>
      `;

      this.attachChildSelectorListener(container, this.renderHomework.bind(this));
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderSchedule(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const children = await api.getParentChildren();
      if (!children.length) return;
      const childId = await this.getSelectedChildId();

      const lessons = await api.getChildSchedule(childId);

      container.innerHTML = `
        ${this.renderChildSelector(children, container, this.renderSchedule.bind(this))}

        <div class="card-header">
          <h2 style="font-size:18px;font-weight:700;">${i18n.t('parent.child_schedule')}</h2>
        </div>

        <div style="display:flex;flex-direction:column;gap:8px;">
          ${lessons.length === 0 ? '<p class="empty-text">Расписание не сформировано</p>' : lessons.map(l => `
            <div class="lesson-card">
              <div class="lesson-period">${l.period}</div>
              <div class="lesson-details">
                <div class="lesson-subject">${escapeHtml(l.subject)}</div>
                <div class="lesson-meta">
                  <span><i data-lucide="map-pin" style="width:12px;height:12px;display:inline;"></i> Каб. ${escapeHtml(l.room || '—')}</span>
                  <span>${l.date}</span>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;

      this.attachChildSelectorListener(container, this.renderSchedule.bind(this));
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderProfile(container) {
    try {
      const user = await api.getMe();
      const initial = (user.first_name || 'P')[0].toUpperCase();
      container.innerHTML = `
        <div class="card" style="align-items:center;text-align:center;padding:24px;">
          <div style="width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,var(--color-primary),#0284c7);color:#fff;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:800;margin-bottom:12px;">
            ${escapeHtml(initial)}
          </div>
          <h2 style="font-size:18px;font-weight:700;">${escapeHtml(user.first_name)} ${escapeHtml(user.last_name || '')}</h2>
          <span class="role-badge" style="margin-top:6px;">${escapeHtml(user.role)} • ${escapeHtml(user.school_name || 'Lumina')}</span>
        </div>

        <div class="card">
          <div class="card-title">
            <i data-lucide="settings" aria-hidden="true"></i>
            <span>${escapeHtml(i18n.t('common.settings', 'Настройки'))}</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border-color);">
            <span style="font-size:14px;font-weight:600;">${escapeHtml(i18n.t('settings.language', 'Язык приложения'))}</span>
            <button class="lang-btn" id="parentLangBtn">Сменить (RU/UZ)</button>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;">
            <span style="font-size:14px;font-weight:600;">${escapeHtml(i18n.t('settings.dark_mode', 'Темная тема'))}</span>
            <button class="btn btn-subtle" id="parentThemeToggleBtn" style="padding:6px 12px;font-size:12px;">${escapeHtml(i18n.t('settings.toggle', 'Переключить'))}</button>
          </div>
        </div>
      `;

      document.getElementById('parentLangBtn')?.addEventListener('click', async () => {
        triggerHaptic('impact', 'light');
        await i18n.toggleLanguage();
        ParentView.renderProfile(container);
      });

      document.getElementById('parentThemeToggleBtn')?.addEventListener('click', () => {
        triggerHaptic('impact', 'light');
        document.body.classList.toggle('dark-mode');
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },
};

function roundAvg(arr) {
  if (!arr || !arr.length) return '0.0';
  const s = arr.reduce((acc, v) => acc + v, 0);
  return (s / arr.length).toFixed(2);
}
