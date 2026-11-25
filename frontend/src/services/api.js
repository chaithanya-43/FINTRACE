const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const TOKEN_KEY = "fintrace.access_token";

export function getToken() {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(TOKEN_KEY);
  }
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(message, status, code, details) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request(path, { method = "GET", body, formData, auth = true } = {}) {
  const headers = {};
  const token = getToken();
  if (auth && token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let payload;
  if (formData) {
    payload = formData;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: payload,
    });
  } catch {
    throw new ApiError(
      "Cannot reach the FINTRACE API. Is the backend running?",
      0,
      "network_error",
      null,
    );
  }

  if (response.status === 204) {
    return null;
  }

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const error = data?.error;
    if (response.status === 401) {
      clearToken();
      window.dispatchEvent(new Event("fintrace:unauthorized"));
    }
    throw new ApiError(
      error?.message || `Request failed with status ${response.status}.`,
      response.status,
      error?.code || "http_error",
      error?.details ?? null,
    );
  }

  return data;
}

export const api = {
  register: (payload) =>
    request("/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload) =>
    request("/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => request("/auth/me"),

  dashboardSummary: () => request("/dashboard/summary"),

  listCases: (includeArchived = false) =>
    request(`/cases?include_archived=${includeArchived ? "true" : "false"}`),
  getCase: (caseId) => request(`/cases/${caseId}`),
  caseSummary: (caseId) => request(`/cases/${caseId}/summary`),
  createCase: (payload) => request("/cases", { method: "POST", body: payload }),
  updateCase: (caseId, payload) =>
    request(`/cases/${caseId}`, { method: "PATCH", body: payload }),
  changeCaseStatus: (caseId, internalStatus) =>
    request(`/cases/${caseId}/status`, {
      method: "POST",
      body: { internal_status: internalStatus },
    }),
  archiveCase: (caseId) =>
    request(`/cases/${caseId}/archive`, { method: "POST" }),

  listTransactions: (caseId) => request(`/cases/${caseId}/transactions`),
  createTransaction: (caseId, payload) =>
    request(`/cases/${caseId}/transactions`, { method: "POST", body: payload }),
  updateTransaction: (caseId, transactionId, payload) =>
    request(`/cases/${caseId}/transactions/${transactionId}`, {
      method: "PATCH",
      body: payload,
    }),

  analyze: (caseId) => request(`/cases/${caseId}/analyze`, { method: "POST" }),

  listRules: () => request("/regulatory-rules"),
  activeRegulations: (caseId) => request(`/cases/${caseId}/regulations`),
  runAssessment: (caseId, payload = {}) =>
    request(`/cases/${caseId}/assessments`, { method: "POST", body: payload }),
  listAssessments: (caseId) => request(`/cases/${caseId}/assessments`),
  reviewAssessment: (assessmentId, payload) =>
    request(`/assessments/${assessmentId}/review`, { method: "PATCH", body: payload }),

  listEvidence: (caseId) => request(`/cases/${caseId}/evidence`),
  uploadEvidence: (caseId, file, fields = {}) => {
    const formData = new FormData();
    formData.append("file", file);
    Object.entries(fields).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        formData.append(key, value);
      }
    });
    return request(`/cases/${caseId}/evidence`, { method: "POST", formData });
  },
  verifyEvidence: (caseId, evidenceId) =>
    request(`/cases/${caseId}/evidence/${evidenceId}/verify`, { method: "POST" }),
  signEvidence: (caseId, evidenceId) =>
    request(`/cases/${caseId}/evidence/${evidenceId}/sign`, { method: "POST" }),
  downloadEvidence: async (caseId, evidenceId) => {
    const headers = {};
    if (getToken()) {
      headers.Authorization = `Bearer ${getToken()}`;
    }
    const response = await fetch(
      `${API_BASE_URL}/cases/${caseId}/evidence/${evidenceId}/download`,
      { headers },
    );
    if (!response.ok) {
      throw new ApiError("Could not download this evidence file.", response.status);
    }
    return response.blob();
  },

  roadmap: (caseId) => request(`/cases/${caseId}/roadmap`),
  listActions: (caseId) => request(`/cases/${caseId}/actions`),
  createAction: (caseId, payload) =>
    request(`/cases/${caseId}/actions`, { method: "POST", body: payload }),
  updateAction: (caseId, actionId, payload) =>
    request(`/cases/${caseId}/actions/${actionId}`, {
      method: "PATCH",
      body: payload,
    }),

  listComplaints: (caseId) => request(`/cases/${caseId}/complaints`),
  createComplaint: (caseId, payload) =>
    request(`/cases/${caseId}/complaints`, { method: "POST", body: payload }),
  updateComplaint: (caseId, complaintId, payload) =>
    request(`/cases/${caseId}/complaints/${complaintId}`, {
      method: "PATCH",
      body: payload,
    }),
  complaintHistory: (caseId, complaintId) =>
    request(`/cases/${caseId}/complaints/${complaintId}/history`),
  recordComplaintStatus: (caseId, complaintId, payload) =>
    request(`/cases/${caseId}/complaints/${complaintId}/history`, {
      method: "POST",
      body: payload,
    }),

  caseAudit: (caseId) => request(`/cases/${caseId}/audit`),
};
