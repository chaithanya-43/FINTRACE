import { useAuth } from "../context/AuthContext";
import { Link, navigate, usePath } from "../router";

export function Brand({ compact = false }) {
  return (
    <span className="sidebar-brand" style={compact ? { padding: 0 } : undefined}>
      <span className="brand-mark">FT</span>
      <span className="brand-name">
        FIN<span>TRACE</span>
      </span>
    </span>
  );
}

export function EmergencyBanner() {
  return (
    <div className="emergency-banner" role="note">
      <strong>Active fraud?</strong> Call the cybercrime helpline{" "}
      <a href="tel:1930">1930</a> and report at{" "}
      <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer">
        cybercrime.gov.in
      </a>{" "}
      now. FINTRACE never asks for an OTP, UPI PIN, CVV or banking password.
    </div>
  );
}

const NAV_GROUPS = [
  {
    label: "Workspace",
    items: [
      { to: "/dashboard", label: "Case dashboard", icon: "◧" },
      { to: "/report", label: "Report an incident", icon: "✚" },
      { to: "/roadmap", label: "Recovery roadmap", icon: "◎" },
    ],
  },
  {
    label: "Case records",
    items: [
      { to: "/transactions", label: "Transaction details", icon: "⇄" },
      { to: "/evidence", label: "Evidence centre", icon: "▤" },
      { to: "/analysis", label: "Incident analysis", icon: "⌕" },
      { to: "/complaints", label: "Complaint tracker", icon: "✉" },
    ],
  },
  {
    label: "Intelligence & assurance",
    items: [
      { to: "/regulatory", label: "Regulatory intelligence", icon: "§" },
      { to: "/audit", label: "Audit history", icon: "◷" },
      { to: "/emergency", label: "Emergency assistance", icon: "!" },
    ],
  },
];

function initials(user) {
  const source = user?.full_name || user?.email || "?";
  return source
    .split(/[\s@._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

export function AppShell({ children }) {
  const { user, logout } = useAuth();
  const path = usePath();
  const isActive = (to) =>
    path === to || (to === "/dashboard" && path.startsWith("/cases"));

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="sidebar-brand">
          <span className="brand-mark">FT</span>
          <span className="brand-name">
            FIN<span>TRACE</span>
          </span>
        </Link>
        <div className="sidebar-tagline">Fraud recovery workspace</div>

        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <div className="side-section-label">{group.label}</div>
            <nav className="side-nav">
              {group.items.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`side-link ${isActive(item.to) ? "active" : ""}`.trim()}
                >
                  <span className="side-icon" aria-hidden="true">
                    {item.icon}
                  </span>
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        ))}

        <div className="sidebar-emergency">
          <strong>Money still moving?</strong>
          Call <a href="tel:1930">1930</a> now, then your bank’s fraud desk.
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <span className="avatar">{initials(user)}</span>
            <div style={{ minWidth: 0 }}>
              <div className="sidebar-user-name">{user?.full_name || "Signed in"}</div>
              <div className="sidebar-user-email">{user?.email}</div>
            </div>
          </div>
          <button
            type="button"
            className="button button-small button-ghost"
            style={{ width: "100%", color: "#c3cee2", borderColor: "rgba(255,255,255,0.18)" }}
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-left">
            <span className="topbar-crumb">FINTRACE workspace</span>
            {user && <span className="role-chip">{user.role}</span>}
          </div>
          <div className="topbar-actions">
            <Link to="/emergency" className="topbar-link">
              Emergency help
            </Link>
            <Link to="/report" className="button button-primary button-small">
              New report
            </Link>
          </div>
        </header>
        <main className="page">{children}</main>
        <footer className="app-footer">
          FINTRACE records what you report and evaluates stored rules against it. It is not
          legal advice and has no connection to any bank, police or government system.
        </footer>
      </div>
    </div>
  );
}

export function PublicLayout({ children }) {
  const { user } = useAuth();

  return (
    <div className="public-shell">
      <header className="public-nav">
        <Link to="/" className="brand">
          <span className="brand-mark">FT</span>
          <span className="brand-name">
            FIN<span>TRACE</span>
          </span>
        </Link>
        <nav className="public-nav-links">
          <a href="/#how">How it works</a>
          <a href="/#capabilities">Capabilities</a>
          <Link to="/emergency">Emergency help</Link>
        </nav>
        <div className="public-nav-actions">
          {user ? (
            <Link to="/dashboard" className="button button-primary button-small">
              Open workspace
            </Link>
          ) : (
            <>
              <Link to="/login" className="button button-ghost button-small" style={{ color: "#fff", borderColor: "rgba(255,255,255,0.25)" }}>
                Sign in
              </Link>
              <Link to="/register" className="button button-primary button-small">
                Create account
              </Link>
            </>
          )}
        </div>
      </header>
      <main className="public-main">{children}</main>
      <footer className="public-footer">
        <div className="public-footer-inner">
          <span>
            <strong style={{ color: "#fff" }}>FINTRACE</strong> · Financial fraud recovery
            workspace · Hackathon prototype
          </span>
          <span>
            Official helpline <a href="tel:1930">1930</a> ·{" "}
            <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer">
              cybercrime.gov.in
            </a>
          </span>
        </div>
      </footer>
    </div>
  );
}
