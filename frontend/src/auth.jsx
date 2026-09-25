import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { AuthAPI, clearTokens, getAccess, setTokens } from "./api.js";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState("");

  const loadMe = useCallback(async () => {
    if (!getAccess()) {
      setUser(null);
      setAuthLoading(false);
      return null;
    }
    try {
      const me = await AuthAPI.me();
      setUser(me);
      setAuthError("");
      return me;
    } catch (e) {
      if (e.kind === "unauthorized") {
        clearTokens();
        setUser(null);
      } else {
        setAuthError(e.message);
      }
      return null;
    } finally {
      setAuthLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  const login = useCallback(
    async (username, password) => {
      setAuthError("");
      const tokens = await AuthAPI.login(username, password);
      setTokens(tokens);
      setAuthLoading(true);
      const me = await loadMe();
      return me;
    },
    [loadMe]
  );

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    window.location.hash = "#/login";
  }, []);

  // Global 401 -> redirect to login (expired token).
  useEffect(() => {
    const onUnhandled = (e) => {
      const err = e.reason;
      if (err && err.kind === "unauthorized") {
        clearTokens();
        setUser(null);
        window.location.hash = "#/login";
      }
    };
    window.addEventListener("unhandledrejection", onUnhandled);
    const onExpired = () => {
      clearTokens();
      setUser(null);
      setAuthError("Session expired — please log in again.");
      window.location.hash = "#/login";
    };
    window.addEventListener("auth-expired", onExpired);
    return () => {
      window.removeEventListener("unhandledrejection", onUnhandled);
      window.removeEventListener("auth-expired", onExpired);
    };
  }, []);

  return (
    <AuthCtx.Provider value={{ user, authLoading, authError, setAuthError, login, logout, reloadMe: loadMe }}>
      {children}
    </AuthCtx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
