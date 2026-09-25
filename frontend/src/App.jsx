import React, { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./auth.jsx";
import { StoreProvider } from "./store.jsx";
import { Layout, routeFor } from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import ChangePassword from "./pages/ChangePassword.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Courses from "./pages/Courses.jsx";
import CourseDetail from "./pages/CourseDetail.jsx";
import MyCourses from "./pages/MyCourses.jsx";
import Users from "./pages/Users.jsx";
import Assignments from "./pages/Assignments.jsx";
import Progress from "./pages/Progress.jsx";
import Tenants from "./pages/Tenants.jsx";
import { ROLES } from "./tokens.js";

function parseHash() {
  const h = window.location.hash || "#/dashboard";
  const m = h.match(/^#\/courses\/(\d+)/);
  if (m) return { name: "course-detail", id: m[1], raw: "#/courses" };
  const name = h.replace(/^#\//, "").split("?")[0];
  return { name: name || "dashboard", id: null, raw: `#/${name}` };
}

function Shell() {
  const { user, authLoading } = useAuth();
  const [route, setRoute] = useState(parseHash());

  useEffect(() => {
    const onHash = () => setRoute(parseHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  if (authLoading) {
    return (
      <div className="section"><p className="muted">Loading session…</p></div>
    );
  }

  const publicRoutes = ["login", "register"];
  if (!user && !publicRoutes.includes(route.name)) {
    window.location.hash = "#/login";
    return (
      <Layout route="#/login">
        <Login />
      </Layout>
    );
  }

  if (route.name === "login" || route.name === "register") {
    if (user) {
      window.location.hash = routeFor(user.role);
      return null;
    }
    const active = route.name === "register" ? "#/register" : "#/login";
    return (
      <Layout route={active}>
        {route.name === "register" ? <Register /> : <Login />}
      </Layout>
    );
  }

  // Forced password rotation: nothing else renders until it is done.
  if (user && user.must_change_password && route.name !== "change-password") {
    window.location.hash = "#/change-password";
    return (
      <Layout route="#/change-password">
        <ChangePassword />
      </Layout>
    );
  }

  if (route.name === "change-password") {
    if (!user) {
      window.location.hash = "#/login";
      return (
        <Layout route="#/login">
          <Login />
        </Layout>
      );
    }
    if (!user.must_change_password) {
      window.location.hash = routeFor(user.role);
      return null;
    }
    return (
      <Layout route="#/change-password">
        <ChangePassword />
      </Layout>
    );
  }

  if (!user) {
    return (
      <Layout route="#/login">
        <Login />
      </Layout>
    );
  }

  const role = user.role;
  const gate = (allowed, el) =>
    allowed.includes(role)
      ? el
      : <div className="section"><div className="notice">No access — your role ({role}) cannot open this screen.</div></div>;

  let page;
  const active = route.raw;
  switch (route.name) {
    case "dashboard":
      page = <Dashboard />;
      break;
    case "my":
      page = gate([ROLES.TENANT_USER], <MyCourses />);
      break;
    case "courses":
      page = <Courses />;
      break;
    case "course-detail":
      page = <CourseDetail id={route.id} />;
      break;
    case "users":
      page = gate([ROLES.SUPER_ADMIN, ROLES.ADMIN, ROLES.SUPER_VIEWER, ROLES.TENANT_ADMIN], <Users />);
      break;
    case "assignments":
      page = <Assignments />;
      break;
    case "progress":
      page = <Progress />;
      break;
    case "tenants":
      page = gate([ROLES.SUPER_ADMIN, ROLES.ADMIN, ROLES.SUPER_VIEWER], <Tenants />);
      break;
    default:
      page = <div className="section"><div className="notice">Not found — no such screen.</div></div>;
  }

  return <Layout route={active}>{page}</Layout>;
}

export default function App() {
  return (
    <AuthProvider>
      <ScopedStore />
    </AuthProvider>
  );
}

// Store is keyed by user so cached tenant data from a previous login
// can never briefly render for the next user in the same tab.
// Backend authorization stays authoritative; this only resets local cache.
function ScopedStore() {
  const { user } = useAuth();
  return (
    <StoreProvider key={user?.id ?? "anon"}>
      <Shell />
    </StoreProvider>
  );
}
