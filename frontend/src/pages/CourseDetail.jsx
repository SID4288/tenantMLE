import React, { useEffect, useState } from "react";
import { useAuth } from "../auth.jsx";
import { CoursesAPI } from "../api.js";
import { useStore } from "../store.jsx";
import { ProgressBar } from "../components/Layout.jsx";
import { ROLES } from "../tokens.js";

// Course detail. For Tenant Users: assignment + progress for this course,
// milestone buttons + slider that PATCH progress; the bar updates live
// (optimistic) then reconciles with the server — no refresh.
// Backend tracks course-level percentage, not per-lesson rows.
const MILESTONES = [0, 25, 50, 75, 100];

export default function CourseDetail({ id }) {
  const { user } = useAuth();
  const { cache, updateProgress } = useStore();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveErr, setSaveErr] = useState("");

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    CoursesAPI.get(id)
      .then((c) => alive && setCourse(c))
      .catch((e) => alive && setError(e))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [id]);

  const assignments = Array.isArray(cache["assignments"]?.data) ? cache["assignments"].data : [];
  const progress = Array.isArray(cache["progress"]?.data) ? cache["progress"].data : [];

  const myAssignment =
    user?.role === ROLES.TENANT_USER
      ? assignments.find((a) => a.course === Number(id) && a.user === user.id) ||
        assignments.find((a) => a.course === Number(id))
      : assignments.find((a) => a.course === Number(id));
  const myProgress = myAssignment ? progress.find((p) => p.assignment === myAssignment.id) : null;
  const pct = myProgress ? myProgress.progress_percentage : 0;

  async function setPct(next) {
    if (!myProgress) {
      setSaveErr("No progress record yet — assignments create one automatically. Ask your admin to assign this course.");
      return;
    }
    setSaving(true);
    setSaveErr("");
    try {
      await updateProgress(myProgress.id, next, { courseId: Number(id) });
    } catch (e) {
      setSaveErr(e.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="section"><p className="muted">Loading course…</p></div>;
  if (error) {
    return (
      <div className="section">
        {error.kind === "forbidden" ? (
          <div className="notice">No access — this course is not assigned to you or belongs to another tenant.</div>
        ) : error.kind === "notfound" ? (
          <div className="notice">Not found — this course does not exist or is outside your tenant.</div>
        ) : (
          <div className="notice">Error — {error.message}</div>
        )}
        <p><a href="#/courses">← Back to courses</a></p>
      </div>
    );
  }

  return (
    <div className="section">
      <p><a href={user?.role === ROLES.TENANT_USER ? "#/my" : "#/courses"}>← Back</a></p>
      <h2>{course.title}</h2>
      <p className="lede">{course.description || "No description."}</p>
      <p className="caption">tenant {course.tenant} · id {course.id}</p>

      <div className="form-card" style={{ marginTop: 16 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 400, margin: "0 0 8px 0" }}>
          Progress
        </h3>
        {!myAssignment ? (
          <p className="muted">
            No assignment found for this course in the cached list.
            {user?.role === ROLES.TENANT_USER
              ? " Ask your tenant admin to assign it."
              : " Assign it to a learner from Assignments."}
          </p>
        ) : (
          <>
            <ProgressBar value={pct} />
            <p className="caption" style={{ marginTop: 8 }}>
              Assignment {myAssignment.id}
              {myProgress ? ` · progress record ${myProgress.id}` : ""}
              {myProgress?.completed_at ? ` · completed ${myProgress.completed_at}` : ""}
            </p>
            {(user?.role === ROLES.TENANT_USER ||
              user?.role === ROLES.TENANT_ADMIN ||
              user?.role === ROLES.SUPER_ADMIN ||
              user?.role === ROLES.ADMIN) && (
              <>
                <div className="row" style={{ marginTop: 16 }}>
                  {MILESTONES.map((m) => (
                    <button
                      key={m}
                      className={m === 100 ? "btn-primary btn-sm" : "btn-secondary-light btn-sm"}
                      disabled={saving || !myProgress}
                      onClick={() => setPct(m)}
                    >
                      {m === 100 ? "Mark complete" : `${m}%`}
                    </button>
                  ))}
                </div>
                <label className="lbl">Or drag to a percentage</label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={pct}
                  disabled={saving || !myProgress}
                  onChange={(e) => setPct(Number(e.target.value))}
                  style={{ width: "100%" }}
                />
                {saving && <p className="muted">Saving…</p>}
                {saveErr && <p className="err">{saveErr}</p>}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
