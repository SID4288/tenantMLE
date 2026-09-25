import React, { useEffect, useState } from "react";
import { AuthAPI, TenantsAPI } from "../api.js";

// Public registration page (hash route #/register).
// Two paths, matching the backend's anonymous endpoints:
// - "Join an Organization" -> POST /api/auth/register/ (TENANT_USER)
// - "Create an Organization" -> POST /api/auth/tenant-application/ (PENDING)
export default function Register() {
  const [mode, setMode] = useState("join");

  return (
    <div>
      <section className="hero">
        <h1>JOIN THE CURRENT</h1>
        <p>
          Register as a learner in an existing organization, or apply to
          create a new one. Approval comes first — courses come later.
        </p>
      </section>

      <div className="section">
        <h2>Register</h2>
        <p className="lede">
          Pick a path. Both are public — no login needed.
        </p>

        <div className="form-card">
          <div className="row">
            <button
              type="button"
              className={
                mode === "join" ? "btn-primary btn-sm" : "btn-secondary-light btn-sm"
              }
              onClick={() => setMode("join")}
            >
              Join an Organization
            </button>
            <button
              type="button"
              className={
                mode === "create" ? "btn-primary btn-sm" : "btn-secondary-light btn-sm"
              }
              onClick={() => setMode("create")}
            >
              Create an Organization
            </button>
          </div>

          {mode === "join" ? <JoinForm /> : <CreateForm />}
        </div>

        {mode === "create" && <StatusCheck />}

        <p className="caption" style={{ marginTop: 16 }}>
          Already have an account? <a href="#/login">Log in →</a>
        </p>
      </div>
    </div>
  );
}

function JoinForm() {
  const [tenants, setTenants] = useState([]);
  const [loadingTenants, setLoadingTenants] = useState(true);
  const [loadErr, setLoadErr] = useState("");

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenant, setTenant] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState("");

  useEffect(() => {
    let alive = true;
    TenantsAPI.publicList()
      .then((list) => alive && setTenants(Array.isArray(list) ? list : []))
      .catch((e) => alive && setLoadErr(e.message))
      .finally(() => alive && setLoadingTenants(false));
    return () => {
      alive = false;
    };
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    setDone("");
    try {
      const created = await AuthAPI.register({
        username,
        email,
        password,
        tenant: Number(tenant),
      });
      setDone(
        `Welcome, ${created.username} — learner account created. You can now log in.`
      );
      setUsername("");
      setEmail("");
      setPassword("");
      setTenant("");
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} style={{ marginTop: 16 }}>
      <label className="lbl">Username</label>
      <input
        className="input"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        autoComplete="username"
        required
      />

      <label className="lbl">Email</label>
      <input
        className="input"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoComplete="email"
        required
      />

      <label className="lbl">Password (min 8 characters)</label>
      <input
        className="input"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        autoComplete="new-password"
        minLength={8}
        required
      />

      <label className="lbl">Organization</label>
      {loadingTenants ? (
        <p className="muted">Loading organizations…</p>
      ) : loadErr ? (
        <p className="err">{loadErr}</p>
      ) : (
        <select
          className="select"
          value={tenant}
          onChange={(e) => setTenant(e.target.value)}
          required
        >
          <option value="">Select organization…</option>
          {tenants.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      )}

      <p className="caption">
        You join as a learner (TENANT_USER). Only approved organizations are listed.
      </p>

      {err && <p className="err">{err}</p>}
      {done && (
        <div className="notice">
          {done} <a href="#/login">Log in →</a>
        </div>
      )}

      <div className="row" style={{ marginTop: 16 }}>
        <button className="btn-primary" disabled={busy || loadingTenants} type="submit">
          {busy ? "Joining…" : "Join organization"}
        </button>
      </div>
    </form>
  );
}

function CreateForm() {
  const [orgName, setOrgName] = useState("");
  const [adminName, setAdminName] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    setDone("");
    try {
      const res = await AuthAPI.applyTenant({
        organization_name: orgName,
        admin_name: adminName,
        admin_email: adminEmail,
      });
      setDone(
        `Application received for "${res.tenant.name}". It is pending approval — ` +
          `you will be able to log in as ${res.user.username} once approved.`
      );
      setOrgName("");
      setAdminName("");
      setAdminEmail("");
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} style={{ marginTop: 16 }}>
      <label className="lbl">Organization name</label>
      <input
        className="input"
        value={orgName}
        onChange={(e) => setOrgName(e.target.value)}
        placeholder="Acme Academy"
        required
      />

      <label className="lbl">Admin name (login username)</label>
      <input
        className="input"
        value={adminName}
        onChange={(e) => setAdminName(e.target.value)}
        autoComplete="username"
        required
      />

      <label className="lbl">Admin email</label>
      <input
        className="input"
        type="email"
        value={adminEmail}
        onChange={(e) => setAdminEmail(e.target.value)}
        autoComplete="email"
        required
      />

      <p className="caption">
        Creates a pending organization with you as its admin. No password is set
        yet and login stays disabled until a Super Admin approves.
      </p>

      {err && <p className="err">{err}</p>}
      {done && <div className="notice">{done}</div>}

      <div className="row" style={{ marginTop: 16 }}>
        <button className="btn-primary" disabled={busy} type="submit">
          {busy ? "Applying…" : "Apply to create organization"}
        </button>
      </div>
    </form>
  );
}

function StatusCheck() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);

  async function onCheck(e) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    setResult(null);
    try {
      const res = await AuthAPI.applicationStatus({ admin_email: email });
      setResult(res);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="form-card" style={{ marginTop: 24 }}>
      <h3 style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 400, margin: "0 0 8px 0" }}>
        Check application status
      </h3>
      <p className="muted">
        Applied already? Enter your admin email. If approved, your one-time
        temporary password appears here — exactly once.
      </p>

      <form onSubmit={onCheck}>
        <label className="lbl">Admin email</label>
        <input
          className="input"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          required
        />

        {err && <p className="err">{err}</p>}

        {result && (
          <div className="notice">
            <p>
              <strong>{result.tenant?.name}</strong> — {result.status}
              <br />
              {result.detail}
            </p>
            {result.temp_password && (
              <p style={{ marginTop: 8 }}>
                Temporary password: <code>{result.temp_password}</code>
                <br />
                <a href="#/login">Log in now and change it →</a>
              </p>
            )}
          </div>
        )}

        <div className="row" style={{ marginTop: 16 }}>
          <button className="btn-secondary-light" disabled={busy} type="submit">
            {busy ? "Checking…" : "Check status"}
          </button>
        </div>
      </form>
    </div>
  );
}
