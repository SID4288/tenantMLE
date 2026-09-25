import React from "react";
import { useAuth } from "../auth.jsx";
import { ROLES } from "../tokens.js";

export function routeFor(role) {
  switch (role) {
    case ROLES.SUPER_ADMIN:
    case ROLES.ADMIN:
    case ROLES.SUPER_VIEWER:
      return "#/tenants";
    case ROLES.TENANT_ADMIN:
      return "#/courses";
    case ROLES.TENANT_USER:
      return "#/my";
    default:
      return "#/login";
  }
}

export function navFor(role) {
  const items = [{ to: "#/dashboard", label: "Dashboard" }];
  if (role === ROLES.SUPER_ADMIN || role === ROLES.ADMIN || role === ROLES.SUPER_VIEWER) {
    items.push(
      { to: "#/tenants", label: "Tenants" },
      { to: "#/users", label: "Users" },
      { to: "#/courses", label: "Courses" },
      { to: "#/assignments", label: "Assignments" },
      { to: "#/progress", label: "Progress" }
    );
  } else if (role === ROLES.TENANT_ADMIN) {
    items.push(
      { to: "#/courses", label: "Courses" },
      { to: "#/users", label: "Users" },
      { to: "#/assignments", label: "Assignments" },
      { to: "#/progress", label: "Progress" }
    );
  } else if (role === ROLES.TENANT_USER) {
    items.push({ to: "#/my", label: "My courses" }, { to: "#/progress", label: "My progress" });
  }
  return items;
}

export function Layout({ route, children }) {
  const { user, logout } = useAuth();
  const items = navFor(user?.role);
  return (
    <div>
      <header className="topnav">
        <span className="brand">
          <span className="badge" />
          TenantMLE
        </span>
        {items.map((i) => (
          <a key={i.to} className={`nav-link${route === i.to ? " active" : ""}`} href={i.to}>
            {i.label}
          </a>
        ))}
        <span className="spacer" />
        {user && (
          <span className="who">
            {user.username} · {user.role}
            {user.tenant ? ` · tenant ${user.tenant}` : ""}
          </span>
        )}
        {user ? (
          <button className="btn-secondary btn-sm" onClick={logout}>
            Log out
          </button>
        ) : (
          <a className="nav-link" href="#/login">
            Log in
          </a>
        )}
      </header>
      <main>{children}</main>
      <footer className="footer">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span>TenantMLE — multi-tenant learning platform (frontend only).</span>
          <span className="caption">Backend is authoritative for permissions.</span>
        </div>
      </footer>
    </div>
  );
}

export function StatusState({ loading, error, empty, emptyText = "Nothing here yet." }) {
  if (loading) return <p className="muted">Loading…</p>;
  if (error) {
    if (error.kind === "forbidden") return <div className="notice">No access — {error.message}</div>;
    if (error.kind === "notfound") return <div className="notice">Not found — {error.message}</div>;
    if (error.kind === "unauthorized")
      return (
        <div className="notice">
          Session expired — <a href="#/login">log in again</a>.
        </div>
      );
    return <div className="notice">Error — {error.message}</div>;
  }
  if (empty) return <p className="muted">{emptyText}</p>;
  return null;
}

export function ProgressBar({ value, dark = false }) {
  const pct = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div>
      <div className={`pbar${dark ? " dark" : ""}`} role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div style={{ width: `${pct}%` }} />
      </div>
      <div className="caption" style={{ marginTop: 4 }}>{pct}% complete</div>
    </div>
  );
}
