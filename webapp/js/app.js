/**
 * Lumina Mini App Main Application Controller
 * Handles Telegram WebApp lifecycle, Role-Based Navigation, i18n, and View Routing.
 */
import { api } from './api.js';
import { i18n } from './i18n.js';
import { StudentView } from './views/student.js';
import { TeacherView } from './views/teacher.js';
import { ParentView } from './views/parent.js';
import { AdminView } from './views/admin.js';
import { triggerHaptic, showToast } from './utils.js';

class LuminaApp {
  constructor() {
    this.currentRole = 'STUDENT';
    this.currentTab = 'home';
    this.container = document.getElementById('viewContainer');
    this.bottomNav = document.getElementById('bottomNav');
    this.roleBadge = document.getElementById('roleBadge');
    this.tg = window.Telegram?.WebApp;
  }

  async init() {
    // 1. Initialize Telegram WebApp SDK if available
    if (this.tg) {
      try {
        this.tg.ready();
        this.tg.expand();
        if (this.tg.colorScheme === 'dark') {
          document.body.classList.add('dark-mode');
        }
      } catch (e) {
        console.warn('Telegram WebApp SDK init error', e);
      }
    }

    // 2. Initialize i18n
    await i18n.init();

    // 3. Setup language toggle button in header
    document.getElementById('langToggleBtn')?.addEventListener('click', async () => {
      triggerHaptic('impact', 'light');
      await i18n.toggleLanguage();
      this.buildNav();
      this.renderCurrentView();
    });

    // 4. Setup Dev Role Switcher (strictly local development only)
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const devSwitcherBar = document.getElementById('devSwitcherBar');
    if (!isLocalhost && devSwitcherBar) {
      devSwitcherBar.style.display = 'none';
    } else if (devSwitcherBar) {
      devSwitcherBar.style.display = 'flex';
      const roleSwitcher = document.getElementById('roleSwitcher');
      if (roleSwitcher) {
        roleSwitcher.addEventListener('change', async (e) => {
          await this.switchDevRole(e.target.value);
        });
      }
    }

    // 5. Initial auth or dev session
    await this.setupSession();
    this.buildNav();
    this.renderCurrentView();
  }

  async setupSession() {
    // If running inside Telegram with initData
    if (this.tg && this.tg.initData) {
      try {
        const authData = await api.authenticateTelegram(this.tg.initData);
        this.currentRole = authData.user.role;
        this.currentTab = this.getDefaultTabForRole(this.currentRole);
      } catch (e) {
        console.error('Telegram authentication failed', e);
        showToast(e.message, 'error');
      }
    } else {
      // Local development fallback
      try {
        if (api.token) {
          const me = await api.getMe();
          this.currentRole = me.role;
          this.currentTab = this.getDefaultTabForRole(this.currentRole);
        } else {
          await this.switchDevRole('STUDENT');
        }
      } catch (e) {
        await this.switchDevRole('STUDENT');
      }
    }

    this.updateRoleBadge();
  }

  updateRoleBadge() {
    if (this.roleBadge) {
      this.roleBadge.textContent = this.currentRole;
      this.roleBadge.className = 'role-badge';
      if (this.currentRole === 'ADMIN') this.roleBadge.classList.add('badge-danger');
      else if (this.currentRole === 'TEACHER') this.roleBadge.classList.add('badge-info');
      else if (this.currentRole === 'PARENT') this.roleBadge.classList.add('badge-warning');
      else this.roleBadge.classList.add('badge-success');
    }
  }

  async switchDevRole(role) {
    this.currentRole = role;
    this.updateRoleBadge();

    try {
      const res = await fetch(`/api/v1/auth/dev-token?role=${encodeURIComponent(role)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (res.ok) {
        const data = await res.json();
        api.setToken(data.access_token);
      } else {
        console.warn('Dev token request not available on server');
      }
    } catch (e) {
      console.warn('Failed to switch dev role token', e);
    }

    this.currentTab = this.getDefaultTabForRole(role);
    this.buildNav();
    this.renderCurrentView();
  }

  getDefaultTabForRole(role) {
    if (role === 'TEACHER') return 'dashboard';
    if (role === 'ADMIN') return 'overview';
    if (role === 'PARENT') return 'overview';
    return 'home';
  }

  buildNav() {
    if (!this.bottomNav) return;

    let items = [];
    if (this.currentRole === 'STUDENT') {
      items = [
        { id: 'home', label: i18n.t('nav.home', 'Главная'), icon: 'home' },
        { id: 'grades', label: i18n.t('nav.grades', 'Оценки'), icon: 'award' },
        { id: 'homework', label: i18n.t('nav.homework', 'Домашка'), icon: 'check-square' },
        { id: 'schedule', label: i18n.t('nav.schedule', 'Расписание'), icon: 'calendar' },
        { id: 'profile', label: i18n.t('nav.profile', 'Профиль'), icon: 'user' },
      ];
    } else if (this.currentRole === 'TEACHER') {
      items = [
        { id: 'dashboard', label: i18n.t('nav.dashboard', 'Классы'), icon: 'layout-dashboard' },
        { id: 'journal', label: i18n.t('nav.journal', 'Журнал'), icon: 'clipboard-list' },
        { id: 'homework', label: i18n.t('nav.homework', 'ДЗ'), icon: 'file-text' },
        { id: 'profile', label: i18n.t('nav.profile', 'Профиль'), icon: 'user' },
      ];
    } else if (this.currentRole === 'PARENT') {
      items = [
        { id: 'overview', label: i18n.t('nav.overview', 'Сводка'), icon: 'layout-dashboard' },
        { id: 'grades', label: i18n.t('nav.grades', 'Оценки'), icon: 'award' },
        { id: 'attendance', label: i18n.t('nav.attendance', 'Посещаемость'), icon: 'calendar-check' },
        { id: 'homework', label: i18n.t('nav.homework', 'ДЗ'), icon: 'check-square' },
        { id: 'schedule', label: i18n.t('nav.schedule', 'Расписание'), icon: 'calendar' },
        { id: 'profile', label: i18n.t('nav.profile', 'Профиль'), icon: 'user' },
      ];
    } else if (this.currentRole === 'ADMIN') {
      items = [
        { id: 'overview', label: i18n.t('nav.overview', 'Школа'), icon: 'bar-chart-3' },
        { id: 'settings', label: i18n.t('nav.settings', 'Настройки'), icon: 'sliders' },
      ];
    }

    this.bottomNav.innerHTML = items.map(item => `
      <button class="nav-item ${item.id === this.currentTab ? 'active' : ''}" data-tab="${item.id}">
        <i data-lucide="${item.icon}" aria-hidden="true"></i>
        <span>${item.label}</span>
      </button>
    `).join('');

    lucide.createIcons();

    this.bottomNav.querySelectorAll('.nav-item').forEach(btn => {
      btn.addEventListener('click', () => {
        triggerHaptic('selection');
        this.bottomNav.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentTab = btn.getAttribute('data-tab');
        this.renderCurrentView();
      });
    });
  }

  renderCurrentView() {
    if (!this.container) return;

    if (this.currentRole === 'STUDENT') {
      switch (this.currentTab) {
        case 'home': StudentView.renderHome(this.container); break;
        case 'grades': StudentView.renderGrades(this.container); break;
        case 'homework': StudentView.renderHomework(this.container); break;
        case 'schedule': StudentView.renderSchedule(this.container); break;
        case 'profile': StudentView.renderProfile(this.container); break;
        default: StudentView.renderHome(this.container);
      }
    } else if (this.currentRole === 'TEACHER') {
      switch (this.currentTab) {
        case 'dashboard': TeacherView.renderDashboard(this.container); break;
        case 'journal': TeacherView.renderJournal(this.container); break;
        case 'homework': TeacherView.renderHomework(this.container); break;
        case 'profile': TeacherView.renderProfile(this.container); break;
        default: TeacherView.renderDashboard(this.container);
      }
    } else if (this.currentRole === 'PARENT') {
      switch (this.currentTab) {
        case 'overview': ParentView.renderOverview(this.container); break;
        case 'grades': ParentView.renderGrades(this.container); break;
        case 'attendance': ParentView.renderAttendance(this.container); break;
        case 'homework': ParentView.renderHomework(this.container); break;
        case 'schedule': ParentView.renderSchedule(this.container); break;
        case 'profile': ParentView.renderProfile(this.container); break;
        default: ParentView.renderOverview(this.container);
      }
    } else if (this.currentRole === 'ADMIN') {
      switch (this.currentTab) {
        case 'overview': AdminView.renderOverview(this.container); break;
        case 'settings': AdminView.renderSettings(this.container); break;
        default: AdminView.renderOverview(this.container);
      }
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const app = new LuminaApp();
  window.luminaApp = app;
  app.init();
});
