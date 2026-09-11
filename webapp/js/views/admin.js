/**
 * Admin View Renderer (Overview, Academics, People, Invites, Audit Log, Settings & Feature Flags)
 * Complete implementation covering all school administrative workflows.
 */
import { api } from '../api.js';
import { i18n } from '../i18n.js';
import { escapeHtml, triggerHaptic, showToast } from '../utils.js';

export const AdminView = {
  activeSubTab: 'overview',

  async renderOverview(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const stats = await api.getAdminOverview();
      container.innerHTML = `
        <div class="hero-card">
          <div class="hero-greeting">Панель администратора 🏛️</div>
          <div class="hero-name">Управление школой</div>
          <div class="hero-stats">
            <div class="stat-box">
              <span class="stat-label">Учеников</span>
              <span class="stat-val">${stats.total_students}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Учителей</span>
              <span class="stat-val">${stats.total_teachers}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Классов</span>
              <span class="stat-val">${stats.total_classes}</span>
            </div>
          </div>
        </div>

        <!-- Admin Navigation Grid -->
        <div style="display:grid;grid-template-columns:repeat(2, 1fr);gap:10px;margin-bottom:14px;">
          <button class="card admin-nav-card" data-subtab="academics" style="padding:14px;align-items:flex-start;text-align:left;cursor:pointer;">
            <i data-lucide="book-open" style="color:var(--color-primary);margin-bottom:6px;"></i>
            <div style="font-weight:700;font-size:14px;">Классы и предметы</div>
            <span style="font-size:11px;color:var(--text-muted);">Учебный план</span>
          </button>
          <button class="card admin-nav-card" data-subtab="people" style="padding:14px;align-items:flex-start;text-align:left;cursor:pointer;">
            <i data-lucide="users" style="color:var(--color-info);margin-bottom:6px;"></i>
            <div style="font-weight:700;font-size:14px;">Пользователи</div>
            <span style="font-size:11px;color:var(--text-muted);">Ученики, учителя</span>
          </button>
          <button class="card admin-nav-card" data-subtab="invites" style="padding:14px;align-items:flex-start;text-align:left;cursor:pointer;">
            <i data-lucide="user-plus" style="color:var(--color-accent);margin-bottom:6px;"></i>
            <div style="font-weight:700;font-size:14px;">Приглашения</div>
            <span style="font-size:11px;color:var(--text-muted);">Deep link генератор</span>
          </button>
          <button class="card admin-nav-card" data-subtab="audit" style="padding:14px;align-items:flex-start;text-align:left;cursor:pointer;">
            <i data-lucide="shield-check" style="color:var(--color-success);margin-bottom:6px;"></i>
            <div style="font-weight:700;font-size:14px;">Аудит действий</div>
            <span style="font-size:11px;color:var(--text-muted);">Безопасность</span>
          </button>
        </div>

        <!-- Quick Invite Generator -->
        <div class="card">
          <div class="card-title">
            <i data-lucide="key" aria-hidden="true"></i>
            <span>Быстрое приглашение</span>
          </div>
          <div class="form-group" style="margin-top:8px;">
            <label class="form-label">Роль:</label>
            <select class="form-input" id="quickInviteRole">
              <option value="STUDENT">Ученик</option>
              <option value="TEACHER">Учитель</option>
              <option value="PARENT">Родитель</option>
            </select>
          </div>
          <button class="btn btn-primary" id="generateQuickInviteBtn" style="margin-top:10px;width:100%;">
            Сгенерировать Deep Link
          </button>
          <div id="quickInviteResult" style="display:none;margin-top:10px;padding:10px;background:var(--bg-subtle);border-radius:var(--radius-sm);word-break:break-all;font-size:12px;"></div>
        </div>
      `;

      container.querySelectorAll('.admin-nav-card').forEach(btn => {
        btn.addEventListener('click', () => {
          const sub = btn.getAttribute('data-subtab');
          if (sub === 'academics') AdminView.renderAcademics(container);
          else if (sub === 'people') AdminView.renderPeople(container);
          else if (sub === 'invites') AdminView.renderInvites(container);
          else if (sub === 'audit') AdminView.renderAudit(container);
        });
      });

      document.getElementById('generateQuickInviteBtn')?.addEventListener('click', async () => {
        const role = document.getElementById('quickInviteRole').value;
        try {
          const inv = await api.createInvite({ role, duration_hours: 48, max_uses: 1 });
          const resDiv = document.getElementById('quickInviteResult');
          resDiv.style.display = 'block';
          resDiv.innerHTML = `
            <strong>Ссылка для входа (${inv.role}):</strong><br>
            <a href="${inv.deep_link}" target="_blank" style="color:var(--color-primary);font-weight:600;">${inv.deep_link}</a>
            <div style="margin-top:4px;color:var(--text-muted);">Срок: ${new Date(inv.expires_at).toLocaleString()}</div>
          `;
          showToast('Приглашение создано', 'success');
        } catch (err) {
          alert(err.message);
        }
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderAcademics(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const [classes, subjects, curriculum] = await Promise.all([
        api.getClasses(),
        api.getSubjects(),
        api.getCurriculum(),
      ]);

      container.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
          <button class="btn btn-subtle" id="adminBackBtn" style="padding:6px 12px;font-size:12px;">
            <i data-lucide="arrow-left" style="width:14px;height:14px;"></i> Назад
          </button>
          <h2 style="font-size:18px;font-weight:700;">Учебный план школы</h2>
        </div>

        <!-- Classes -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="layers"></i>
              <span>Классы (${classes.length})</span>
            </div>
            <button class="btn btn-primary" id="openAddClassModalBtn" style="font-size:12px;padding:4px 10px;">
              + Класс
            </button>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:8px;">
            ${classes.map(c => `
              <div class="badge badge-info" style="font-size:13px;padding:6px 12px;">
                ${escapeHtml(c.name)} (${c.students_count} уч.)
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Subjects -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="book"></i>
              <span>Предметы (${subjects.length})</span>
            </div>
            <button class="btn btn-primary" id="openAddSubjectModalBtn" style="font-size:12px;padding:4px 10px;">
              + Предмет
            </button>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:8px;">
            ${subjects.map(s => `
              <div class="badge badge-success" style="font-size:13px;padding:6px 12px;">
                ${escapeHtml(s.name)} (${escapeHtml(s.code)})
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Curriculum Assignments -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="link"></i>
              <span>Назначенные учителя (${curriculum.length})</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            ${curriculum.length === 0 ? '<p class="empty-text">Назначений нет</p>' : curriculum.map(link => `
              <div class="card" style="padding:10px 14px;background:var(--bg-subtle);">
                <div style="font-weight:700;font-size:14px;">${escapeHtml(link.class_name)} • ${escapeHtml(link.subject_name)}</div>
                <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">Учитель: ${escapeHtml(link.teacher_name || 'Не назначен')}</div>
              </div>
            `).join('')}
          </div>
        </div>
      `;

      container.querySelector('#adminBackBtn')?.addEventListener('click', () => AdminView.renderOverview(container));
      container.querySelector('#openAddClassModalBtn')?.addEventListener('click', () => AdminView.showAddClassModal(container));
      container.querySelector('#openAddSubjectModalBtn')?.addEventListener('click', () => AdminView.showAddSubjectModal(container));
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  showAddClassModal(mainContainer) {
    const modal = document.createElement('div');
    modal.className = 'modal-backdrop';
    modal.innerHTML = `
      <div class="modal-content">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <h3 style="font-size:16px;font-weight:700;">Добавить класс</h3>
          <button id="closeClassModalBtn" style="background:none;border:none;cursor:pointer;"><i data-lucide="x"></i></button>
        </div>
        <div class="form-group">
          <label class="form-label">Название класса:</label>
          <input type="text" class="form-input" id="newClassName" placeholder="например: 9-А">
        </div>
        <div class="form-group">
          <label class="form-label">Параллель (1-11):</label>
          <input type="number" class="form-input" id="newClassGrade" min="1" max="12" value="7">
        </div>
        <button class="btn btn-primary" id="saveClassBtn" style="margin-top:8px;">Создать класс</button>
      </div>
    `;
    document.body.appendChild(modal);
    lucide.createIcons();

    modal.querySelector('#closeClassModalBtn').addEventListener('click', () => modal.remove());
    modal.querySelector('#saveClassBtn').addEventListener('click', async () => {
      const name = modal.querySelector('#newClassName').value.trim();
      const grade = parseInt(modal.querySelector('#newClassGrade').value, 10);
      if (!name) return alert('Введите название');

      try {
        await api.createClass({ name, grade_level: grade, academic_year: '2026-2027' });
        modal.remove();
        showToast('Класс добавлен', 'success');
        AdminView.renderAcademics(mainContainer);
      } catch (err) {
        alert(err.message);
      }
    });
  },

  showAddSubjectModal(mainContainer) {
    const modal = document.createElement('div');
    modal.className = 'modal-backdrop';
    modal.innerHTML = `
      <div class="modal-content">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <h3 style="font-size:16px;font-weight:700;">Добавить предмет</h3>
          <button id="closeSubModalBtn" style="background:none;border:none;cursor:pointer;"><i data-lucide="x"></i></button>
        </div>
        <div class="form-group">
          <label class="form-label">Название предмета:</label>
          <input type="text" class="form-input" id="newSubName" placeholder="например: Геометрия">
        </div>
        <div class="form-group">
          <label class="form-label">Код (3-5 букв):</label>
          <input type="text" class="form-input" id="newSubCode" placeholder="например: GEOM">
        </div>
        <button class="btn btn-primary" id="saveSubBtn" style="margin-top:8px;">Создать предмет</button>
      </div>
    `;
    document.body.appendChild(modal);
    lucide.createIcons();

    modal.querySelector('#closeSubModalBtn').addEventListener('click', () => modal.remove());
    modal.querySelector('#saveSubBtn').addEventListener('click', async () => {
      const name = modal.querySelector('#newSubName').value.trim();
      const code = modal.querySelector('#newSubCode').value.trim();
      if (!name || !code) return alert('Заполните все поля');

      try {
        await api.createSubject({ name, code });
        modal.remove();
        showToast('Предмет добавлен', 'success');
        AdminView.renderAcademics(mainContainer);
      } catch (err) {
        alert(err.message);
      }
    });
  },

  async renderPeople(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const [teachers, students, parents] = await Promise.all([
        api.getTeachers(),
        api.getStudents(),
        api.getParents(),
      ]);

      container.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
          <button class="btn btn-subtle" id="adminBackBtn" style="padding:6px 12px;font-size:12px;">
            <i data-lucide="arrow-left" style="width:14px;height:14px;"></i> Назад
          </button>
          <h2 style="font-size:18px;font-weight:700;">Пользователи школы</h2>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="graduation-cap"></i>
              <span>Учителя (${teachers.length})</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:6px;">
            ${teachers.map(t => `
              <div style="padding:8px 12px;background:var(--bg-subtle);border-radius:var(--radius-sm);font-size:13px;display:flex;justify-content:space-between;">
                <strong>${escapeHtml(t.name)}</strong>
                <span style="color:var(--text-muted);">${escapeHtml(t.title || 'Учитель')}</span>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="user"></i>
              <span>Ученики (${students.length})</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:6px;">
            ${students.map(s => `
              <div style="padding:8px 12px;background:var(--bg-subtle);border-radius:var(--radius-sm);font-size:13px;display:flex;justify-content:space-between;">
                <strong>${escapeHtml(s.name)}</strong>
                <span class="badge badge-info">${escapeHtml(s.class_name || 'Без класса')}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;

      container.querySelector('#adminBackBtn')?.addEventListener('click', () => AdminView.renderOverview(container));
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderInvites(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const invites = await api.getInvites();

      container.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
          <button class="btn btn-subtle" id="adminBackBtn" style="padding:6px 12px;font-size:12px;">
            <i data-lucide="arrow-left" style="width:14px;height:14px;"></i> Назад
          </button>
          <h2 style="font-size:18px;font-weight:700;">Приглашения школы</h2>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${invites.length === 0 ? '<div class="card"><p class="empty-text">Приглашений пока нет</p></div>' : invites.map(inv => `
            <div class="card" style="padding:12px;background:var(--bg-subtle);">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span class="badge ${inv.is_active ? 'badge-success' : 'badge-warning'}">${inv.role}</span>
                <span style="font-size:11px;color:var(--text-muted);">Использовано: ${inv.current_uses}/${inv.max_uses}</span>
              </div>
              <div style="margin-top:8px;font-size:12px;word-break:break-all;">
                <a href="${inv.deep_link}" target="_blank" style="color:var(--color-primary);font-weight:600;">${inv.deep_link}</a>
              </div>
              <div style="margin-top:4px;font-size:11px;color:var(--text-muted);">
                Истекает: ${new Date(inv.expires_at).toLocaleString()}
              </div>
            </div>
          `).join('')}
        </div>
      `;

      container.querySelector('#adminBackBtn')?.addEventListener('click', () => AdminView.renderOverview(container));
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderAudit(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const logs = await api.getAuditLogs(30);

      container.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
          <button class="btn btn-subtle" id="adminBackBtn" style="padding:6px 12px;font-size:12px;">
            <i data-lucide="arrow-left" style="width:14px;height:14px;"></i> Назад
          </button>
          <h2 style="font-size:18px;font-weight:700;">Журнал аудита</h2>
        </div>

        <div style="display:flex;flex-direction:column;gap:8px;">
          ${logs.length === 0 ? '<div class="card"><p class="empty-text">Логов аудита пока нет</p></div>' : logs.map(log => `
            <div class="card" style="padding:10px 14px;background:var(--bg-subtle);">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span class="badge badge-info">${log.entity_type} • ${log.action}</span>
                <span style="font-size:11px;color:var(--text-muted);">${new Date(log.created_at).toLocaleTimeString()}</span>
              </div>
              <div style="font-size:13px;font-weight:600;margin-top:6px;">${escapeHtml(log.reason || 'Операция')}</div>
            </div>
          `).join('')}
        </div>
      `;

      container.querySelector('#adminBackBtn')?.addEventListener('click', () => AdminView.renderOverview(container));
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderSettings(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const flags = await api.getFeatureFlags();
      container.innerHTML = `
        <div class="card-header">
          <h2 style="font-size:18px;font-weight:700;">Настройки и Feature Flags</h2>
        </div>
        <p style="font-size:13px;color:var(--text-secondary);margin-bottom:12px;">
          Включение и выключение модулей школы без необходимости перезапуска или деплоя.
        </p>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${flags.map(f => `
            <div class="card" style="padding:12px;background:var(--bg-subtle);">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div style="font-weight:700;font-size:14px;">${escapeHtml(f.flag_name)}</div>
                  <span style="font-size:11px;color:var(--text-muted);">${f.is_enabled ? 'Включено' : 'Выключено'}</span>
                </div>
                <button class="btn ${f.is_enabled ? 'btn-primary' : 'btn-subtle'} toggle-flag-btn" data-name="${f.flag_name}" data-enabled="${f.is_enabled}" style="padding:6px 14px;font-size:12px;">
                  ${f.is_enabled ? 'ON' : 'OFF'}
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      `;

      container.querySelectorAll('.toggle-flag-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const name = btn.getAttribute('data-name');
          const cur = btn.getAttribute('data-enabled') === 'true';
          try {
            await api.updateFeatureFlag(name, !cur);
            showToast('Статус флага обновлен', 'success');
            AdminView.renderSettings(container);
          } catch (err) {
            alert(err.message);
          }
        });
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  }
};
