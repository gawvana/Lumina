/**
 * Lumina Client-Side Internationalization (i18n) Module
 */
class I18nManager {
  constructor() {
    this.currentLang = localStorage.getItem('lumina_lang') || 'ru';
    this.translations = {};
  }

  async init() {
    await this.loadLocale(this.currentLang);
  }

  async loadLocale(lang) {
    this.currentLang = lang;
    localStorage.setItem('lumina_lang', lang);
    try {
      const res = await fetch(`/api/v1/shared/locales/${lang}`);
      if (res.ok) {
        this.translations = await res.json();
      }
    } catch (e) {
      console.warn('Failed to fetch remote translations, using fallback', e);
    }
    this.updateDOM();
  }

  t(key, params = {}) {
    const keys = key.split('.');
    let val = this.translations;
    for (const k of keys) {
      if (val && typeof val === 'object' && k in val) {
        val = val[k];
      } else {
        return key;
      }
    }

    if (typeof val === 'string' && params) {
      return val.replace(/\{(\w+)\}/g, (match, paramKey) => {
        return params[paramKey] !== undefined ? params[paramKey] : match;
      });
    }
    return val || key;
  }

  updateDOM() {
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      if (key) {
        el.textContent = this.t(key);
      }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (key) {
        el.setAttribute('placeholder', this.t(key));
      }
    });

    // Update lang button text
    const langBtn = document.getElementById('langToggleBtn');
    if (langBtn) {
      langBtn.textContent = this.currentLang === 'ru' ? '🇺🇿 UZ' : '🇷🇺 RU';
    }
  }

  toggleLanguage() {
    const next = this.currentLang === 'ru' ? 'uz' : 'ru';
    return this.loadLocale(next);
  }
}

export const i18n = new I18nManager();
