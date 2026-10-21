/**
 * API service for communicating with FastAPI backend.
 * Automatically injects X-Telegram-Init-Data header.
 */

const API_BASE = ''; // Relative path, handled by Vite proxy in dev or FastAPI in prod

function buildHeaders(initData) {
  const headers = {
    'Content-Type': 'application/json',
  };
  if (initData) {
    headers['X-Telegram-Init-Data'] = initData;
  }
  return headers;
}

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'Request failed';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    }
    const err = new Error(errorDetail);
    err.status = response.status;
    throw err;
  }
  return response.json();
}

export const api = {
  // Client endpoints
  async getActiveProject(initData) {
    const response = await fetch(`${API_BASE}/api/client/projects/active`, {
      method: 'GET',
      headers: buildHeaders(initData),
    });
    return handleResponse(response);
  },

  async approveMilestone(initData, milestoneId, signatureData, deviceInfo = null) {
    const response = await fetch(`${API_BASE}/api/client/milestones/${milestoneId}/approve`, {
      method: 'POST',
      headers: buildHeaders(initData),
      body: JSON.stringify({
        signature_data: signatureData,
        device_info: deviceInfo || { user_agent: navigator.userAgent },
      }),
    });
    return handleResponse(response);
  },

  async createTicket(initData, { milestoneId, type, message, attachmentUrl }) {
    const response = await fetch(`${API_BASE}/api/client/tickets`, {
      method: 'POST',
      headers: buildHeaders(initData),
      body: JSON.stringify({
        milestone_id: milestoneId || null,
        type: type || 'REVISION',
        message: message,
        attachment_url: attachmentUrl || null,
      }),
    });
    return handleResponse(response);
  },

  // Admin endpoints
  async getAdminProjects(initData) {
    const response = await fetch(`${API_BASE}/api/admin/projects`, {
      method: 'GET',
      headers: buildHeaders(initData),
    });
    return handleResponse(response);
  },

  async updateMilestoneStatus(initData, milestoneId, status) {
    const response = await fetch(`${API_BASE}/api/admin/milestones/${milestoneId}/status`, {
      method: 'PATCH',
      headers: buildHeaders(initData),
      body: JSON.stringify({ status }),
    });
    return handleResponse(response);
  },

  async updateTicketStatus(initData, ticketId, status) {
    const response = await fetch(`${API_BASE}/api/admin/tickets/${ticketId}/status`, {
      method: 'PATCH',
      headers: buildHeaders(initData),
      body: JSON.stringify({ status }),
    });
    return handleResponse(response);
  },
};
