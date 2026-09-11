/**
 * Student View Renderer (5 tabs: Home, Grades, Homework, Schedule, Profile)
 * Enhanced with Daily Vibe Selector, Streak/Level hero, AI Study Assistant,
 * 3D Flashcards, and Digital Backpack files.
 */
import { api } from '../api.js';
import { i18n } from '../i18n.js';
import { escapeHtml, triggerHaptic, showToast } from '../utils.js';

export const StudentView = {
  activeVibe: null,

  async renderHome(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const [dashData, gamificationData] = await Promise.all([
        api.getStudentDashboard(),
        api.getGamificationProfile().catch(() => null),
      ]);

      const s = dashData.student || {};
      const streakDays = gamificationData?.streak_days || 1;
      const totalXp = gamificationData?.xp || s.xp || 0;
      const currentLevel = gamificationData?.level || s.level || 1;
      this.activeVibe = gamificationData?.today_vibe || null;

      container.innerHTML = `
        <!-- Hero Editorial Banner -->
        <div class="hero-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <div class="hero-greeting">${escapeHtml(i18n.t('student.greeting', 'Добро пожаловать в Lumina 👋'))}</div>
              <div class="hero-name">${escapeHtml(s.name || 'Ученик')}</div>
            </div>
            <div style="background:rgba(255,255,255,0.2);padding:6px 12px;border-radius:var(--radius-full);font-size:12px;font-weight:700;display:flex;align-items:center;gap:6px;">
              <span>🔥 ${streakDays} ${i18n.t('gamification.streak', 'дней')}</span>
            </div>
          </div>
          <div class="hero-stats">
            <div class="stat-box">
              <span class="stat-label">${escapeHtml(i18n.t('student.class', 'Класс'))}</span>
              <span class="stat-val">${escapeHtml(s.class_name || '—')}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">${escapeHtml(i18n.t('gamification.level', 'Уровень'))}</span>
              <span class="stat-val">Lvl ${currentLevel} (${totalXp} XP)</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">${escapeHtml(i18n.t('student.urgent_hw', 'Дедлайны'))}</span>
              <span class="stat-val">${dashData.urgent_homework_count || 0}</span>
            </div>
          </div>
        </div>

        <!-- Daily Vibe Tracking Bar -->
        <div class="card" style="padding:14px;">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
            <i data-lucide="smile" style="width:16px;height:16px;color:var(--color-accent);" aria-hidden="true"></i>
            <span style="font-size:13px;font-weight:700;">${i18n.t('gamification.vibe_title', 'Твой настрой на сегодня')}</span>
          </div>
          <div class="vibe-bar">
            <button class="vibe-pill ${this.activeVibe === 'energized' ? 'active' : ''}" data-vibe="energized">
              ${i18n.t('gamification.vibe_energized', '⚡ Энергичный')}
            </button>
            <button class="vibe-pill ${this.activeVibe === 'focused' ? 'active' : ''}" data-vibe="focused">
              ${i18n.t('gamification.vibe_focused', '🎯 В фокусе')}
            </button>
            <button class="vibe-pill ${this.activeVibe === 'calm' ? 'active' : ''}" data-vibe="calm">
              ${i18n.t('gamification.vibe_calm', '😌 Спокойный')}
            </button>
            <button class="vibe-pill ${this.activeVibe === 'tired' ? 'active' : ''}" data-vibe="tired">
              ${i18n.t('gamification.vibe_tired', '😴 Уставший')}
            </button>
          </div>
        </div>

        <!-- Study Tools Quick Access Bar -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">
          <button class="card" id="openAiStudyBtn" style="padding:14px;align-items:flex-start;text-align:left;cursor:pointer;border-color:var(--color-primary-subtle);">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
              <i data-lucide="sparkles" style="color:var(--color-primary);width:18px;height:18px;"></i>
              <span style="font-weight:700;font-size:13px;">AI-помощник</span>
            </div>
            <span style="font-size:11px;color:var(--text-muted);">Подсказки без спойлеров</span>
          </button>
          <button class="card" id="openFlashcardsBtn" style="padding:14px;align-items:flex-start;text-align:left;cursor:pointer;border-color:var(--color-accent-subtle);">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
              <i data-lucide="layers" style="color:var(--color-accent);width:18px;height:18px;"></i>
              <span style="font-weight:700;font-size:13px;">Карточки</span>
            </div>
            <span style="font-size:11px;color:var(--text-muted);">Экспресс-повторение</span>
          </button>
        </div>

        <!-- Today's Lessons -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="calendar" aria-hidden="true"></i>
              <span>${escapeHtml(i18n.t('student.today_lessons', 'Уроки на сегодня'))}</span>
            </div>
            <span class="badge badge-info">${dashData.today_lessons.length} ${escapeHtml(i18n.t('common.lessons', 'уроков'))}</span>
          </div>
          <div class="card-body">
            ${dashData.today_lessons.length === 0 ? `<p class="empty-text">${escapeHtml(i18n.t('student.no_lessons_today', 'Сегодня уроков нет'))}</p>` : dashData.today_lessons.map(l => `
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

        <!-- Latest Grade Alert -->
        ${dashData.latest_grade ? `
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                <i data-lucide="award" aria-hidden="true"></i>
                <span>${escapeHtml(i18n.t('student.latest_grade', 'Последняя оценка'))}</span>
              </div>
              <div class="grade-pill grade-${Math.floor(dashData.latest_grade.value)}">${escapeHtml(dashData.latest_grade.raw_display)}</div>
            </div>
            <p style="font-size:13px;color:var(--text-secondary);">${escapeHtml(dashData.latest_grade.type)}: ${escapeHtml(dashData.latest_grade.comment || i18n.t('student.no_comment', 'Без комментария'))}</p>
          </div>
        ` : ''}
      `;

      // Vibe check listeners
      container.querySelectorAll('.vibe-pill').forEach(pill => {
        pill.addEventListener('click', async () => {
          const vibe = pill.getAttribute('data-vibe');
          try {
            triggerHaptic('impact', 'light');
            await api.submitVibe(vibe);
            container.querySelectorAll('.vibe-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            showToast('Настроение записано!', 'success');
          } catch (err) {
            showToast(err.message, 'error');
          }
        });
      });

      // AI Drawer Listener
      container.querySelector('#openAiStudyBtn')?.addEventListener('click', () => {
        triggerHaptic('selection');
        StudentView.openAiStudySheet();
      });

      // Flashcards Listener
      container.querySelector('#openFlashcardsBtn')?.addEventListener('click', () => {
        triggerHaptic('selection');
        StudentView.openFlashcardsModal();
      });

    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  openAiStudySheet() {
    const overlay = document.createElement('div');
    overlay.className = 'lumina-sheet-overlay';
    overlay.innerHTML = `
      <div class="lumina-sheet">
        <div class="lumina-sheet-handle"></div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
          <h3 style="font-size:17px;font-weight:700;">✨ AI-Помощник Lumina</h3>
          <button id="closeAiSheetBtn" style="background:none;border:none;cursor:pointer;color:var(--text-muted);"><i data-lucide="x"></i></button>
        </div>
        <div class="form-group">
          <label class="form-label">Предмет и тема:</label>
          <input type="text" id="aiTopicInput" class="form-input" placeholder="Например: Алгебра, Квадратные уравнения">
        </div>
        <div class="form-group" style="margin-top:8px;">
          <label class="form-label">Твой вопрос или задача:</label>
          <textarea id="aiQuestionInput" class="form-input" rows="3" placeholder="Не могу понять, как раскрыть скобки в упражнении 5..."></textarea>
        </div>
        <button class="btn btn-primary" id="askAiHintBtn" style="width:100%;margin-top:12px;">
          Получить подсказку (без готового решения)
        </button>
        <div id="aiHintResult" style="display:none;margin-top:14px;padding:14px;border-radius:var(--radius-md);background:var(--bg-subtle);border-left:3px solid var(--color-primary);"></div>
      </div>
    `;
    document.body.appendChild(overlay);
    lucide.createIcons();

    overlay.querySelector('#closeAiSheetBtn').addEventListener('click', () => overlay.remove());

    overlay.querySelector('#askAiHintBtn').addEventListener('click', async () => {
      const topic = overlay.querySelector('#aiTopicInput').value.trim() || 'Математика';
      const question = overlay.querySelector('#aiQuestionInput').value.trim();
      if (!question) {
        showToast('Введите текст задачи или вопроса', 'error');
        return;
      }
      const resDiv = overlay.querySelector('#aiHintResult');
      resDiv.style.display = 'block';
      resDiv.innerHTML = '<i data-lucide="loader-2" class="animate-spin" style="width:18px;height:18px;"></i> Думаю над подсказкой...';
      lucide.createIcons();

      try {
        const hintData = await api.getAiHint('Общий', topic, question);
        resDiv.innerHTML = `
          <div style="font-weight:700;font-size:14px;margin-bottom:6px;color:var(--color-primary);">💡 Наводящий совет:</div>
          <p style="font-size:13px;line-height:1.5;margin-bottom:10px;">${escapeHtml(hintData.hint)}</p>
          <div style="font-size:12px;font-weight:600;color:var(--text-secondary);">❓ Подумай над вопросом:</div>
          <p style="font-size:13px;font-style:italic;">${escapeHtml(hintData.thought_question || '')}</p>
        `;
        triggerHaptic('notification', 'success');
      } catch (err) {
        resDiv.innerHTML = `<span style="color:var(--color-danger);font-size:13px;">${escapeHtml(err.message)}</span>`;
      }
    });
  },

  openFlashcardsModal() {
    const overlay = document.createElement('div');
    overlay.className = 'lumina-sheet-overlay';
    overlay.innerHTML = `
      <div class="lumina-sheet">
        <div class="lumina-sheet-handle"></div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
          <h3 style="font-size:17px;font-weight:700;">📚 Экспресс-карточки</h3>
          <button id="closeFcSheetBtn" style="background:none;border:none;cursor:pointer;color:var(--text-muted);"><i data-lucide="x"></i></button>
        </div>
        <div class="flashcard-wrapper" id="activeCard">
          <div class="flashcard-inner" id="cardInner">
            <div class="flashcard-face">
              <span class="badge badge-info" style="margin-bottom:12px;">Физика • 8 класс</span>
              <div class="flashcard-text">Второй закон Ньютона</div>
              <div class="flashcard-hint">Нажмите, чтобы перевернуть</div>
            </div>
            <div class="flashcard-face flashcard-back">
              <span class="badge badge-success" style="margin-bottom:12px;">Формула & Смысл</span>
              <div class="flashcard-text" style="color:var(--color-primary);">F = m · a</div>
              <p style="font-size:12px;color:var(--text-secondary);line-height:1.4;">Сила равна произведению массы тела на его ускорение.</p>
            </div>
          </div>
        </div>
        <div style="display:flex;gap:10px;margin-top:14px;">
          <button class="btn btn-subtle" id="repeatCardBtn" style="flex:1;">Повторить 🔁</button>
          <button class="btn btn-primary" id="knowCardBtn" style="flex:1;">Знаю! ✅</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    lucide.createIcons();

    const cardInner = overlay.querySelector('#cardInner');
    overlay.querySelector('#activeCard').addEventListener('click', () => {
      triggerHaptic('selection');
      cardInner.classList.toggle('flipped');
    });

    overlay.querySelector('#closeFcSheetBtn').addEventListener('click', () => overlay.remove());
    overlay.querySelector('#knowCardBtn').addEventListener('click', () => {
      triggerHaptic('notification', 'success');
      showToast('Отлично! Запомнено (+5 XP)', 'success');
      overlay.remove();
    });
    overlay.querySelector('#repeatCardBtn').addEventListener('click', () => {
      triggerHaptic('impact', 'light');
      cardInner.classList.remove('flipped');
      showToast('Карточка отложена на повторение', 'info');
    });
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
                  <span>${escapeHtml(s.name)}</span>
                </div>
                <span class="badge ${s.gpa >= 4.0 ? 'badge-success' : 'badge-warning'}">GPA: ${escapeHtml(String(s.gpa))}</span>
              </div>
              <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;">
                ${s.grades.map(g => `
                  <div class="grade-pill grade-${Math.floor(g.value)}" title="${escapeHtml(g.comment || '')}">
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
      const homeworkList = await api.getStudentHomework();
      container.innerHTML = `
        <div class="card-header">
          <h2 style="font-size:18px;font-weight:700;">${escapeHtml(i18n.t('student.homework', 'Домашние задания'))}</h2>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${homeworkList.length === 0 ? `<p class="empty-text">${escapeHtml(i18n.t('student.no_homework', 'Заданий нет!'))}</p>` : homeworkList.map(h => `
            <div class="card" style="padding:14px;border-left: 4px solid ${h.status === 'DONE' ? 'var(--color-success)' : 'var(--color-warning)'}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div style="font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;">${escapeHtml(h.subject)}</div>
                  <div style="font-size:15px;font-weight:700;color:var(--text-primary);margin:2px 0;">${escapeHtml(h.title)}</div>
                  <div style="font-size:13px;color:var(--text-secondary);line-height:1.4;">${escapeHtml(h.description || '')}</div>
                  <div style="font-size:11px;color:var(--text-muted);margin-top:8px;">
                    Срок сдачи: ${escapeHtml(h.due_date)}
                  </div>
                </div>
                <button class="hw-checkbox badge ${h.status === 'DONE' ? 'badge-success' : 'badge-warning'}" data-id="${h.id}" data-status="${h.status}" style="cursor:pointer;border:none;padding:6px 10px;font-size:12px;">
                  ${h.status === 'DONE' ? '✓ Сдано' : '○ Сдать'}
                </button>
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
      const [user, gamificationData, backpackFiles] = await Promise.all([
        api.getMe(),
        api.getGamificationProfile().catch(() => null),
        api.getBackpackFiles().catch(() => []),
      ]);

      const initial = (user.first_name || 'U')[0].toUpperCase();
      const achievements = gamificationData?.all_achievements || [];

      container.innerHTML = `
        <div class="card" style="align-items:center;text-align:center;padding:24px;">
          <div style="width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,var(--color-primary),#0284c7);color:#fff;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:800;margin-bottom:12px;box-shadow:var(--shadow-md);">
            ${escapeHtml(initial)}
          </div>
          <h2 style="font-size:18px;font-weight:700;">${escapeHtml(user.first_name)} ${escapeHtml(user.last_name || '')}</h2>
          <span class="role-badge" style="margin-top:6px;">${escapeHtml(user.role)} • ${escapeHtml(user.class_name || '—')}</span>
        </div>

        <!-- Unlocked Achievements -->
        <div class="card">
          <div class="card-title">
            <i data-lucide="trophy" style="color:var(--color-accent);" aria-hidden="true"></i>
            <span>${i18n.t('gamification.achievements', 'Достижения')}</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;">
            ${achievements.map(a => `
              <div style="padding:10px;background:var(--bg-subtle);border-radius:var(--radius-sm);display:flex;align-items:center;gap:8px;">
                <span style="font-size:20px;">${escapeHtml(a.icon || '🏆')}</span>
                <div>
                  <div style="font-size:12px;font-weight:700;">${escapeHtml(a.title_ru || a.code)}</div>
                  <span style="font-size:10px;color:var(--color-primary);font-weight:600;">+${a.xp} XP</span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Digital Backpack Files -->
        <div class="card">
          <div class="card-title">
            <i data-lucide="briefcase" style="color:var(--color-primary);" aria-hidden="true"></i>
            <span>${i18n.t('study.backpack', 'Рюкзак / Учебные материалы')}</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;margin-top:10px;">
            ${backpackFiles.length === 0 ? '<p class="empty-text">Файлов пока нет</p>' : backpackFiles.map(f => `
              <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:var(--bg-subtle);border-radius:var(--radius-sm);">
                <div>
                  <div style="font-size:13px;font-weight:600;">${escapeHtml(f.filename)}</div>
                  <span style="font-size:11px;color:var(--text-muted);">${escapeHtml(f.category || 'Материал')}</span>
                </div>
                <a href="${escapeHtml(f.file_url)}" target="_blank" class="btn btn-subtle" style="padding:4px 10px;font-size:11px;">
                  <i data-lucide="download" style="width:12px;height:12px;"></i> Скачать
                </a>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Manual Invite redemption -->
        <div class="card">
          <div class="card-title">
            <i data-lucide="ticket" aria-hidden="true"></i>
            <span>${escapeHtml(i18n.t('student.invite_title', 'Код приглашения в класс'))}</span>
          </div>
          <p style="font-size:13px;color:var(--text-secondary);margin-bottom:12px;">
            ${escapeHtml(i18n.t('student.invite_desc', 'Если учитель выдал вам персональный код, введите его для привязки к вашему классу:'))}
          </p>
          <div style="display:flex;gap:8px;">
            <input type="text" id="manualInviteInput" class="form-input" placeholder="inv_..." style="flex:1;">
            <button class="btn btn-primary" id="manualInviteSubmitBtn" style="padding:8px 16px;">
              ${escapeHtml(i18n.t('common.confirm', 'Применить'))}
            </button>
          </div>
        </div>

        <!-- Settings -->
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

      document.getElementById('manualInviteSubmitBtn')?.addEventListener('click', async () => {
        const input = document.getElementById('manualInviteInput');
        const token = input?.value.trim();
        if (!token) return;
        try {
          await api.redeemInvite(token);
          showToast('Приглашение успешно активировано!', 'success');
          StudentView.renderProfile(container);
        } catch (err) {
          showToast(err.message, 'error');
        }
      });

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
