import { useCallback, useEffect, useState } from "react";

import { Badge, Card, EmptyState, ErrorBanner, Loading, Notice } from "../ui";
import {
  OUTCOME_STATUSES,
  RECOVERY_STATUSES,
  formatDateTime,
} from "../../constants";
import { api } from "../../services/api";

export default function RecoveryTab({ caseId, isArchived }) {
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    setRoadmap(await api.roadmap(caseId));
  }, [caseId]);

  useEffect(() => {
    let active = true;
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

  if (loading) {
    return <Loading label="Building your recovery roadmap…" />;
  }

  if (!roadmap) {
    return <ErrorBanner error={error || new Error("Roadmap unavailable.")} />;
  }

  return (
    <div className="stack">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {roadmap.urgent && (
        <Notice tone="error">
          <strong>Active fraud priority.</strong> {roadmap.headline}
        </Notice>
      )}
      {!roadmap.urgent && <Notice>{roadmap.headline}</Notice>}

      <Card title="Do these first" subtitle="Official channels you contact yourself.">
        <ol className="plain-list numbered">
          {roadmap.emergency_guidance.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </Card>

      <Card
        title="Recovery actions"
        subtitle={`${roadmap.progress.completed} of ${roadmap.progress.total} complete${
          roadmap.progress.overdue > 0 ? ` · ${roadmap.progress.overdue} overdue` : ""
        }`}
      >
        {roadmap.actions.length === 0 ? (
          <EmptyState title="No actions yet">Reload to generate the roadmap.</EmptyState>
        ) : (
          <div className="stack">
            {roadmap.actions.map((action) => (
              <article key={action.id} className="action-row">
                <div>
                  <div className="action-title">
                    <Badge value={action.priority} />
                    <strong>{action.title}</strong>
                    <Badge value={action.status} />
                  </div>
                  {action.description && <p className="muted small">{action.description}</p>}
                  {action.instructions && <p className="small">{action.instructions}</p>}
                  <p className="muted small">
                    Due {formatDateTime(action.due_at)}
                    {action.completed_at ? ` · completed ${formatDateTime(action.completed_at)}` : ""}
                    {` · outcome: ${action.outcome_status.replaceAll("_", " ")}`}
                  </p>
                </div>
                {!isArchived && (
                  <div className="action-controls">
                    <select
                      aria-label={`Status for ${action.title}`}
                      value={action.status}
                      disabled={busyId === action.id}
                      onChange={(event) => patchAction(action, { status: event.target.value })}
                    >
                      {RECOVERY_STATUSES.map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                    {action.status === "completed" && (
                      <select
                        aria-label={`Outcome for ${action.title}`}
                        value={action.outcome_status}
                        disabled={busyId === action.id}
                        onChange={(event) =>
                          patchAction(action, { outcome_status: event.target.value })
                        }
                      >
                        {OUTCOME_STATUSES.map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </Card>

      <Card title="Record your own action">
        <NewActionForm caseId={caseId} onCreated={load} disabled={isArchived} />
      </Card>
    </div>
  );
}

function NewActionForm({ caseId, onCreated, disabled }) {
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
      await onCreated();
    } catch (problem) {
      setError(problem);
    } finally {
      setSaving(false);
    }
  }

  if (disabled) {
    return <p className="muted">Archived cases are read-only.</p>;
  }

  return (
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
        <button type="submit" className="button" disabled={saving}>
          {saving ? "Adding…" : "Add action"}
        </button>
      </div>
    </form>
  );
}
