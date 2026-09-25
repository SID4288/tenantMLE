import React, { useState } from "react";
import { useAuth } from "../auth.jsx";
import { useQuery, useStore } from "../store.jsx";
import { StatusState } from "../components/Layout.jsx";
import { ROLES } from "../tokens.js";

// Assignments: Tenant Admin assigns courses to learners (same tenant,
// enforced server-side). Progress rows are auto-created with each
// assignment. Mutations invalidate assignments+progress so lists update live.
export default function Assignments() {
  const { user } = useAuth();
  const { data, loading, error } = useQuery("assignments");
  const coursesQ = useQuery("courses");
  const usersQ = useQuery("users");
  const { createAssignment, deleteAssignment } = useStore();

  const [course, setCourse] = useState("");
  const [assignee, setAssignee] = useState("");
  const [busy, setBusy] = useState(false);
  const [formErr, setFormErr] = useState("");

  const list = Array.isArray(data) ? data : [];
  const courses = Array.isArray(coursesQ.data) ? coursesQ.data : [];
  const users = (Array.isArray(usersQ.data) ? usersQ.data : []).filter((u) => u.role === ROLES.TENANT_USER);
  const courseName = new Map(courses.map((c) => [c.id, c.title]));
  const userName = new Map((Array.isArray(usersQ.data) ? usersQ.data : []).map((u) => [u.id, u.username]));

  const canManage =
    user?.role === ROLES.SUPER_ADMIN || user?.role === ROLES.ADMIN || user?.role === ROLES.TENANT_ADMIN;

  async function onCreate(e) {
    e.preventDefault();
    setBusy(true);
    setFormErr("");
    try {
      await createAssignment({ course: Number(course), user: Number(assignee) });
      setCourse("");
      setAssignee("");
    } catch (err) {
      setFormErr(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id) {
    if (!window.confirm("Delete this assignment? Its progress record goes too.")) return;
    try {
      await deleteAssignment(id);
    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <div className="section">
      <h2>{user?.role === ROLES.TENANT_USER ? "My assignments" : "Assignments"}</h2>
      <p className="lede">
        {user?.role === ROLES.TENANT_USER
          ? "Courses assigned to you."
          : "Assign courses to learners. Course and learner must share a tenant."}
      </p>
      <StatusState loading={loading} error={error} empty={list.length === 0} emptyText="No assignments yet." />
      <table className="tbl">
        <thead>
          <tr><th>ID</th><th>Course</th><th>Learner</th><th>Assigned</th><th></th></tr>
        </thead>
        <tbody>
          {list.map((a) => (
            <tr key={a.id}>
              <td>{a.id}</td>
              <td>{courseName.get(a.course) ?? `course ${a.course}`}</td>
              <td>{userName.get(a.user) ?? `user ${a.user}`}</td>
              <td>{a.assigned_at || "—"}</td>
              <td>
                <span className="row">
                  <a href={`#/courses/${a.course}`}>Open</a>
                  {canManage && (
                    <button className="btn-secondary-light btn-sm" onClick={() => onDelete(a.id)}>Delete</button>
                  )}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManage && (
        <div className="form-card" style={{ marginTop: 24 }}>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 400, margin: 0 }}>Assign course</h3>
          <form onSubmit={onCreate}>
            <label className="lbl">Course</label>
            <select className="select" value={course} onChange={(e) => setCourse(e.target.value)} required>
              <option value="">Select course…</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>{c.title} (tenant {c.tenant})</option>
              ))}
            </select>
            <label className="lbl">Learner (tenant user)</label>
            <select className="select" value={assignee} onChange={(e) => setAssignee(e.target.value)} required>
              <option value="">Select learner…</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>{u.username} (tenant {u.tenant})</option>
              ))}
            </select>
            {formErr && <p className="err">{formErr}</p>}
            <div className="row" style={{ marginTop: 16 }}>
              <button className="btn-primary" disabled={busy} type="submit">{busy ? "Assigning…" : "Assign course"}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
