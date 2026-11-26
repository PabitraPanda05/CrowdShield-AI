const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let detail = "";

    try {
      const body = await response.json();
      detail = body.detail || body.message || "";
    } catch {
      // The response may not contain JSON.
    }

    throw new Error(
      detail ||
        `API request failed: ${response.status} ${response.statusText}`
    );
  }

  return response.json();
}

function buildQuery(params = {}) {
  const query = new URLSearchParams();

  if (params.cameraId) {
    query.set("camera_id", params.cameraId);
  }

  if (params.startTime) {
    query.set("start_time", params.startTime);
  }

  if (params.endTime) {
    query.set("end_time", params.endTime);
  }

  return query.toString();
}

// Alert-specific query parameters.
function buildAlertQuery(filters = {}) {
  const query = new URLSearchParams();

  if (filters.cameraId) {
    query.set("camera_id", filters.cameraId);
  }

  if (filters.riskLevel) {
    query.set("risk_level", filters.riskLevel);
  }

  if (filters.status) {
    query.set("status", filters.status);
  }

  if (filters.limit !== undefined && filters.limit !== null) {
    query.set("limit", String(filters.limit));
  }

  return query.toString();
}

function post(endpoint, payload = {}) {
  return request(endpoint, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export const api = {
  // ==============================
  // SYSTEM HEALTH
  // ==============================

  health() {
    return request("/api/health");
  },

  // ==============================
  // DASHBOARD
  // ==============================

  dashboardSummary() {
    return request("/api/dashboard/summary");
  },

  riskTimeline() {
    return request("/api/risk/timeline");
  },

  alerts(filters = {}) {
    const query = buildAlertQuery(filters);

    return request(
      `/api/alerts${query ? `?${query}` : ""}`
    );
  },

  // ==============================
  // ALERT MANAGEMENT
  // ==============================

  acknowledgeAlert(alertId, payload = {}) {
    return post(
      `/api/alerts/${encodeURIComponent(alertId)}/acknowledge`,
      {
        actor: payload.actor || "operator",
      }
    );
  },

  assignAlert(alertId, payload = {}) {
    return post(
      `/api/alerts/${encodeURIComponent(alertId)}/assign`,
      {
        actor: payload.actor || "operator",
        officer: payload.officer,
      }
    );
  },

  resolveAlert(alertId, payload = {}) {
    return post(
      `/api/alerts/${encodeURIComponent(alertId)}/resolve`,
      {
        actor: payload.actor || "operator",
        note: payload.note || null,
      }
    );
  },

  reopenAlert(alertId, payload = {}) {
    return post(
      `/api/alerts/${encodeURIComponent(alertId)}/reopen`,
      {
        actor: payload.actor || "operator",
      }
    );
  },

  incidentHistory(alertId = null, limit = 200) {
    const query = new URLSearchParams();

    if (alertId) {
      query.set("alert_id", alertId);
    }

    query.set("limit", String(limit));

    return request(
      `/api/incidents/history?${query.toString()}`
    );
  },

  // ==============================
  // CAMERA MANAGEMENT
  // ==============================

  cameras() {
    return request("/api/cameras");
  },

  cameraIntelligence(cameraId) {
    return request(
      `/api/cameras/${encodeURIComponent(cameraId)}/intelligence`
    );
  },

  // ==============================
  // CROWD INTELLIGENCE
  // ==============================

  crowdIntelligence() {
    return request("/api/crowd-intelligence");
  },

  crowdIntelligenceFrames() {
    return request("/api/crowd-intelligence/frames");
  },

  crowdIntelligenceAlerts() {
    return request("/api/crowd-intelligence/alerts");
  },

  crowdFlow() {
    return request("/api/crowd-intelligence/flow");
  },

  // ==============================
  // ROUTE MANAGEMENT
  // ==============================

  simulatedRoute() {
    return request("/api/routes/simulated");
  },

  routeValidation() {
    return request("/api/routes/validation");
  },

  // ==============================
  // DATABASE
  // ==============================

  databaseHealth() {
    return request("/api/database/health");
  },

  databaseSummary() {
    return request("/api/database/summary");
  },

  databaseCameras() {
    return request("/api/database/cameras");
  },

  databaseRisk() {
    return request("/api/database/risk");
  },

  databaseResponse() {
    return request("/api/database/response");
  },

  databaseRuns() {
    return request("/api/database/runs");
  },

  // ==============================
  // HISTORICAL CROWD ANALYTICS
  // ==============================

  crowdHistory(filters = {}) {
    const query = buildQuery(filters);

    return request(
      `/api/crowd-history${query ? `?${query}` : ""}`
    );
  },

  crowdHistorySummary(filters = {}) {
    const query = buildQuery(filters);

    return request(
      `/api/crowd-history/summary${query ? `?${query}` : ""}`
    );
  },
};

export { API_BASE_URL };