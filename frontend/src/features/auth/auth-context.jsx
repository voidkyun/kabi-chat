import { createContext, useCallback, useContext, useMemo, useState } from "react";

import { requestJson } from "../../shared/api/http";
import { demoUser } from "../../shared/data/demo-data";

const AuthContext = createContext(null);

async function fetchCurrentUser(accessToken) {
  return requestJson("/auth/me", {
    accessToken,
  });
}

export function AuthProvider({ children }) {
  const [status, setStatus] = useState("anonymous");
  const [mode, setMode] = useState("none");
  const [accessToken, setAccessToken] = useState("");
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");

  const clearAuth = useCallback(() => {
    setStatus("anonymous");
    setMode("none");
    setAccessToken("");
    setUser(null);
  }, []);

  const loginWithAccessToken = useCallback(async (token) => {
    setStatus("loading");
    setError("");

    try {
      const me = await fetchCurrentUser(token);
      setAccessToken(token);
      setUser({
        id: me.id,
        username: me.username,
        display_name: me.display_name,
        avatar_url: me.avatar_url,
        discord_user_id: me.discord_user_id,
      });
      setMode("api");
      setStatus("authenticated");
    } catch (loginError) {
      clearAuth();
      setError(loginError.message);
    }
  }, [clearAuth]);

  const refreshAccessToken = useCallback(async () => {
    const refreshed = await requestJson("/auth/token/refresh", {
      method: "POST",
    });
    setAccessToken(refreshed.access_token);
    return refreshed.access_token;
  }, []);

  const apiRequest = useCallback(async (path, options = {}) => {
    const runRequest = (token) =>
      requestJson(path, {
        ...options,
        accessToken: token,
      });

    try {
      return await runRequest(accessToken);
    } catch (requestError) {
      if (requestError.status !== 401 || mode !== "api") {
        throw requestError;
      }

      try {
        const nextToken = await refreshAccessToken();
        return await runRequest(nextToken);
      } catch (refreshError) {
        clearAuth();
        throw refreshError;
      }
    }
  }, [accessToken, clearAuth, mode, refreshAccessToken]);

  const startDiscordLogin = useCallback(async () => {
    setStatus("loading");
    setError("");

    try {
      const loginPayload = await requestJson("/auth/discord/login");
      window.location.assign(loginPayload.authorization_url);
    } catch (loginError) {
      clearAuth();
      setError(loginError.message);
    }
  }, [clearAuth]);

  const useDemoSession = useCallback(() => {
    setAccessToken("");
    setUser(demoUser);
    setMode("demo");
    setStatus("authenticated");
    setError("");
  }, []);

  const logout = useCallback(async () => {
    if (mode === "api") {
      try {
        await requestJson("/auth/logout", {
          method: "POST",
        });
      } catch {
        // Ignore logout cleanup failures and clear local state.
      }
    }

    clearAuth();
    setError("");
  }, [clearAuth, mode]);

  const value = useMemo(() => ({
    accessToken,
    apiRequest,
    error,
    loginWithAccessToken,
    logout,
    mode,
    startDiscordLogin,
    status,
    useDemoSession,
    user,
  }), [accessToken, apiRequest, error, loginWithAccessToken, logout, mode, startDiscordLogin, status, useDemoSession, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return value;
}
