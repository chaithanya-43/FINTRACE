import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge, Card, EmptyState, ErrorBanner, Loading, Notice } from "../ui";
import {
  OUTCOME_STATUSES,
  RECOVERY_STATUSES,
  formatDateTime,
  formatMoney,
} from "../../constants";
import { api } from "../../services/api";

const PRIORITY_RANK = { critical: 0, high: 1, medium: 2, low: 3 };

function bucketFor(action) {
  if (action.status === "completed") {
    return "completed";
  }
  if (!action.due_at) {
    return "later";
  }
  const hours = (new Date(action.due_at).getTime() - Date.now()) / 3600000;
  if (hours <= 8) {
    return "immediate";
  }
  if (hours <= 26) {
    return "day";
  }
  if (hours <= 24 * 8) {
    return "week";
  }
  return "later";
}

const BUCKETS = [
  ["immediate", "Immediate · next few hours"],
  ["day", "Within 24 hours"],
  ["week", "This week"],
  ["later", "Follow-up"],
  ["completed", "Completed"],
];

export default function RoadmapView({ caseId, isArchived }) {
  const [roadmap, setRoadmap] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    const [roadmapData, transactionList] = await Promise.all([
      api.roadmap(caseId),
      api.listTransactions(caseId),
    ]);
    setRoadmap(roadmapData);
    setTransactions(transactionList);
  }, [caseId]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    load()
      .catch((problem) => active && setError(problem))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [load]);

  async function patchAction(action, changes) {
    setBusyId(action.id);
    setError(null);
    try {
      await api.updateAction(caseId, action.id, changes);
      await load();
    } catch (problem) {
      setError(problem);
    } finally {
      setBusyId(null);
    }
  }

  const groups = useMemo(() => {
    const map = new Map(BUCKETS.map(([key]) => [key, []]));
    if (!roadmap) {
      return map;
    }
    const sorted = [...roadmap.actions].sort((a, b) => {
      const priority = (PRIORITY_RANK[a.priority] ?? 9) - (PRIORITY_RANK[b.priority] ?? 9);
      if (priority !== 0) {
        return priority;
      }
      return new Date(a.due_at || 0) - new Date(b.due_at || 0);
    });
    sorted.forEach((action) => map.get(bucketFor(action)).push(action));
    return map;
  }, [roadmap]);

  if (loading) {
    return <Loading label="Building your recovery roadmap…" />;
  }

  if (!roadmap) {
    return <ErrorBanner error={error || new Error("Roadmap unavailable.")} />;
  }

  const unauthorized = transactions.some((item) => item.authorization_type === "unauthorized");
  const deceived = transactions.some((item) => item.authorization_type === "authorized_deceived");
  const pct = roadmap.progress.total
    ? Math.round((roadmap.progress.completed / roadmap.progress.total) * 100)
    : 0;

  return (
    <div className="stack">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <section className="roadmap-hero">
        <div>
          <span className="hero-urgent" style={{ marginBottom: "0.55rem" }}>
            {roadmap.urgent ? "Act now" : "Recovery plan"}
          </span>
          <h2>Your personalised recovery roadmap</h2>
          <p>{roadmap.headline}</p>
        </div>
        <div className="roadmap-score">
          <div className="score-label">Actions completed</div>
          <div className="score-value">
            {roadmap.progress.completed}
            <span style={{ fontSize: "1rem", color: "#93a4c0" }}>
              /{roadmap.progress.total}
            </span>
          </div>
          <div className="hero-progress">
            <span style={{ width: `${pct}%` }} />
          </div>
          <div style={{ fontSize: "0.72rem", color: "#93a4c0", marginTop: "0.3rem" }}>
            {pct}% complete
            {roadmap.progress.overdue > 0 ? ` · ${roadmap.progress.overdue} overdue` : ""}
          </div>
        </div>
      </section>

      <div className="grid-two">
        <Card title="Official channels to contact" subtitle="These are actions you take yourself.">
          <ol className="plain-list numbered">
            {roadmap.emergency_guidance.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </Card>

        <Card
          title="Why authorisation matters"
          subtitle="The roadmap adapts to how the payment left your account."
        >
          <div className="roadmap-compare">
            <div className={`compare-col ${unauthorized ? "active" : ""}`.trim()}>
              <h4>I did not authorise it</h4>
              <p>
                Treated as an unauthorised debit: the plan adds a request to freeze or
                block further debits.
              </p>
              {unauthorized && <Badge value="your case" tone="info" />}
            </div>
            <div className={`compare-col ${deceived ? "active" : ""}`.trim()}>
              <h4>I approved it but was deceived</h4>
              <p>
                Treated as a deceived-authorised payment: recovery focuses on the bank
                dispute and complaint path, not a simple unauthorised-debit freeze.
              </p>
              {deceived && <Badge value="your case" tone="info" />}
            </div>
          </div>
          {!unauthorized && !deceived && (
            <p className="muted small" style={{ marginTop: "0.6rem" }}>
              No transaction has a recorded authorisation type yet. Add one in Transaction
              details so the roadmap can adapt.
            </p>
          )}
        </Card>
      </div>

      <Card
        title="Action timeline"
        subtitle="Tick each action as you complete it. Progress is saved to this case."
      >
        {roadmap.actions.length === 0 ? (
          <EmptyState title="No actions yet">Reload to generate the roadmap.</EmptyState>
        ) : (
          BUCKETS.map(([key, label]) => {
            const items = groups.get(key);
            if (!items || items.length === 0) {
              return null;
            }
            return (
              <div className="roadmap-group" key={key}>
                <div className="roadmap-group-head">
                  <h3>{label}</h3>
                  <span className={`badge badge-${key === "completed" ? "positive" : key === "immediate" ? "danger" : "neutral"}`}>
                    {items.length}
                  </span>
                  <span className="rule" />
                </div>
                <div className="roadmap-list">
                  {items.map((action) => {
                    const done = action.status === "completed";
                    return (
                      <article
                        className={`roadmap-item ${done ? "is-done" : ""}`.trim()}
                        key={action.id}
                      >
                        <button
                          type="button"
                          className="roadmap-check"
                          aria-label={done ? `Mark ${action.title} as not done` : `Mark ${action.title} as done`}
                          aria-pressed={done}
                          disabled={isArchived || busyId === action.id}
                          onClick={() =>
                            patchAction(action, {
                              status: done ? "pending" : "completed",
                            })
                          }
                        >
                          ✓
                        </button>
                        <div className="roadmap-item-body">
                          <div className="roadmap-item-title">
                            {action.title}
                            <Badge value={action.priority} />
                            {done ? <Badge value="completed" /> : null}
                          </div>
                          {action.description && <p>{action.description}</p>}
                          {action.instructions && (
                            <div className="roadmap-instructions">{action.instructions}</div>
                          )}
                          <div className="roadmap-meta">
                            <span>Due {formatDateTime(action.due_at)}</span>
                            {action.completed_at && (
                              <span>Completed {formatDateTime(action.completed_at)}</span>
                            )}
                            {done && action.outcome_status !== "unknown" && (
                              <span>Outcome: {action.outcome_status.replaceAll("_", " ")}</span>
                            )}
                            {action.recovered_amount && (
                              <span>Recovered {formatMoney(action.recovered_amount)}</span>
                            )}
                          </div>

                          {!isArchived && (
                            <div className="roadmap-actions">
                              <select
                                aria-label={`Status for ${action.title}`}
                                value={action.status}
                                disabled={busyId === action.id}
                                onChange={(event) =>
                                  patchAction(action, { status: event.target.value })
                                }
                                style={{ width: "auto", fontSize: "0.78rem", padding: "0.3rem 0.45rem" }}
                              >
                                {RECOVERY_STATUSES.map(([value, optionLabel]) => (
                                  <option key={value} value={value}>
                                    {optionLabel}
                                  </option>
                                ))}
                              </select>
                              {done && (
                                <select
                                  aria-label={`Outcome for ${action.title}`}
                                  value={action.outcome_status}
                                  disabled={busyId === action.id}
                                  onChange={(event) =>
                                    patchAction(action, { outcome_status: event.target.value })
                                  }
                                  style={{ width: "auto", fontSize: "0.78rem", padding: "0.3rem 0.45rem" }}
                                >
                                  {OUTCOME_STATUSES.map(([value, optionLabel]) => (
                                    <option key={value} value={value}>
                                      {optionLabel}
                                    </option>
                                  ))}
                                </select>
                              )}
                            </div>
                          )}
                        </div>
                      </article>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </Card>

      <Notice>
        FINTRACE does not call the helpline, contact your bank or submit a portal complaint
        for you. The roadmap tracks what you do and records the result.
      </Notice>

      {!isArchived && <NewActionForm caseId={caseId} onCreated={load} />}
    </div>
  );
}

function NewActionForm({ caseId, onCreated }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    if (title.trim().length < 3) {
      setError(new Error("Give the action a title."));
      return;
    }
    setSaving(true);
    try {
      await api.createAction(caseId, {
        action_type: "follow_up",
        title: title.trim(),
        description: description.trim() || null,
        priority,
      });
      setTitle("");
      setDescription("");
      setPriority("medium");
      setOpen(false);
      await onCreated();
    } catch (problem) {
      setError(problem);
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return (
      <div>
        <button type="button" className="button button-ghost" onClick={() => setOpen(true)}>
          + Add your own action
        </button>
      </div>
    );
  }

  return (
    <Card title="Add your own action" subtitle="For follow-ups that are specific to your bank or case.">
      <form onSubmit={handleSubmit}>
        <ErrorBanner error={error} onDismiss={() => setError(null)} />
        <div className="form-grid">
          <label className="field">
            <span className="field-label">Title</span>
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label className="field">
            <span className="field-label">Priority</span>
            <select value={priority} onChange={(event) => setPriority(event.target.value)}>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </label>
          <label className="field">
            <span className="field-label">Notes</span>
            <input value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
        </div>
        <div className="form-actions">
          <button type="submit" className="button button-primary" disabled={saving}>
            {saving ? "Adding…" : "Add action"}
          </button>
          <button type="button" className="button button-ghost" onClick={() => setOpen(false)}>
            Cancel
          </button>
        </div>
      </form>
    </Card>
  );
}
