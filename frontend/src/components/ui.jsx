const RESULT_TONES = {
  applies: "positive",
  may_apply: "warning",
  does_not_apply: "neutral",
  inconclusive: "warning",
  disputed: "danger",
  verified: "positive",
  failed: "danger",
  unverified: "warning",
  pending: "neutral",
  in_progress: "info",
  completed: "positive",
  blocked: "danger",
  skipped: "neutral",
  critical: "danger",
  high: "warning",
  medium: "info",
  low: "neutral",
  intake: "neutral",
  collecting_evidence: "info",
  assessment: "info",
  recovery: "warning",
  closed: "positive",
  draft: "neutral",
  ready: "info",
  submitted: "info",
  acknowledged: "positive",
  rejected: "danger",
  withdrawn: "neutral",
  active: "positive",
  archived: "neutral",
  confirmed: "positive",
  unreviewed: "neutral",
  user_confirmed: "good",
};

export function Badge({ value, tone }) {
  let resolved = tone || RESULT_TONES[value] || "neutral";
  if (resolved === "good") {
    resolved = "teal";
  }
  return (
    <span className={`badge badge-${resolved}`}>
      {String(value ?? "—").replaceAll("_", " ")}
    </span>
  );
}

export function Card({ title, subtitle, actions, children, className = "" }) {
  return (
    <section className={`card ${className}`.trim()}>
      {(title || actions) && (
        <header className="card-header">
          <div>
            {title && <h2>{title}</h2>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="card-actions">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

export function ErrorBanner({ error, onDismiss }) {
  if (!error) {
    return null;
  }
  const details = Array.isArray(error.details) ? error.details : null;
  return (
    <div className="alert alert-error" role="alert">
      <div>
        <strong>{error.message || "Something went wrong."}</strong>
        {details && (
          <ul>
            {details.map((item) => (
              <li key={`${item.field}-${item.message}`}>
                {item.field ? `${item.field}: ` : ""}
                {item.message}
              </li>
            ))}
          </ul>
        )}
      </div>
      {onDismiss && (
        <button type="button" className="link-button" onClick={onDismiss}>
          Dismiss
        </button>
      )}
    </div>
  );
}

export function Notice({ children, tone = "info" }) {
  return <div className={`alert alert-${tone === "error" ? "error" : tone}`}>{children}</div>;
}

export function Loading({ label = "Loading…" }) {
  return (
    <div className="loading" role="status">
      <span className="spinner" aria-hidden="true" />
      {label}
    </div>
  );
}

export function EmptyState({ title, children }) {
  return (
    <div className="empty-state">
      <p className="empty-title">{title}</p>
      {children && <p style={{ margin: 0 }}>{children}</p>}
    </div>
  );
}

export function Field({ label, hint, children, htmlFor }) {
  return (
    <label className="field" htmlFor={htmlFor}>
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  );
}

export function Stat({ label, value, hint, tone }) {
  return (
    <div className={`stat ${tone ? `stat-${tone}` : ""}`.trim()}>
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {hint && <span className="stat-hint">{hint}</span>}
    </div>
  );
}

export function ProgressBar({ value, total, label }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div>
      <div className="progress-track" aria-label={label || "Progress"}>
        <span style={{ width: `${pct}%` }} />
      </div>
      {label && (
        <p className="small muted" style={{ marginTop: "0.35rem" }}>
          {label}
        </p>
      )}
    </div>
  );
}

export function DemoTag({ children = "Demonstration data" }) {
  return <span className="demo-tag">{children}</span>;
}
