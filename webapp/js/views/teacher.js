/**
 * Teacher View Renderer (Dashboard, Classes, Journal, Homework, Profile)
 */
import { api } from '../api.js';
import { i18n } from '../i18n.js';

export const TeacherView = {
  async renderDashboard(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const classes = await api.getTeacherClasses();
      container.innerHTML = `
        <div class="hero-card">
          <div class="hero-greeting">Кабинет учителя 🧑‍🏫</div>
          <div class="hero-name">Журнал и Уроки</div>
          <div class="hero-stats">
            <div class="stat-box">
              <span class="stat-label">Мои классы</span>
              <span class="stat-val">${classes.length}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Посещаемость</span>
              <span class="stat-val">97%</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="book-open" aria-hidden="true"></i>
              <span>Мои активные классы</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            ${classes.length === 0 ? '<p class="empty-text">Нет назначенных классов</p>' : classes.map(c => `
              <div class="card" style="padding:12px;background:var(--bg-subtle);">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <div>
                    <div style="font-weight:700;font-size:15px;">${c.class_name} • ${c.subject_name}</div>
                    <span style="font-size:11px;color:var(--text-muted);">Код предмета: ${c.subject_code}</span>
                  </div>
                  <button class="btn btn-primary open-journal-btn" data-class="${c.class_id}" data-subject="${c.subject_id}" style="padding:6px 12px;font-size:12px;">
                    В журнал
                  </button>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;

      container.querySelectorAll('.open-journal-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const cid = btn.getAttribute('data-class');
          const sid = btn.getAttribute('data-subject');
          window.activeJournalClass = cid;
          window.activeJournalSubject = sid;
          document.querySelector('[data-tab="journal"]').click();
        });
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${e.message}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderJournal(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const classes = await api.getTeacherClasses();
      if (classes.length === 0) {
        container.innerHTML = `<div class="card"><p class="empty-text">У вас нет назначенных классов</p></div>`;
        return;
      }

      const activeClass = window.activeJournalClass || classes[0].class_id;
      const activeSubject = window.activeJournalSubject || classes[0].subject_id;

      const journal = await api.getJournal(activeClass, activeSubject);

      container.innerHTML = `
        <div class="card">
          <div class="form-group">
            <label class="form-label">Выберите класс и предмет:</label>
            <select class="form-input" id="journalClassSelect">
              ${classes.map(c => `
                <option value="${c.class_id}|${c.subject_id}" ${c.class_id === activeClass && c.subject_id === activeSubject ? 'selected' : ''}>
                  ${c.class_name} — ${c.subject_name}
                </option>
              `).join('')}
            </select>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="users" aria-hidden="true"></i>
              <span>Список учащихся</span>
            </div>
            <span class="badge badge-info">${journal.students.length} учеников</span>
          </div>

          <div style="display:flex;flex-direction:column;gap:8px;">
            ${journal.students.map(s => {
              const studentGrades = journal.grades.filter(g => g.student_id === s.student_id);
              return `
                <div class="card" style="padding:12px;background:var(--bg-subtle);">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                      <div style="font-weight:700;font-size:14px;">${s.first_name} ${s.last_name}</div>
                      <div style="display:flex;gap:4px;margin-top:6px;">
                        ${studentGrades.map(g => `
                          <span class="grade-pill grade-${Math.floor(g.value)}" style="width:28px;height:28px;font-size:12px;" title="${g.type_name}: ${g.comment || ''}">
                            ${g.raw_display}
                          </span>
                        `).join('')}
                      </div>
                    </div>
                    <button class="btn btn-primary add-grade-btn" data-student="${s.student_id}" data-name="${s.first_name} ${s.last_name}" style="padding:6px 10px;font-size:12px;">
                      + Оценка
                    </button>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;

      // Event listener on select
      document.getElementById('journalClassSelect')?.addEventListener('change', (e) => {
        const [cid, sid] = e.target.value.split('|');
        window.activeJournalClass = cid;
        window.activeJournalSubject = sid;
        TeacherView.renderJournal(container);
      });

      // Event listeners on Add Grade
      container.querySelectorAll('.add-grade-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const studentId = btn.getAttribute('data-student');
          const studentName = btn.getAttribute('data-name');
          TeacherView.showGradeModal(studentId, studentName, journal.lessons[0]?.id, journal.grade_types, container);
        });
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${e.message}</p></div>`;
    }
    lucide.createIcons();
  },

  showGradeModal(studentId, studentName, lessonId, gradeTypes, mainContainer) {
    if (!lessonId) {
      alert('Нет активного урока для выставления оценки');
      return;
    }

    const modal = document.createElement('div');
    modal.className = 'modal-backdrop';
    modal.innerHTML = `
      <div class="modal-content">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <h3 style="font-size:16px;font-weight:700;">Поставить оценку: ${studentName}</h3>
          <button id="closeModalBtn" style="background:none;border:none;cursor:pointer;"><i data-lucide="x"></i></button>
        </div>

        <div class="form-group">
          <label class="form-label">Балл:</label>
          <div class="score-selector">
            <button class="score-btn selected" data-val="5">5</button>
            <button class="score-btn" data-val="4">4</button>
            <button class="score-btn" data-val="3">3</button>
            <button class="score-btn" data-val="2">2</button>
            <button class="score-btn" data-val="1">1</button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Тип работы:</label>
          <select class="form-input" id="gradeTypeSelect">
            ${gradeTypes.map(gt => `<option value="${gt.id}">${gt.name}</option>`).join('')}
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Комментарий:</label>
          <input type="text" class="form-input" id="gradeCommentInput" placeholder="Отличная работа у доски...">
        </div>

        <button class="btn btn-primary" id="saveGradeBtn" style="width:100%;margin-top:8px;">
          Сохранить в журнал
        </button>
      </div>
    `;

    document.body.appendChild(modal);
    lucide.createIcons();

    let selectedValue = 5.0;
    modal.querySelectorAll('.score-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        modal.querySelectorAll('.score-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedValue = parseFloat(btn.getAttribute('data-val'));
      });
    });

    modal.querySelector('#closeModalBtn').addEventListener('click', () => modal.remove());

    modal.querySelector('#saveGradeBtn').addEventListener('click', async () => {
      const typeId = modal.querySelector('#gradeTypeSelect').value;
      const comment = modal.querySelector('#gradeCommentInput').value;

      try {
        await api.awardGrade({
          student_id: studentId,
          lesson_id: lessonId,
          grade_type_id: typeId,
          value: selectedValue,
          raw_display: selectedValue.toString(),
          comment: comment,
          weight: 1.0,
        });
        modal.remove();
        TeacherView.renderJournal(mainContainer);
      } catch (err) {
        alert(err.message);
      }
    });
  },

  async renderHomework(container) {
    container.innerHTML = `
      <div class="card-header">
        <h2 style="font-size:18px;font-weight:700;">Управление ДЗ</h2>
      </div>
      <div class="card">
        <p style="font-size:14px;color:var(--text-secondary);">Здесь учитель публикует новые задания и отслеживает статистику сдачи.</p>
      </div>
    `;
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
        <span class="role-badge" style="margin-top:6px;">${user.role}</span>
      </div>
    `;
    lucide.createIcons();
  }
};
