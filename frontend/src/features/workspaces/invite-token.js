const PENDING_WORKSPACE_INVITE_KEY = "kabi-chat.pending-workspace-invite";

export function getWorkspaceInviteTokenFromLocation() {
  const params = new URLSearchParams(window.location.search);
  return params.get("invite_token")?.trim() || "";
}

export function persistPendingWorkspaceInviteToken(token) {
  if (!token) {
    return;
  }
  window.sessionStorage.setItem(PENDING_WORKSPACE_INVITE_KEY, token);
}

export function loadPendingWorkspaceInviteToken() {
  return window.sessionStorage.getItem(PENDING_WORKSPACE_INVITE_KEY)?.trim() || "";
}

export function clearPendingWorkspaceInviteToken() {
  window.sessionStorage.removeItem(PENDING_WORKSPACE_INVITE_KEY);
}

export function stripWorkspaceInviteTokenFromLocation() {
  const url = new URL(window.location.href);
  if (!url.searchParams.has("invite_token")) {
    return;
  }
  url.searchParams.delete("invite_token");
  const query = url.searchParams.toString();
  const nextUrl = `${url.pathname}${query ? `?${query}` : ""}${url.hash}`;
  window.history.replaceState({}, document.title, nextUrl);
}

export function buildWorkspaceInviteUrl(token) {
  const url = new URL(window.location.href);
  url.search = "";
  url.hash = "";
  url.searchParams.set("invite_token", token);
  return url.toString();
}
