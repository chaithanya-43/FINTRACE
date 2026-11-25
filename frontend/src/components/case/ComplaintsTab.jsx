import { useCallback, useEffect, useState } from "react";

import { Badge, Card, EmptyState, ErrorBanner, Field, Loading, Notice } from "../ui";
import {
  COMPLAINT_CHANNELS,
  SUBMISSION_STATUSES,
  formatDateTime,
  labelFor,
} from "../../constants";
import { api } from "../../services/api";

export default function ComplaintsTab({ caseId, isArchived }) {
  const [complaints, setComplaints] = useState([]);
  const [histories, setHistories] = useState({});
  const [openId, setOpenId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({
    channel: "cybercrime_portal",
    organisation_name: "",
    reference_number: "",
    submission_status: "draft",
  });
  const [saving, setSaving] = useState(false);
  const [observation, setObservation] = useState({ status: "", detail: "" });
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setComplaints(await api.listComplaints(caseId));
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

  async function loadHistory(complaintId) {
    const history = await api.complaintHistory(caseId, complaintId);
    setHistories((current) => ({ ...current, [complaintId]: history }));
  }

  async function toggle(complaintId) {
    if (openId === complaintId) {
      setOpenId(null);
      return;
    }
    setOpenId(complaintId);
    try {
      await loadHistory(complaintId);
    } catch (problem) {
      setError(problem);
    }
  }

  async function handleCreate(event) {
    event.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await api.createComplaint(caseId, {
        channel: form.channel,
        organisation_name: form.organisation_name || null,
        reference_number: form.reference_number || null,
        submission_status: form.submission_status,
      });
      setForm({
        channel: "cybercrime_portal",
        organisation_name: "",
        reference_number: "",
        submission_status: "draft",
      });
      await load();
    } catch (problem) {
      setError(problem);
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmissionStatus(complaint, status) {
    setError(null);
    try {
      await api.updateComplaint(caseId, complaint.id, { submission_status: status });
      await load();
    } catch (problem) {
      setError(problem);
    }
  }

  async function handleObservation(complaint) {
    setError(null);
    if (!observation.status.trim()) {
      setError(new Error("Enter the status the organisation showed you."));
      return;
    }
    setBusy(true);
    try {
      await api.recordComplaintStatus(caseId, complaint.id, {
        observed_status: observation.status.trim(),
        status_detail: observation.detail.trim() || null,
      });
      setObservation({ status: "", detail: "" });
      await load();
      await loadHistory(complaint.id);
    } catch (problem) {
      setError(problem);
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <Loading label="Loading complaints…" />;
  }

  return (
    <div className="stack">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <Notice>
        FINTRACE records complaints you filed yourself. It does not submit anything to a
        portal, bank or police system, and it cannot create an official acknowledgement.
      </Notice>

      <Card title="Complaints on this case">
        {complaints.length === 0 ? (
          <EmptyState title="No complaints recorded">
            Add the report you filed, then record what the organisation tells you over time.
          </EmptyState>
        ) : (
          <div className="stack">
            {complaints.map((complaint) => (
              <article key={complaint.id} className="complaint-row">
                <header className="action-title">
                  <strong>{labelFor(COMPLAINT_CHANNELS, complaint.channel)}</strong>
                  <Badge value={complaint.submission_status} />
                  {complaint.official_status ? (
                    <Badge value={complaint.official_status} tone="info" />
                  ) : (
                    <span className="muted small">official status not yet observed</span>
                  )}
                  <span className="muted small mono">
                    {complaint.reference_number || "no reference"}
                  </span>
                </header>

                <p className="muted small">
                  {complaint.organisation_name || "Organisation not recorded"} · filed{" "}
                  {formatDateTime(complaint.filed_at)} · last checked{" "}
                  {formatDateTime(complaint.last_checked_at)}
                </p>

                <div className="inline-actions">
                  {!isArchived && (
                    <select
                      aria-label="Submission status"
                      value={complaint.submission_status}
                      onChange={(event) => handleSubmissionStatus(complaint, event.target.value)}
                    >
                      {SUBMISSION_STATUSES.map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  )}
                  <button
                    type="button"
                    className="button button-small button-ghost"
                    onClick={() => toggle(complaint.id)}
                  >
                    {openId === complaint.id ? "Hide status history" : "Status history"}
                  </button>
                </div>

                {openId === complaint.id && (
                  <div className="history">
                    {(histories[complaint.id] || []).length === 0 ? (
                      <p className="muted small">No status observations recorded yet.</p>
                    ) : (
                      <ol className="timeline">
                        {(histories[complaint.id] || []).map((event) => (
                          <li key={event.id}>
                            <span className="timeline-dot" aria-hidden="true" />
                            <div>
                              <strong>{event.observed_status}</strong>
                              <p className="muted small">
                                {formatDateTime(event.checked_at)}
                                {event.status_detail ? ` · ${event.status_detail}` : ""}
                              </p>
                            </div>
                          </li>
                        ))}
                      </ol>
                    )}

                    {!isArchived && (
                      <div className="form-grid observation-form">
                        <Field label="Observed status" htmlFor={`status-${complaint.id}`}>
                          <input
                            id={`status-${complaint.id}`}
                            value={observation.status}
                            onChange={(event) =>
                              setObservation((current) => ({
                                ...current,
                                status: event.target.value,
                              }))
                            }
                            placeholder="pending review"
                          />
                        </Field>
                        <Field label="Detail" htmlFor={`detail-${complaint.id}`}>
                          <input
                            id={`detail-${complaint.id}`}
                            value={observation.detail}
                            onChange={(event) =>
                              setObservation((current) => ({
                                ...current,
                                detail: event.target.value,
                              }))
                            }
                            placeholder="What the portal or bank told you"
                          />
                        </Field>
                        <div className="form-actions">
                          <button
                            type="button"
                            className="button button-small"
                            disabled={busy}
                            onClick={() => handleObservation(complaint)}
                          >
                            Record observation
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </Card>

      {!isArchived && (
        <Card title="Add a complaint you filed">
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <Field label="Channel" htmlFor="channel">
                <select
                  id="channel"
                  value={form.channel}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, channel: event.target.value }))
                  }
                >
                  {COMPLAINT_CHANNELS.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Organisation" htmlFor="organisation_name">
                <input
                  id="organisation_name"
                  value={form.organisation_name}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      organisation_name: event.target.value,
                    }))
                  }
                />
              </Field>
              <Field label="Reference number" htmlFor="reference_number">
                <input
                  id="reference_number"
                  value={form.reference_number}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      reference_number: event.target.value,
                    }))
                  }
                />
              </Field>
              <Field label="Submission status" htmlFor="submission_status">
                <select
                  id="submission_status"
                  value={form.submission_status}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      submission_status: event.target.value,
                    }))
                  }
                >
                  {SUBMISSION_STATUSES.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
            <div className="form-actions">
              <button type="submit" className="button button-primary" disabled={saving}>
                {saving ? "Saving…" : "Add complaint"}
              </button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
