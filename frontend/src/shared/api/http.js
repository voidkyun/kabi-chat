const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function buildUrl(path) {
  if (!API_BASE_URL) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
}

async function parseJson(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  return JSON.parse(text);
}

function extractErrorMessage(payload, status) {
  if (typeof payload?.detail === "string" && payload.detail) {
    return payload.detail;
  }

  if (typeof payload?.error === "string" && payload.error) {
    return payload.error;
  }

  if (payload && typeof payload === "object") {
    for (const value of Object.values(payload)) {
      if (typeof value === "string" && value) {
        return value;
      }
      if (Array.isArray(value) && typeof value[0] === "string" && value[0]) {
        return value[0];
      }
    }
  }

  return `Request failed with status ${status}`;
}

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export async function requestJson(path, options = {}) {
  const { accessToken, body, headers, ...rest } = options;
  const requestHeaders = new Headers(headers ?? {});

  if (accessToken) {
    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  const isJsonBody = body !== undefined && !(body instanceof FormData);
  if (isJsonBody && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(buildUrl(path), {
    credentials: "include",
    ...rest,
    headers: requestHeaders,
    body: isJsonBody ? JSON.stringify(body) : body,
  });
  const payload = await parseJson(response);

  if (!response.ok) {
    const message = extractErrorMessage(payload, response.status);
    throw new ApiError(message, response.status, payload);
  }

  return payload;
}
