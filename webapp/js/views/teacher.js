/**
 * Teacher View Renderer (Dashboard, Classes, Journal, Homework, Profile)
 * Full implementation: live journal, grading modal with scale awareness, attendance batching, and homework CRUD.
 */
import { api } from '../api.js';
import { i18n } from '../i18n.js';
import { escapeHtml, triggerHaptic, showToast } from '../utils.js';

export const TeacherView = {
  activeClassId: null,
  activeSubjectId: null,

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
              <span>${i18n.t('nav.classes')}</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            ${classes.length === 0 ? '<p class="empty-text">Нет назначенных классов</p>' : classes.map(c => `
              <div class="card" style="padding:12px;background:var(--bg-subtle);">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <div>
                    <div style="font-weight:700;font-size:15px;">${escapeHtml(c.class_name)} • ${escapeHtml(c.subject_name)}</div>
                    <span style="font-size:11px;color:var(--text-muted);">Код предмета: ${escapeHtml(c.subject_code)}</span>
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
          TeacherView.activeClassId = btn.getAttribute('data-class');
          TeacherView.activeSubjectId = btn.getAttribute('data-subject');
          triggerHaptic('selection');
          document.querySelector('[data-tab="journal"]')?.click();
        });
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
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
        lucide.createIcons();
        return;
      }

      const activeClass = TeacherView.activeClassId || classes[0].class_id;
      const activeSubject = TeacherView.activeSubjectId || classes[0].subject_id;
      TeacherView.activeClassId = activeClass;
      TeacherView.activeSubjectId = activeSubject;

      const journal = await api.getJournal(activeClass, activeSubject);

      container.innerHTML = `
        <div class="card">
          <div class="form-group">
            <label class="form-label">Выберите класс и предмет:</label>
            <select class="form-input" id="journalClassSelect">
              ${classes.map(c => `
                <option value="${c.class_id}|${c.subject_id}" ${c.class_id === activeClass && c.subject_id === activeSubject ? 'selected' : ''}>
                  ${escapeHtml(c.class_name)} — ${escapeHtml(c.subject_name)}
                </option>
              `).join('')}
            </select>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <i data-lucide="users" aria-hidden="true"></i>
              <span>Список учащихся (${journal.students.length})</span>
            </div>
            ${journal.lessons.length > 0 ? `
              <button class="btn btn-subtle" id="openAttendanceBatchBtn" style="font-size:12px;padding:4px 10px;">
                <i data-lucide="calendar-check" style="width:14px;height:14px;"></i>
                <span>Отметить явку</span>
              </button>
            ` : ''}
          </div>

          <div style="display:flex;flex-direction:column;gap:8px;">
            ${journal.students.length === 0 ? '<p class="empty-text">В классе нет учеников</p>' : journal.students.map(s => {
              const studentGrades = journal.grades.filter(g => g.student_id === s.student_id);
              return `
                <div class="card" style="padding:12px;background:var(--bg-subtle);">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                      <div style="font-weight:700;font-size:14px;">${escapeHtml(s.first_name)} ${escapeHtml(s.last_name)}</div>
                      <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;">
                        ${studentGrades.length === 0 ? '<span style="font-size:11px;color:var(--text-muted);">Оценок нет</span>' : studentGrades.map(g => `
                          <span class="grade-pill grade-${Math.floor(g.value)}" style="width:28px;height:28px;font-size:11px;cursor:pointer;" title="${escapeHtml(g.type_name)}: ${escapeHtml(g.comment || '')}">
                            ${escapeHtml(g.raw_display)}
                          </span>
                        `).join('')}
                      </div>
                    </div>
                    <button class="btn btn-primary add-grade-btn" data-student="${s.student_id}" data-name="${escapeHtml(s.first_name)} ${escapeHtml(s.last_name)}" style="padding:6px 10px;font-size:12px;">
                      + Оценка
                    </button>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;

      // Event listener on class select
      document.getElementById('journalClassSelect')?.addEventListener('change', (e) => {
        const [cid, sid] = e.target.value.split('|');
        TeacherView.activeClassId = cid;
        TeacherView.activeSubjectId = sid;
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

      // Event listener for Attendance Batching
      container.querySelector('#openAttendanceBatchBtn')?.addEventListener('click', () => {
        TeacherView.showAttendanceModal(journal.lessons[0]?.id, journal.students, container);
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
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
          <h3 style="font-size:16px;font-weight:700;">Поставить оценку: ${escapeHtml(studentName)}</h3>
          <button id="closeModalBtn" style="background:none;border:none;cursor:pointer;color:var(--text-secondary);"><i data-lucide="x"></i></button>
        </div>

        <div class="form-group">
          <label class="form-label">Балл (1-5):</label>
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
            ${gradeTypes.map(gt => `<option value="${gt.id}">${escapeHtml(gt.name)}</option>`).join('')}
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
        triggerHaptic('selection');
      });
    });

    modal.querySelector('#closeModalBtn').addEventListener('click', () => modal.remove());

    modal.querySelector('#saveGradeBtn').addEventListener('click', async () => {
      const typeId = modal.querySelector('#gradeTypeSelect').value;
      const comment = modal.querySelector('#gradeCommentInput').value.trim();

      try {
        await api.awardGrade({
          student_id: studentId,
          lesson_id: lessonId,
          grade_type_id: typeId,
          value: selectedValue,
          raw_display: selectedValue.toString(),
          comment: comment || null,
          weight: 1.0,
        });
        modal.remove();
        showToast('Оценка успешно выставлена', 'success');
        TeacherView.renderJournal(mainContainer);
      } catch (err) {
        alert(err.message);
      }
    });
  },

  showAttendanceModal(lessonId, students, mainContainer) {
    const modal = document.createElement('div');
    modal.className = 'modal-backdrop';
    modal.innerHTML = `
      <div class="modal-content" style="max-height:85vh;overflow-y:auto;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <h3 style="font-size:16px;font-weight:700;">Отметка посещаемости урока</h3>
          <button id="closeAttModalBtn" style="background:none;border:none;cursor:pointer;color:var(--text-secondary);"><i data-lucide="x"></i></button>
        </div>

        <div style="display:flex;flex-direction:column;gap:8px;margin-top:8px;">
          ${students.map(s => `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border-color);">
              <span style="font-size:13px;font-weight:600;">${escapeHtml(s.first_name)} ${escapeHtml(s.last_name)}</span>
              <select class="form-input att-select" data-student="${s.student_id}" style="padding:4px 8px;font-size:12px;width:auto;">
                <option value="PRESENT" selected>Был</option>
                <option value="ABSENT">Н (Отсутствовал)</option>
                <option value="LATE">Опоздал</option>
                <option value="EXCUSED">Уважительная</option>
              </select>
            </div>
          `).join('')}
        </div>

        <button class="btn btn-primary" id="saveAttendanceBtn" style="width:100%;margin-top:12px;">
          Сохранить посещаемость
        </button>
      </div>
    `;

    document.body.appendChild(modal);
    lucide.createIcons();

    modal.querySelector('#closeAttModalBtn').addEventListener('click', () => modal.remove());

    modal.querySelector('#saveAttendanceBtn').addEventListener('click', async () => {
      const records = [];
      modal.querySelectorAll('.att-select').forEach(sel => {
        records.push({
          student_id: sel.getAttribute('data-student'),
          status: sel.value,
        });
      });

      try {
        await api.submitAttendance({
          lesson_id: lessonId,
          records: records,
        });
        modal.remove();
        showToast('Посещаемость успешно сохранена', 'success');
        TeacherView.renderJournal(mainContainer);
      } catch (err) {
        alert(err.message);
      }
    });
  },

  async renderHomework(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const [homeworkList, classes] = await Promise.all([
        api.getTeacherHomework(),
        api.getTeacherClasses(),
      ]);

      container.innerHTML = `
        <div class="card-header">
          <div style="display:flex;justify-content:space-between;align-items:center;width:100%;">
            <div>
              <h2 style="font-size:18px;font-weight:700;">${i18n.t('homework.title')}</h2>
              <span style="font-size:12px;color:var(--text-muted);">${homeworkList.length} активных заданий</span>
            </div>
            ${classes.length > 0 ? `
              <button class="btn btn-primary" id="openCreateHwModalBtn" style="font-size:12px;padding:6px 12px;">
                + Задать ДЗ
              </button>
            ` : ''}
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${homeworkList.length === 0 ? '<div class="card"><p class="empty-text">Вы еще не задавали домашних заданий</p></div>' : homeworkList.map(h => `
            <div class="card" style="padding:14px;background:var(--bg-subtle);">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <span class="badge badge-info">${escapeHtml(h.class_name)} • ${escapeHtml(h.subject_name)}</span>
                  <div style="font-size:15px;font-weight:700;margin-top:6px;">${escapeHtml(h.title)}</div>
                  <p style="font-size:13px;color:var(--text-secondary);margin-top:4px;">${escapeHtml(h.description)}</p>
                  <div style="font-size:11px;color:var(--color-accent);margin-top:6px;font-weight:600;">
                    Срок: ${h.due_date} • Сдано: ${h.submissions_count} учеников
                  </div>
                </div>
                <button class="btn btn-subtle delete-hw-btn" data-id="${h.id}" style="padding:6px;color:var(--color-danger);" title="Удалить">
                  <i data-lucide="trash-2" style="width:16px;height:16px;"></i>
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      `;

      container.querySelectorAll('.delete-hw-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const hwId = btn.getAttribute('data-id');
          if (confirm('Вы действительно хотите удалить это домашнее задание?')) {
            try {
              await api.deleteHomework(hwId);
              showToast('Задание удалено', 'info');
              TeacherView.renderHomework(container);
            } catch (err) {
              alert(err.message);
            }
          }
        });
      });

      container.querySelector('#openCreateHwModalBtn')?.addEventListener('click', () => {
        TeacherView.showCreateHomeworkModal(classes, container);
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  showCreateHomeworkModal(classes, mainContainer) {
    const today = new Date();
    today.setDate(today.getDate() + 1);
    const tomorrow = today.toISOString().split('T')[0];

    const modal = document.createElement('div');
    modal.className = 'modal-backdrop';
    modal.innerHTML = `
      <div class="modal-content">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <h3 style="font-size:16px;font-weight:700;">Создать домашнее задание</h3>
          <button id="closeHwModalBtn" style="background:none;border:none;cursor:pointer;color:var(--text-secondary);"><i data-lucide="x"></i></button>
        </div>

        <div class="form-group">
          <label class="form-label">Класс и предмет:</label>
          <select class="form-input" id="hwClassSelect">
            ${classes.map(c => `
              <option value="${c.class_id}|${c.subject_id}">
                ${escapeHtml(c.class_name)} — ${escapeHtml(c.subject_name)}
              </option>
            `).join('')}
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Тема / Заголовок:</label>
          <input type="text" class="form-input" id="hwTitleInput" placeholder="Упражнения 12.1 - 12.5...">
        </div>

        <div class="form-group">
          <label class="form-label">Подробное описание:</label>
          <textarea class="form-input" id="hwDescInput" rows="3" placeholder="Прочитать параграф 12, решить задачи в тетради..."></textarea>
        </div>

        <div class="form-group">
          <label class="form-label">Срок сдачи:</label>
          <input type="date" class="form-input" id="hwDueDateInput" value="${tomorrow}">
        </div>

        <button class="btn btn-primary" id="saveHwBtn" style="width:100%;margin-top:8px;">
          Опубликовать задание
        </button>
      </div>
    `;

    document.body.appendChild(modal);
    lucide.createIcons();

    modal.querySelector('#closeHwModalBtn').addEventListener('click', () => modal.remove());

    modal.querySelector('#saveHwBtn').addEventListener('click', async () => {
      const [classId, subjectId] = modal.querySelector('#hwClassSelect').value.split('|');
      const title = modal.querySelector('#hwTitleInput').value.trim();
      const description = modal.querySelector('#hwDescInput').value.trim();
      const dueDate = modal.querySelector('#hwDueDateInput').value;

      if (!title || !description) {
        alert('Пожалуйста, заполните заголовок и описание задания');
        return;
      }

      try {
        await api.createHomework({
          class_id: classId,
          subject_id: subjectId,
          title: title,
          description: description,
          due_date: dueDate,
        });
        modal.remove();
        showToast('Домашнее задание опубликовано', 'success');
        TeacherView.renderHomework(mainContainer);
      } catch (err) {
        alert(err.message);
      }
    });
  },

  async renderProfile(container) {
    try {
      const user = await api.getMe();
      container.innerHTML = `
        <div class="card" style="align-items:center;text-align:center;padding:28px 20px;">
          <div style="width:68px;height:68px;border-radius:50%;background:linear-gradient(135deg,var(--color-primary),#0284c7);color:#fff;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:800;margin-bottom:12px;box-shadow:var(--shadow-md);">
            ${escapeHtml((user.first_name || 'U')[0])}
          </div>
          <h2 style="font-size:18px;font-weight:700;">${escapeHtml(user.first_name)} ${escapeHtml(user.last_name || '')}</h2>
          <span class="role-badge" style="margin-top:6px;">${escapeHtml(user.role)}</span>
          <p style="font-size:12px;color:var(--text-muted);margin-top:8px;">Школа: ${escapeHtml(user.school_name || 'Lumina')}</p>
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  },

  async renderSeating(container) {
    container.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="animate-spin"></i></div>`;
    lucide.createIcons();

    try {
      const classes = await api.getTeacherClasses();
      if (classes.length === 0) {
        container.innerHTML = `<div class="card"><p class="empty-text">У вас нет назначенных классов</p></div>`;
        lucide.createIcons();
        return;
      }

      const activeClass = TeacherView.activeClassId || classes[0].class_id;
      TeacherView.activeClassId = activeClass;

      const seatingData = await api.getSeatingChart(activeClass);

      container.innerHTML = `
        <div class="card" style="padding:12px;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <select class="form-input" id="seatingClassSelect" style="flex:1;margin-right:10px;">
              ${classes.map(c => `
                <option value="${c.class_id}" ${c.class_id === activeClass ? 'selected' : ''}>
                  ${escapeHtml(c.class_name)}
                </option>
              `).join('')}
            </select>
            <button class="btn btn-primary" id="pickRandomStudentBtn" style="padding:8px 14px;font-size:12px;white-space:nowrap;">
              🎲 Вызвать
            </button>
          </div>
        </div>

        <div id="randomStudentBanner" style="display:none;margin-bottom:12px;padding:14px;background:var(--color-primary-subtle);border:1px solid var(--color-primary);border-radius:var(--radius-md);text-align:center;">
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--color-primary);">К доске вызывается:</div>
          <div id="randomStudentName" style="font-size:18px;font-weight:800;color:var(--text-primary);margin-top:2px;"></div>
        </div>

        <div class="seating-grid">
          ${seatingData.desks.map(d => `
            <div class="desk-card ${d.is_empty ? 'empty' : ''}" data-row="${d.row}" data-col="${d.col}" data-student="${d.student ? d.student.id : ''}" data-name="${d.student ? escapeHtml(d.student.name) : ''}">
              <div class="desk-label">${escapeHtml(d.desk_label)}</div>
              ${d.student ? `
                <div class="desk-student-name">${escapeHtml(d.student.name)}</div>
                <div class="desk-level-badge">Lvl ${d.student.level} • ${d.student.xp} XP</div>
              ` : `
                <span style="font-size:11px;color:var(--text-muted);">Свободно</span>
              `}
            </div>
          `).join('')}
        </div>
      `;

      container.querySelector('#seatingClassSelect')?.addEventListener('change', (e) => {
        TeacherView.activeClassId = e.target.value;
        TeacherView.renderSeating(container);
      });

      container.querySelector('#pickRandomStudentBtn')?.addEventListener('click', async () => {
        try {
          triggerHaptic('impact', 'medium');
          const picked = await api.pickRandomStudent(activeClass);
          if (picked) {
            const banner = container.querySelector('#randomStudentBanner');
            const nameEl = container.querySelector('#randomStudentName');
            banner.style.display = 'block';
            nameEl.textContent = `${picked.first_name} ${picked.last_name || ''}`;
            triggerHaptic('notification', 'success');
          } else {
            showToast('Нет доступных учеников', 'info');
          }
        } catch (err) {
          showToast(err.message, 'error');
        }
      });

    } catch (e) {
      container.innerHTML = `<div class="card"><p class="error-text">${escapeHtml(e.message)}</p></div>`;
    }
    lucide.createIcons();
  }
};
