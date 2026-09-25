import React from "react";
import { useAuth } from "../auth.jsx";
import { useQuery } from "../store.jsx";
import { ProgressBar, StatusState } from "../components/Layout.jsx";

// Tenant User home: assigned courses with live progress % each.
export default function MyCourses() {
  const { user } = useAuth();
  const courses = useQuery("courses");
  const assignments = useQuery("assignments");
  const progress = useQuery("progress");

  const list = Array.isArray(courses.data) ? courses.data : [];
  const alist = Array.isArray(assignments.data) ? assignments.data : [];
  const plist = Array.isArray(progress.data) ? progress.data : [];

  const byCourseAssignment = new Map(alist.map((a) => [a.course, a]));
  const byAssignmentProgress = new Map(plist.map((p) => [p.assignment, p]));

  const loading = courses.loading || assignments.loading || progress.loading;
  const error = courses.error || assignments.error || progress.error;

  return (
    <div className="section">
      <h2>My courses</h2>
      <p className="lede">
        Courses assigned to {user?.username}. Open one to continue — progress updates live, no refresh.
      </p>
      <StatusState loading={loading} error={error} empty={!loading && !error && list.length === 0} emptyText="No courses assigned yet. Ask your tenant admin." />
      <div className="grid3">
        {list.map((c) => {
          const a = byCourseAssignment.get(c.id);
          const p = a ? byAssignmentProgress.get(a.id) : null;
          return (
            <div className="card" key={c.id}>
              <h3>{c.title}</h3>
              <p>{c.description || <span className="muted">No description.</span>}</p>
              {p ? <ProgressBar value={p.progress_percentage} /> : <p className="caption">No progress record yet.</p>}
              <div className="row" style={{ marginTop: 8 }}>
                <a href={`#/courses/${c.id}`}>Open course →</a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
