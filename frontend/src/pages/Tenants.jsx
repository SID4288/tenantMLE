import React, { useState } from "react";
import { useAuth } from "../auth.jsx";
import { useQuery, useStore } from "../store.jsx";
import { TenantsAPI } from "../api.js";
import { StatusState } from "../components/Layout.jsx";
import { ROLES } from "../tokens.js";

// Platform-only: tenants list + create + application review
// (Super Admin enforced server-side; others get a clear "No access"
// state, not a raw dump).
export default function Tenants() {
  const { user } = useAuth();
  const { data, loading, error } = useQuery("tenants");
  const { createTenant, invalidate } = useStore();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [busy, setBusy] = useState(false);
  const [formErr, setFormErr] = useState("");
  const [reviewErr, setReviewErr] = useState("");

  const list = Array.isArray(data) ? data : [];
  const isSuperAdmin = user?.role === ROLES.SUPER_ADMIN;

  async function onCreate(e) {
    e.preventDefault();
    setBusy(true);
    setFormErr("");
    try {
      await createTenant({ name, slug });
      setName("");
      setSlug("");
    } catch (err) {
      setFormErr(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onReview(id, decision) {
    setReviewErr("");
    try {
      if (decision === "approve") await TenantsAPI.approve(id);
      else await TenantsAPI.reject(id);
      invalidate(["tenants", "users"]);
    } catch (err) {
      setReviewErr(err.message);
    }
  }

  return (
    <div className="section">
      <h2>Tenants</h2>
      <p className="lede">Platform tenants and trial lifecycle. Super Admin only for writes.</p>
      <StatusState loading={loading} error={error} empty={list.length === 0} emptyText="No tenants yet." />
      {!(loading || error) && list.length > 0 && (
        <table className="tbl">
          <thead>
            <tr><th>Name</th><th>Slug</th><th>Status</th><th>Trial ends</th>{isSuperAdmin && <th>Decision</th>}</tr>
          </thead>
          <tbody>
            {list.map((t) => (
              <tr key={t.id}>
                <td>{t.name}</td>
                <td>{t.slug}</td>
                <td>{t.status}</td>
                <td>{t.trial_ends_at || "—"}</td>
                {isSuperAdmin && (
                  <td>
                    {t.status === "PENDING" ? (
                      <span className="row">
                        <button className="btn-primary btn-sm" onClick={() => onReview(t.id, "approve")}>Approve</button>
                        <button className="btn-secondary-light btn-sm" onClick={() => onReview(t.id, "reject")}>Reject</button>
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {reviewErr && <p className="err">{reviewErr}</p>}
      <div className="form-card" style={{ marginTop: 24 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 400, margin: 0 }}>Create tenant</h3>
        <p className="caption">Trial window (30 days) is initialized server-side; lifecycle fields are read-only.</p>
        <form onSubmit={onCreate}>
          <label className="lbl">Name</label>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
          <label className="lbl">Slug</label>
          <input className="input" value={slug} onChange={(e) => setSlug(e.target.value)} required />
          {formErr && <p className="err">{formErr}</p>}
          <div className="row" style={{ marginTop: 16 }}>
            <button className="btn-primary" disabled={busy} type="submit">{busy ? "Creating…" : "Create tenant"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
