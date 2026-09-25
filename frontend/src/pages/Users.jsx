import React, { useState } from "react";
import { useAuth } from "../auth.jsx";
import { useQuery, useStore } from "../store.jsx";
import { StatusState } from "../components/Layout.jsx";
import { ROLES } from "../tokens.js";

// User management. Tenant Admins create TENANT_USERs (tenant auto-scoped
// server-side); platform roles manage broadly (tenant required for
// tenant roles). List refreshes automatically after mutations.
export default function Users() {
  const { user } = useAuth();
  const { data, loading, error } = useQuery("users");
  const tenantsQ = useQuery("tenants");
  const { createUser, deleteUser } = useStore();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(ROLES.TENANT_USER);
  const [tenant, setTenant] = useState("");
  const [busy, setBusy] = useState(false);
  const [formErr, setFormErr] = useState("");

  const list = Array.isArray(data) ? data : [];
  const isTenantAdmin = user?.role === ROLES.TENANT_ADMIN;
  const canCreate =
    user?.role === ROLES.SUPER_ADMIN || user?.role === ROLES.ADMIN || isTenantAdmin;

  async function onCreate(e) {
    e.preventDefault();
    setBusy(true);
    setFormErr("");
    try {
      const payload = { username, email, password, role: isTenantAdmin ? ROLES.TENANT_USER : role };
      if (!isTenantAdmin && tenant) payload.tenant = Number(tenant);
      await createUser(payload);
      setUsername("");
      setEmail("");
      setPassword("");
    } catch (err) {
      setFormErr(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id) {
    if (!window.confirm("Delete this user?")) return;
    try {
      await deleteUser(id);
    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <div className="section">
      <h2>Manage users</h2>
      <p className="lede">
        {isTenantAdmin ? "Learners in your tenant. New users join your tenant automatically." : "All users by role. Tenant roles require a tenant."}
      </p>
      <StatusState loading={loading} error={error} empty={list.length === 0} emptyText="No users visible." />
      <table className="tbl">
        <thead>
          <tr><th>Username</th><th>Email</th><th>Role</th><th>Tenant</th><th></th></tr>
        </thead>
        <tbody>
          {list.map((u) => (
            <tr key={u.id}>
              <td>{u.username}</td>
              <td>{u.email}</td>
              <td>{u.role}</td>
              <td>{u.tenant ?? "—"}</td>
              <td>
                {canCreate && <button className="btn-secondary-light btn-sm" onClick={() => onDelete(u.id)}>Delete</button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {canCreate && (
        <div className="form-card" style={{ marginTop: 24 }}>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 400, margin: 0 }}>Add user</h3>
          <form onSubmit={onCreate}>
            <label className="lbl">Username</label>
            <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} required />
            <label className="lbl">Email</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <label className="lbl">Password</label>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            {!isTenantAdmin && (
              <>
                <label className="lbl">Role</label>
                <select className="select" value={role} onChange={(e) => setRole(e.target.value)}>
                  <option value={ROLES.TENANT_USER}>TENANT_USER (learner)</option>
                  <option value={ROLES.TENANT_ADMIN}>TENANT_ADMIN (publisher)</option>
                  <option value={ROLES.ADMIN}>ADMIN</option>
                </select>
                <label className="lbl">Tenant (required for tenant roles)</label>
                <select className="select" value={tenant} onChange={(e) => setTenant(e.target.value)}>
                  <option value="">Select tenant…</option>
                  {(Array.isArray(tenantsQ.data) ? tenantsQ.data : []).map((t) => (
                    <option key={t.id} value={t.id}>{t.name} (id {t.id})</option>
                  ))}
                </select>
              </>
            )}
            {isTenantAdmin && <p className="caption">Creates a TENANT_USER in your tenant.</p>}
            {formErr && <p className="err">{formErr}</p>}
            <div className="row" style={{ marginTop: 16 }}>
              <button className="btn-primary" disabled={busy} type="submit">{busy ? "Adding…" : "Add user"}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
