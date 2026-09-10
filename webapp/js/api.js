/**
 * Lumina API Client Module
 */
class ApiClient {
  constructor() {
    this.baseUrl = '/api/v1';
    this.token = localStorage.getItem('lumina_token') || null;
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

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.setToken(null);
      // Trigger re-login or demo auth
    }

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { detail: response.statusText };
      }
      throw new Error(errorData.detail || 'API Request Failed');
    }

    return response.json();
  }

  // Auth endpoints
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

  // Student endpoints
  async getStudentDashboard() {
    return this.request('/student/dashboard');
  }

  async getStudentGrades() {
    return this.request('/student/grades');
  }

  async getStudentHomework() {
    return this.request('/student/homework');
  }

  async toggleHomework(hwId, status) {
    return this.request(`/student/homework/${hwId}/status?status_val=${status}`, {
      method: 'PATCH',
    });
  }

  async getStudentSchedule() {
    return this.request('/student/schedule');
  }

  async getStudentAnalytics() {
    return this.request('/student/analytics');
  }

  // Teacher endpoints
  async getTeacherClasses() {
    return this.request('/teacher/classes');
  }

  async getJournal(classId, subjectId) {
    return this.request(`/teacher/journal/${classId}/${subjectId}`);
  }

  async awardGrade(payload) {
    return this.request('/teacher/grades', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateGrade(gradeId, payload) {
    return this.request(`/teacher/grades/${gradeId}`, {
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

  // Admin endpoints
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

  async getFeatureFlags() {
    return this.request('/admin/feature-flags');
  }

  async updateFeatureFlag(flagName, isEnabled) {
    return this.request('/admin/feature-flags', {
      method: 'PATCH',
      body: JSON.stringify({ flag_name: flagName, is_enabled: isEnabled }),
    });
  }

  async createInvite(payload) {
    return this.request('/admin/invites', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
}

export const api = new ApiClient();
