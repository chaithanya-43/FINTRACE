import { useState } from "react";

import { ErrorBanner, Field } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { Link, navigate } from "../router";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError(new Error("Enter your email and password."));
      return;
    }

    setSubmitting(true);
    try {
      await login(email.trim(), password);
      navigate("/dashboard");
    } catch (problem) {
      setError(problem);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <aside className="auth-aside">
        <Link to="/" className="brand" style={{ color: "#fff", display: "flex", gap: "0.6rem", alignItems: "center" }}>
          <span className="brand-mark">FT</span>
          <span className="brand-name">
            FIN<span style={{ color: "#60a5fa" }}>TRACE</span>
          </span>
        </Link>
        <h2>Pick up where your recovery left off.</h2>
        <p>
          Your case file keeps the incident record, evidence hashes, regulatory checks,
          complaints and roadmap progress together.
        </p>
        <ul className="auth-aside-list">
          <li>Prioritised actions for the first 72 hours</li>
          <li>Evidence stored privately with a SHA-256 hash</li>
          <li>Append-only audit trail of every change</li>
        </ul>
        <div className="auth-aside-note">
          <strong>Active fraud?</strong> Call{" "}
          <a href="tel:1930" style={{ color: "#fff" }}>
            1930
          </a>{" "}
          before signing in.
        </div>
      </aside>

      <div className="auth-main">
        <div className="auth-card">
          <p className="eyebrow">Welcome back</p>
          <h1>Sign in to FINTRACE</h1>
          <p className="muted small">
            Use the email and password you registered with.
          </p>

          <ErrorBanner error={error} onDismiss={() => setError(null)} />

          <form onSubmit={handleSubmit} noValidate>
            <Field label="Email" htmlFor="email">
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </Field>
            <Field label="Password" htmlFor="password">
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </Field>
            <button type="submit" className="button button-primary button-block" disabled={submitting}>
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="auth-alt">
            No account yet? <Link to="/register">Create one</Link>
          </p>
        </div>
        <p className="auth-back">
          <Link to="/">← Back to the FINTRACE home page</Link>
        </p>
      </div>
    </div>
  );
}
