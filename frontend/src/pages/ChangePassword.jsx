import React, { useState } from "react";
import { useAuth } from "../auth.jsx";
import { AuthAPI } from "../api.js";
import { routeFor } from "../components/Layout.jsx";

// Forced password rotation (hash route #/change-password).
// Shown exclusively until the password is changed: App.jsx bounces
// every other route back here while user.must_change_password is set.
export default function ChangePassword() {
  const { reloadMe } = useAuth();

  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");

    if (next !== confirm) {
      setErr("New passwords do not match.");
      return;
    }

    setBusy(true);
    try {
      await AuthAPI.changePassword({
        current_password: current,
        new_password: next,
      });
      const me = await reloadMe();
      window.location.hash = routeFor(me?.role);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <section className="hero">
        <h1>SET YOUR PASSWORD</h1>
        <p>
          You logged in with a one-time temporary password. Choose a
          permanent one now — nothing else unlocks until you do.
        </p>
      </section>

      <div className="section">
        <div className="form-card">
          <form onSubmit={onSubmit}>
            <label className="lbl">Temporary password</label>
            <input
              className="input"
              type="password"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              autoComplete="current-password"
              required
            />

            <label className="lbl">New password (min 8 characters)</label>
            <input
              className="input"
              type="password"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              autoComplete="new-password"
              minLength={8}
              required
            />

            <label className="lbl">Confirm new password</label>
            <input
              className="input"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              minLength={8}
              required
            />

            {err && <p className="err">{err}</p>}

            <div className="row" style={{ marginTop: 16 }}>
              <button className="btn-primary" disabled={busy} type="submit">
                {busy ? "Saving…" : "Change password"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
