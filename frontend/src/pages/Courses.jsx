import React, { useState } from "react";
import { useAuth } from "../auth.jsx";
import { useQuery, useStore } from "../store.jsx";
import { ProgressBar, StatusState } from "../components/Layout.jsx";
import { ROLES } from "../tokens.js";

// Courses list + create/edit/delete. Tenant Admin scoped to own tenant
// server-side; platform roles see all. Tenant Users see only assigned
// courses here via the same endpoint (they should prefer #/my).
export default function Courses() {
  const { user } = useAuth();
  const { data, loading, error } = useQuery("courses");
  const { createCourse, updateCourse, deleteCourse } = useStore();
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [tenant, setTenant] = useState("");
  const [busy, setBusy] = useState(false);
  const [formErr, setFormErr] = useState("");
  const [editing, setEditing] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDesc, setEditDesc] = useState("");

  const tenantsQ = useQuery("tenants");
  const canManage =
    user?.role === ROLES.SUPER_ADMIN || user?.role === ROLES.ADMIN || user?.role === ROLES.TENANT_ADMIN;
  const list = Array.isArray(data) ? data : [];

  async function onCreate(e) {
    e.preventDefault();
    setBusy(true);
    setFormErr("");
    try {
      const payload = { title, description: desc };
      // Platform managers must supply tenant; tenant admins are
      // auto-scoped server-side (perform_create).
      if ((user?.role === ROLES.SUPER_ADMIN || user?.role === ROLES.ADMIN) && tenant) {
        payload.tenant = Number(tenant);
      }
      await createCourse(payload);
      setTitle("");
      setDesc("");
      setTenant("");
    } catch (err) {
      setFormErr(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id) {
    if (!window.confirm("Delete this course? Assignments and progress go with it.")) return;
    try {
      await deleteCourse(id);
    } catch (err) {
      alert(err.message);
    }
  }

  function startEdit(c) {
    setEditing(c.id);
    setEditTitle(c.title);
    setEditDesc(c.description || "");
  }

  async function saveEdit(id) {
    try {
      await updateCourse(id, { title: editTitle, description: editDesc });
      setEditing(null);
    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <div className="section">
      <h2>{user?.role === ROLES.TENANT_USER ? "Courses" : "Manage courses"}</h2>
      <p className="lede">
        {user?.role === ROLES.TENANT_USER
          ? "Courses assigned to you. Open one to track progress."
          : "Create, rename, and delete courses. List refreshes automatically after each change."}
      </p>
      <StatusState loading={loading} error={error} empty={list.length === 0} emptyText="No courses yet." />
      <div className="grid3">
        {list.map((c) => (
          <CourseCard
            key={c.id}
            course={c}
            canManage={canManage}
            editing={editing === c.id}
            editTitle={editTitle}
            editDesc={editDesc}
            setEditTitle={setEditTitle}
            setEditDesc={setEditDesc}
            onEdit={() => startEdit(c)}
            onCancel={() => setEditing(null)}
            onSave={() => saveEdit(c.id)}
            onDelete={() => onDelete(c.id)}
          />
        ))}
      </div>

      {canManage && (
        <div className="form-card" style={{ marginTop: 32 }}>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 400, margin: 0 }}>
            Create course
          </h3>
          <form onSubmit={onCreate}>
            <label className="lbl">Title</label>
            <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
            <label className="lbl">Description</label>
            <textarea className="textarea" value={desc} onChange={(e) => setDesc(e.target.value)} />
            {(user?.role === ROLES.SUPER_ADMIN || user?.role === ROLES.ADMIN) && (
              <>
                <label className="lbl">Tenant (required for platform roles)</label>
                <select className="select" value={tenant} onChange={(e) => setTenant(e.target.value)}>
                  <option value="">Select tenant…</option>
                  {(Array.isArray(tenantsQ.data) ? tenantsQ.data : []).map((t) => (
                    <option key={t.id} value={t.id}>{t.name} (id {t.id})</option>
                  ))}
                </select>
              </>
            )}
            {formErr && <p className="err">{formErr}</p>}
            <div className="row" style={{ marginTop: 16 }}>
              <button className="btn-primary" disabled={busy} type="submit">
                {busy ? "Creating…" : "Create course"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function CourseCard({ course, canManage, editing, editTitle, editDesc, setEditTitle, setEditDesc, onEdit, onCancel, onSave, onDelete }) {
  return (
    <div className="card">
      {editing ? (
        <>
          <input className="input" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
          <div style={{ height: 8 }} />
          <textarea className="textarea" value={editDesc} onChange={(e) => setEditDesc(e.target.value)} />
          <div className="row" style={{ marginTop: 8 }}>
            <button className="btn-secondary-light btn-sm" onClick={onSave}>Save</button>
            <button className="btn-secondary-light btn-sm" onClick={onCancel}>Cancel</button>
          </div>
        </>
      ) : (
        <>
          <h3>{course.title}</h3>
          <p>{course.description || <span className="muted">No description.</span>}</p>
          <p className="caption">tenant {course.tenant} · id {course.id}</p>
          <CourseProgressInline courseId={course.id} />
          <div className="row" style={{ marginTop: 8 }}>
            <a href={`#/courses/${course.id}`}>Open →</a>
            {canManage && (
              <>
                <button className="btn-secondary-light btn-sm" onClick={onEdit}>Edit</button>
                <button className="btn-secondary-light btn-sm" onClick={onDelete}>Delete</button>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// Average progress across assignments for this course (from cached progress+assignments).
function CourseProgressInline({ courseId }) {
  const { cache } = useStore();
  const assignments = cache["assignments"]?.data;
  const progress = cache["progress"]?.data;
  if (!Array.isArray(assignments) || !Array.isArray(progress)) return null;
  const mine = assignments.filter((a) => a.course === courseId);
  if (mine.length === 0) return null;
  const byAssignment = new Map(progress.map((p) => [p.assignment, p.progress_percentage]));
  const vals = mine.map((a) => byAssignment.get(a.id)).filter((v) => v !== undefined);
  if (vals.length === 0) return null;
  const avg = Math.round(vals.reduce((s, v) => s + v, 0) / vals.length);
  return (
    <div style={{ margin: "8px 0" }}>
      <ProgressBar value={avg} />
    </div>
  );
}
