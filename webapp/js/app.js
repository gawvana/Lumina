/**
 * Lumina Mini App Main Application Controller
 */
import { api } from './api.js';
import { i18n } from './i18n.js';
import { StudentView } from './views/student.js';
import { TeacherView } from './views/teacher.js';
import { AdminView } from './views/admin.js';

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
      await i18n.toggleLanguage();
      this.renderCurrentView();
    });

    // 4. Setup Dev Role Switcher
    const roleSwitcher = document.getElementById('roleSwitcher');
    if (roleSwitcher) {
      roleSwitcher.addEventListener('change', async (e) => {
        await this.switchDevRole(e.target.value);
      });
    }

    // 5. Initial auth or dev session
    await this.setupSession();
    this.buildNav();
    this.renderCurrentView();
  }

  async setupSession() {
    // If running in real Telegram with initData
    if (this.tg && this.tg.initData) {
      try {
        const authData = await api.authenticateTelegram(this.tg.initData);
        this.currentRole = authData.user.role;
      } catch (e) {
        console.error('Telegram authentication failed', e);
      }
    } else {
      // Dev mode: check existing me or use default demo student
      try {
        if (api.token) {
          const me = await api.getMe();
          this.currentRole = me.role;
        } else {
          // Dev mock login as student
          await this.switchDevRole('STUDENT');
        }
      } catch (e) {
        await this.switchDevRole('STUDENT');
      }
    }

    if (this.roleBadge) {
      this.roleBadge.textContent = this.currentRole;
    }
  }

  async switchDevRole(role) {
    this.currentRole = role;
    if (this.roleBadge) {
      this.roleBadge.textContent = role;
    }

    // Simulate switching JWT token by generating mock initData for role
    const tgIdMap = { STUDENT: 2001, TEACHER: 1002, ADMIN: 1001, PARENT: 3001 };
    const tgId = tgIdMap[role] || 2001;

    try {
      // In dev environment, request auth endpoint with synthetic test signature
      const res = await fetch(`/api/v1/auth/telegram-webapp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          init_data: `auth_date=${Math.floor(Date.now()/1000)}&query_id=DEV&user={"id":${tgId},"first_name":"${role}","language_code":"ru"}&hash=dev_bypass`,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        api.setToken(data.access_token);
      }
    } catch (e) {
      // Fallback
    }

    this.currentTab = this.getDefaultTabForRole(role);
    this.buildNav();
    this.renderCurrentView();
  }

  getDefaultTabForRole(role) {
    if (role === 'TEACHER') return 'dashboard';
    if (role === 'ADMIN') return 'overview';
    return 'home';
  }

  buildNav() {
    if (!this.bottomNav) return;

    let items = [];
    if (this.currentRole === 'STUDENT') {
      items = [
        { id: 'home', label: 'Главная', icon: 'home' },
        { id: 'grades', label: 'Оценки', icon: 'award' },
        { id: 'homework', label: 'Домашка', icon: 'check-square' },
        { id: 'schedule', label: 'Расписание', icon: 'calendar' },
        { id: 'profile', label: 'Профиль', icon: 'user' },
      ];
    } else if (this.currentRole === 'TEACHER') {
      items = [
        { id: 'dashboard', label: 'Дашборд', icon: 'layout-dashboard' },
        { id: 'classes', label: 'Классы', icon: 'book-open' },
        { id: 'journal', label: 'Журнал', icon: 'clipboard-list' },
        { id: 'homework', label: 'ДЗ', icon: 'file-text' },
        { id: 'profile', label: 'Профиль', icon: 'user' },
      ];
    } else if (this.currentRole === 'ADMIN') {
      items = [
        { id: 'overview', label: 'Обзор', icon: 'bar-chart-3' },
        { id: 'settings', label: 'Настройки', icon: 'sliders' },
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
      }
    } else if (this.currentRole === 'TEACHER') {
      switch (this.currentTab) {
        case 'dashboard': TeacherView.renderDashboard(this.container); break;
        case 'classes': TeacherView.renderDashboard(this.container); break;
        case 'journal': TeacherView.renderJournal(this.container); break;
        case 'homework': TeacherView.renderHomework(this.container); break;
        case 'profile': TeacherView.renderProfile(this.container); break;
      }
    } else if (this.currentRole === 'ADMIN') {
      switch (this.currentTab) {
        case 'overview': AdminView.renderOverview(this.container); break;
        case 'settings': AdminView.renderSettings(this.container); break;
      }
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const app = new LuminaApp();
  app.init();
});
