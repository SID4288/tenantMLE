import React, { useState } from "react";
import { useAuth } from "../auth.jsx";

// Demo accounts matching the users currently seeded in the Django backend.
const DEMOS = [
  {
    role: "SUPER_ADMIN",
    username: "superadmin",
    hint: "Platform administrator",
  },
  {
    role: "ADMIN",
    username: "platformadmin",
    hint: "Platform admin",
  },
  {
    role: "SUPER_VIEWER",
    username: "superviewer",
    hint: "Read-only platform viewer",
  },
  {
    role: "TENANT_ADMIN",
    username: "tenant_a_admin",
    hint: "Manages Tenant A",
  },
  {
    role: "TENANT_USER",
    username: "tenant_a_user1",
    hint: "Tenant A learner",
  },
];
const DEMO_PASSWORD = "TestPassword123!";

export default function Login() {
  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function doLogin(e) {
    e?.preventDefault();

    setBusy(true);
    setError("");

    try {
      await login(username, password);
      window.location.hash = "#/dashboard";
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function demoLogin(demo) {
    setUsername(demo.username);
    setPassword(DEMO_PASSWORD);
    setBusy(true);
    setError("");

    // Demo users are seeded with the development password "password".

    try {
      await login(demo.username, DEMO_PASSWORD);
      window.location.hash = "#/dashboard";
    } catch (err) {
      setError(`Demo login as ${demo.username} failed — ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <section className="hero">
        <h1>LEARN AT FULL VOLTAGE</h1>

        <p>
          Multi-tenant courses, assignments, and live progress — one platform
          for providers and learners. Log in with a demo account or set up
          your own.
        </p>
      </section>

      <div className="section">
        <h2>Log in</h2>

        <p className="lede">
          Demo mode or your own credentials.
        </p>

        <div className="grid2">
          <div className="form-card">
            <form onSubmit={doLogin}>
              <label className="lbl" htmlFor="li-user">
                Username
              </label>

              <input
                id="li-user"
                className="input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />

              <label className="lbl" htmlFor="li-pass">
                Password
              </label>

              <input
                id="li-pass"
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                placeholder='Password'
              />

              {error && <p className="err">{error}</p>}

              <div className="row" style={{ marginTop: 16 }}>
                <button
                  className="btn-primary"
                  disabled={busy}
                  type="submit"
                >
                  {busy ? "Logging in…" : "Log in"}
                </button>
              </div>
            </form>
          </div>

          <div className="form-card">
            <h3
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 24,
                fontWeight: 400,
                margin: "0 0 8px 0",
              }}
            >
              Explore with demo accounts
            </h3>

            <p className="muted">
              Click a role to fill the username and log in with the password
              above, or the default development password.
            </p>

            <table className="tbl">
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Username</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {DEMOS.map((demo) => (
                  <tr key={demo.role}>
                    <td>
                      {demo.role}
                      <br />
                      <span className="caption">{demo.hint}</span>
                    </td>

                    <td>
                      <code>{demo.username}</code>
                    </td>

                    <td>
                      <button
                        type="button"
                        className="btn-secondary-light btn-sm"
                        disabled={busy}
                        onClick={() => demoLogin(demo)}
                      >
                        Use
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <p className="caption">
              Demo users must already exist in the backend database.
            </p>
          </div>
        </div>

        <h2 style={{ marginTop: 48 }}>New to TenantMLE?</h2>

        <p className="lede">
          Join an existing organization as a learner, or apply to create a
          new one.
        </p>

        <div className="form-card">
          <div className="row">
            <a href="#/register">
              <button className="btn-primary" type="button">
                Register
              </button>
            </a>
          </div>

          <p className="caption">
            Learners join an approved organization and can log in right away.
            Providers apply to create one — login unlocks after approval.
          </p>
        </div>
      </div>
    </div>
  );
}