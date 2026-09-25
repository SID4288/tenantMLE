import React from "react";
import { useAuth } from "../auth.jsx";
import { useQuery } from "../store.jsx";
import { StatusState } from "../components/Layout.jsx";
import { ROLES } from "../tokens.js";

export default function Dashboard() {
  const { user } = useAuth();
  const courses = useQuery("courses");
  const assignments = useQuery("assignments");
  const progress = useQuery("progress");
  const users = useQuery("users");
  const tenants = useQuery("tenants");

  const role = user?.role;
  const courseList = Array.isArray(courses.data) ? courses.data : [];
  const assignmentList = Array.isArray(assignments.data) ? assignments.data : [];
  const progressList = Array.isArray(progress.data) ? progress.data : [];

  return (
    <div>
      <section className="hero">
        <h1>{role === ROLES.TENANT_USER ? "MY LEARNING" : "COMMAND CENTER"}</h1>
        <p>
          Signed in as {user?.username} ({role}).
          {role === ROLES.TENANT_USER
            ? " Open a course, work through it, and watch progress update live."
            : " Manage courses, users, assignments, and progress. Every change saves via API and refreshes on its own."}
        </p>
        <div className="row" style={{ marginTop: 24 }}>
          {role === ROLES.TENANT_USER ? (
            <a href="#/my"><button className="btn-primary">My courses</button></a>
          ) : (
            <a href="#/courses"><button className="btn-primary">Manage courses</button></a>
          )}
          {role === ROLES.TENANT_ADMIN && (
            <a href="#/assignments"><button className="btn-secondary">Assign courses</button></a>
          )}
        </div>
      </section>
      <div className="section">
        <h2>Overview</h2>
        <p className="lede">Live counts from the API — no refresh needed.</p>
        <StatusState loading={courses.loading && assignments.loading} error={courses.error} />
        <div className="grid3">
          <div className="card">
            <h3>{courseList.length}</h3>
            <p>{role === ROLES.TENANT_USER ? "Assigned courses" : "Courses"}</p>
            <a href={role === ROLES.TENANT_USER ? "#/my" : "#/courses"}>Open →</a>
          </div>
          <div className="card">
            <h3>{assignmentList.length}</h3>
            <p>Assignments</p>
            <a href="#/assignments">Open →</a>
          </div>
          <div className="card">
            <h3>{progressList.length}</h3>
            <p>Progress records</p>
            <a href="#/progress">Open →</a>
          </div>
        </div>
        {(role === ROLES.SUPER_ADMIN || role === ROLES.ADMIN || role === ROLES.SUPER_VIEWER) && (
          <div className="grid2" style={{ marginTop: 16 }}>
            <div className="card">
              <h3>{Array.isArray(tenants.data) ? tenants.data.length : "—"}</h3>
              <p>Tenants</p>
              <a href="#/tenants">Open →</a>
            </div>
            <div className="card">
              <h3>{Array.isArray(users.data) ? users.data.length : "—"}</h3>
              <p>Users</p>
              <a href="#/users">Open →</a>
            </div>
          </div>
        )}
        <p className="caption" style={{ marginTop: 16 }}>
          Note: the backend has no Lesson model — progress is a course-level percentage (0–100) on each
          assignment, updated via PATCH /api/progress/:id/. The course view exposes it as incremental
          milestones plus “Mark complete”.
        </p>
      </div>
    </div>
  );
}
