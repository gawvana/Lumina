/**
 * Admin View Renderer (Overview, School, People, Classes, Settings & Feature Flags)
 */
import { api } from '../api.js';
import { i18n } from '../i18n.js';

export const AdminView = {
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

        <div class="card">
          <div class="card-title">
            <i data-lucide="user-plus" aria-hidden="true"></i>
            <span>Генератор приглашений</span>
          </div>
          <div class="form-group">
            <label class="form-label">Роль пользователя:</label>
            <select class="form-input" id="inviteRoleSelect">
              <option value="STUDENT">Ученик</option>
              <option value="TEACHER">Учитель</option>
              <option value="PARENT">Родитель</option>
            </select>
          </div>
          <button class="btn btn-primary" id="generateInviteBtn" style="margin-top:8px;">
            Сгенерировать Deep Link
          </button>
          <div id="inviteResult" style="display:none;margin-top:12px;padding:12px;background:var(--bg-subtle);border-radius:var(--radius-sm);word-break:break-all;font-size:12px;"></div>
        </div>
      `;

      document.getElementById('generateInviteBtn')?.addEventListener('click', async () => {
        const role = document.getElementById('inviteRoleSelect').value;
        try {
          const inv = await api.createInvite({ role, duration_hours: 48, max_uses: 1 });
          const resDiv = document.getElementById('inviteResult');
          resDiv.style.display = 'block';
          resDiv.innerHTML = `
            <strong>Ссылка для приглашения (${inv.role}):</strong><br>
            <a href="${inv.deep_link}" target="_blank" style="color:var(--color-primary);">${inv.deep_link}</a>
            <div style="margin-top:6px;color:var(--text-muted);">Действует до: ${new Date(inv.expires_at).toLocaleString()}</div>
          `;
        } catch (err) {
          alert(err.message);
        }
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${e.message}</p></div>`;
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
                  <div style="font-weight:700;font-size:14px;">${f.flag_name}</div>
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
            AdminView.renderSettings(container);
          } catch (err) {
            alert(err.message);
          }
        });
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${e.message}</p></div>`;
    }
    lucide.createIcons();
  }
};
