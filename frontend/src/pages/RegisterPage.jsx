import { useState } from "react";

import { ErrorBanner, Field } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { Link, navigate } from "../router";

export default function RegisterPage() {
  const { register } = useAuth();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm: "",
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function update(field) {
    return (event) => setForm((current) => ({ ...current, [field]: event.target.value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    if (form.full_name.trim().length < 2) {
      setError(new Error("Enter your name (at least 2 characters)."));
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      setError(new Error("Enter a valid email address."));
      return;
    }
    if (form.password.length < 10) {
      setError(new Error("Choose a password with at least 10 characters."));
      return;
    }
    if (form.password !== form.confirm) {
      setError(new Error("The two passwords do not match."));
      return;
    }

    setSubmitting(true);
    try {
      await register({
        email: form.email.trim(),
        password: form.password,
        full_name: form.full_name.trim(),
      });
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
        <h2>Start a case file in a few minutes.</h2>
        <p>
          A guided questionnaire captures the incident, the transaction and any evidence.
          FINTRACE then builds a prioritised recovery roadmap.
        </p>
        <ul className="auth-aside-list">
          <li>Guided incident questionnaire</li>
          <li>Private evidence upload with integrity checks</li>
          <li>Roadmap progress saved to your account</li>
        </ul>
        <div className="auth-aside-note">
          <strong>Active fraud?</strong> Call{" "}
          <a href="tel:1930" style={{ color: "#fff" }}>
            1930
          </a>{" "}
          first. Do not wait to create an account.
        </div>
      </aside>

      <div className="auth-main">
        <div className="auth-card">
          <p className="eyebrow">Create an account</p>
          <h1>Start a case file</h1>
          <p className="muted small">
            Use an email you can access. Never enter an OTP, UPI PIN, CVV or banking
            password anywhere in FINTRACE.
          </p>

          <ErrorBanner error={error} onDismiss={() => setError(null)} />

          <form onSubmit={handleSubmit} noValidate>
            <Field label="Full name" htmlFor="full_name">
              <input
                id="full_name"
                value={form.full_name}
                onChange={update("full_name")}
                autoComplete="name"
                required
              />
            </Field>
            <Field label="Email" htmlFor="email">
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={update("email")}
                autoComplete="email"
                required
              />
            </Field>
            <Field label="Password" hint="At least 10 characters." htmlFor="password">
              <input
                id="password"
                type="password"
                value={form.password}
                onChange={update("password")}
                autoComplete="new-password"
                required
              />
            </Field>
            <Field label="Confirm password" htmlFor="confirm">
              <input
                id="confirm"
                type="password"
                value={form.confirm}
                onChange={update("confirm")}
                autoComplete="new-password"
                required
              />
            </Field>
            <button type="submit" className="button button-primary button-block" disabled={submitting}>
              {submitting ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="auth-alt">
            Already registered? <Link to="/login">Sign in</Link>
          </p>
        </div>
        <p className="auth-back">
          <Link to="/">← Back to the FINTRACE home page</Link>
        </p>
      </div>
    </div>
  );
}
