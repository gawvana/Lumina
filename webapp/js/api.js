/**
 * Lumina API Client Module
 * Supports timeouts, aborts, centralized 401 handling, and full 4-role methods.
 */
class ApiClient {
  constructor() {
    this.baseUrl = '/api/v1';
    this.token = localStorage.getItem('lumina_token') || null;
    this.defaultTimeoutMs = 10000; // 10 seconds
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('lumina_token', token);
    } else {
      localStorage.removeItem('lumina_token');
    }
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.defaultTimeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers,
        signal: controller.signal,
      });

      if (response.status === 401) {
        this.setToken(null);
      }

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch (e) {
          errorData = { detail: response.statusText || 'Request failed' };
        }
        throw new Error(errorData.detail || 'API Request Failed');
      }

      return await response.json();
    } catch (err) {
      if (err.name === 'AbortError') {
        throw new Error('Запрос превысил лимит времени ожидания (Timeout)');
      }
      throw err;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // ==================== Auth Endpoints ====================
  async authenticateTelegram(initData, inviteToken = null) {
    const data = await this.request('/auth/telegram-webapp', {
      method: 'POST',
      body: JSON.stringify({ init_data: initData, invite_token: inviteToken }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async getMe() {
    return this.request('/auth/me');
  }

  async redeemInvite(inviteToken) {
    return this.request('/auth/redeem-invite', {
      method: 'POST',
      body: JSON.stringify({ invite_token: inviteToken }),
    });
  }

  // ==================== Student Endpoints ====================
  async getStudentDashboard() {
    return this.request('/student/dashboard');
  }

  async getStudentGrades(studentId = null) {
    const q = studentId ? `?student_id=${encodeURIComponent(studentId)}` : '';
    return this.request(`/student/grades${q}`);
  }

  async getStudentHomework() {
    return this.request('/student/homework');
  }

  async toggleHomework(hwId, status) {
    return this.request(`/student/homework/${encodeURIComponent(hwId)}/status?status_val=${encodeURIComponent(status)}`, {
      method: 'PATCH',
    });
  }

  async getStudentSchedule() {
    return this.request('/student/schedule');
  }

  async getStudentAnalytics() {
    return this.request('/student/analytics');
  }

  // ==================== Teacher Endpoints ====================
  async getTeacherClasses() {
    return this.request('/teacher/classes');
  }

  async getJournal(classId, subjectId) {
    return this.request(`/teacher/journal/${encodeURIComponent(classId)}/${encodeURIComponent(subjectId)}`);
  }

  async awardGrade(payload) {
    return this.request('/teacher/grades', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateGrade(gradeId, payload) {
    return this.request(`/teacher/grades/${encodeURIComponent(gradeId)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async submitAttendance(payload) {
    return this.request('/teacher/attendance', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getTeacherHomework() {
    return this.request('/teacher/homework');
  }

  async createHomework(payload) {
    return this.request('/teacher/homework', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateHomework(hwId, payload) {
    return this.request(`/teacher/homework/${encodeURIComponent(hwId)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteHomework(hwId) {
    return this.request(`/teacher/homework/${encodeURIComponent(hwId)}`, {
      method: 'DELETE',
    });
  }

  // ==================== Parent Endpoints ====================
  async getParentChildren() {
    return this.request('/parent/children');
  }

  async getChildOverview(studentId) {
    return this.request(`/parent/child/${encodeURIComponent(studentId)}/overview`);
  }

  async getChildGrades(studentId) {
    return this.request(`/parent/child/${encodeURIComponent(studentId)}/grades`);
  }

  async getChildAttendance(studentId) {
    return this.request(`/parent/child/${encodeURIComponent(studentId)}/attendance`);
  }

  async getChildHomework(studentId) {
    return this.request(`/parent/child/${encodeURIComponent(studentId)}/homework`);
  }

  async getChildSchedule(studentId) {
    return this.request(`/parent/child/${encodeURIComponent(studentId)}/schedule`);
  }

  async submitAbsenceNote(payload) {
    return this.request('/parent/absence-notes', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getParentAbsenceNotes() {
    return this.request('/parent/absence-notes');
  }

  // ==================== Admin Endpoints ====================
  async getAdminOverview() {
    return this.request('/admin/overview');
  }

  async getClasses() {
    return this.request('/admin/classes');
  }

  async createClass(payload) {
    return this.request('/admin/classes', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getSubjects() {
    return this.request('/admin/subjects');
  }

  async createSubject(payload) {
    return this.request('/admin/subjects', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getTeachers() {
    return this.request('/admin/teachers');
  }

  async getStudents(classId = null) {
    const q = classId ? `?class_id=${encodeURIComponent(classId)}` : '';
    return this.request(`/admin/students${q}`);
  }

  async getParents() {
    return this.request('/admin/parents');
  }

  async getCurriculum() {
    return this.request('/admin/curriculum');
  }

  async assignCurriculum(payload) {
    return this.request('/admin/curriculum/assign', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getInvites() {
    return this.request('/admin/invites');
  }

  async createInvite(payload) {
    return this.request('/admin/invites', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getFeatureFlags() {
    return this.request('/admin/feature-flags');
  }

  async updateFeatureFlag(flagName, isEnabled, config = null) {
    return this.request('/admin/feature-flags', {
      method: 'PATCH',
      body: JSON.stringify({ flag_name: flagName, is_enabled: isEnabled, config }),
    });
  }

  async getAuditLogs(limit = 50, offset = 0, entityType = null) {
    let q = `?limit=${limit}&offset=${offset}`;
    if (entityType) {
      q += `&entity_type=${encodeURIComponent(entityType)}`;
    }
    return this.request(`/admin/audit-logs${q}`);
  }
}

export const api = new ApiClient();
