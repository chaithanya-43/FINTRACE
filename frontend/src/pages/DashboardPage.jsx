import { useEffect, useState } from "react";

import { Badge, Card, EmptyState, ErrorBanner, Loading, Stat } from "../components/ui";
import { CASE_STATUSES, formatDate, formatMoney, labelFor, FRAUD_CATEGORIES } from "../constants";
import { Link } from "../router";
import { api } from "../services/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([api.dashboardSummary(), api.listCases()])
      .then(([summaryData, caseList]) => {
        if (!active) {
          return;
        }
        setSummary(summaryData);
        setCases(caseList);
      })
      .catch((problem) => {
        if (active) {
          setError(problem);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return <Loading label="Loading your cases…" />;
  }

  return (
    <div className="stack stack-lg">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Workspace</p>
          <h1>Case dashboard</h1>
          <p>Your active incidents, recovery progress and recorded loss in one view.</p>
        </div>
        <div className="heading-actions">
          <Link to="/roadmap" className="button button-ghost">
            Recovery roadmap
          </Link>
          <Link to="/report" className="button button-primary">
            + Report an incident
          </Link>
        </div>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {summary && (
        <div className="stat-grid">
          <Stat label="Total cases" value={summary.total_cases} />
          <Stat label="Active cases" value={summary.active_cases} hint="Not closed or archived" />
          <Stat
            label="Need attention"
            value={summary.cases_requiring_action}
            hint="Urgent, incomplete, or with open actions"
            tone={summary.cases_requiring_action > 0 ? "warning" : undefined}
          />
          <Stat label="Open actions" value={summary.open_recovery_actions} hint="Across all roadmaps" />
          <Stat
            label="Recorded loss"
            value={formatMoney(summary.total_estimated_loss)}
            hint="Estimated losses you recorded"
            tone="danger"
          />
        </div>
      )}

      {cases.length === 0 ? (
        <Card title="Your cases" subtitle="Start with the incident report — it takes a few minutes.">
          <EmptyState title="No cases yet">
            Report a fraud incident and FINTRACE will classify it, build a recovery roadmap
            and keep the evidence together.
          </EmptyState>
          <div className="form-actions">
            <Link to="/report" className="button button-primary">
              Report an incident
            </Link>
            <Link to="/emergency" className="button button-ghost">
              Emergency assistance
            </Link>
          </div>
        </Card>
      ) : (
        <Card
          title="Your cases"
          subtitle="Cases you created, plus any assigned to you as an investigator."
        >
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Title</th>
                  <th>Fraud type</th>
                  <th>Status</th>
                  <th>Completeness</th>
                  <th>Loss</th>
                  <th>Created</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {cases.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link to={`/cases/${item.id}`} className="mono">
                        {item.public_reference}
                      </Link>
                    </td>
                    <td>
                      <Link to={`/cases/${item.id}`}>{item.title}</Link>
                    </td>
                    <td>{labelFor(FRAUD_CATEGORIES, item.incident_type)}</td>
                    <td>
                      <Badge value={item.internal_status} />
                    </td>
                    <td>{item.completeness_status.replaceAll("_", " ")}</td>
                    <td>{formatMoney(item.estimated_loss_amount, item.currency)}</td>
                    <td>{formatDate(item.created_at)}</td>
                    <td>
                      <Link to={`/cases/${item.id}/roadmap`} className="text-button">
                        Roadmap →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <div className="grid-two">
        <Card title="Recent activity" subtitle="Latest events recorded against your cases.">
          {summary?.recent_cases?.length ? (
            <ul className="timeline-list">
              {summary.recent_cases.slice(0, 5).map((item) => (
                <li key={item.id || item.public_reference}>
                  <span className="time">{formatDate(item.created_at || item.updated_at)}</span>
                  <div>
                    <strong style={{ fontSize: "0.86rem" }}>
                      {item.title || item.public_reference}
                    </strong>
                    <div className="small muted">
                      {item.internal_status
                        ? `Status: ${String(item.internal_status).replaceAll("_", " ")}`
                        : "Case updated"}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted small">No activity recorded yet.</p>
          )}
        </Card>

        <Card title="Case lifecycle" subtitle="Statuses used by this prototype.">
          <ul className="inline-list">
            {CASE_STATUSES.map(([value, label]) => (
              <li key={value}>
                <Badge value={value} /> <span className="muted small">{label}</span>
              </li>
            ))}
          </ul>
          <hr className="divider" style={{ margin: "0.9rem 0" }} />
          <div className="stack" style={{ gap: "0.6rem" }}>
            <Link to="/regulatory" className="text-button">
              Regulatory intelligence →
            </Link>
            <Link to="/complaints" className="text-button">
              Complaint tracker →
            </Link>
            <Link to="/audit" className="text-button">
              Audit history →
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
