import React from "react";
import { useAuth } from "../auth.jsx";
import { useQuery } from "../store.jsx";
import { ProgressBar, StatusState } from "../components/Layout.jsx";

// Progress list. Tenant Users see only their own rows; Tenant Admins see
// their tenant; platform roles see all. Updates happen from the course
// view; this screen reflects them live via the shared cache.
export default function Progress() {
  const { user } = useAuth();
  const { data, loading, error } = useQuery("progress");
  const assignmentsQ = useQuery("assignments");
  const coursesQ = useQuery("courses");
  const usersQ = useQuery("users");

  const list = Array.isArray(data) ? data : [];
  const assignments = new Map((Array.isArray(assignmentsQ.data) ? assignmentsQ.data : []).map((a) => [a.id, a]));
  const courses = new Map((Array.isArray(coursesQ.data) ? coursesQ.data : []).map((c) => [c.id, c.title]));
  const users = new Map((Array.isArray(usersQ.data) ? usersQ.data : []).map((u) => [u.id, u.username]));

  return (
    <div className="section">
      <h2>{user?.role === "TENANT_USER" ? "My progress" : "Progress"}</h2>
      <p className="lede">Course-level completion per assignment. Change it from the course view — this list follows live.</p>
      <StatusState loading={loading} error={error} empty={list.length === 0} emptyText="No progress records yet." />
      <div className="grid2">
        {list.map((p) => {
          const a = assignments.get(p.assignment);
          return (
            <div className="card" key={p.id}>
              <h3>{a ? (courses.get(a.course) ?? `Course ${a.course}`) : `Assignment ${p.assignment}`}</h3>
              <p className="caption">
                learner {a ? (users.get(a.user) ?? a.user) : "—"}
                {p.completed_at ? ` · completed ${p.completed_at}` : ""}
              </p>
              <ProgressBar value={p.progress_percentage} />
              <div className="row" style={{ marginTop: 8 }}>
                {a && <a href={`#/courses/${a.course}`}>Open course →</a>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
