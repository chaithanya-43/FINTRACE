import { useCallback, useEffect, useMemo, useState } from "react";

import { Icon } from "../Icons";
import {
  Badge,
  Card,
  ConfirmModal,
  EmptyState,
  ErrorBanner,
  Field,
  Loading,
  Notice,
} from "../ui";
import { formatDateTime, formatMoney, labelFor, FRAUD_CATEGORIES } from "../../constants";
import { Link } from "../../router";
import { api } from "../../services/api";

export default function DocumentsTab({ caseId, isArchived }) {
  const [catalog, setCatalog] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusNote, setStatusNote] = useState(null);

  // Stage: "select" | "collect" | "preview"
  const [stage, setStage] = useState("select");
  const [selectedType, setSelectedType] = useState(null);
  const [prefill, setPrefill] = useState(null);
  const [answers, setAnswers] = useState({});
  const [prefillLoading, setPrefillLoading] = useState(false);

  const [activeDraft, setActiveDraft] = useState(null);
  const [editor, setEditor] = useState({
    title: "",
    recipient: "",
    subject: "",
    content: "",
    draft_status: "draft",
  });
  const [viewMode, setViewMode] = useState("preview"); // "preview" | "edit"
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [regenConfirmOpen, setRegenConfirmOpen] = useState(false);

  const loadAll = useCallback(async () => {
    const [catList, draftList] = await Promise.all([
      api.documentCatalog(),
      api.listDocuments(caseId),
    ]);
    setCatalog(catList);
    setDrafts(draftList);
  }, [caseId]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    loadAll()
      .catch((problem) => active && setError(problem))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [loadAll]);

  async function startDocument(documentType) {
    setError(null);
    setStatusNote(null);
    setSelectedType(documentType);
    setPrefillLoading(true);
    try {
      const data = await api.prefillDocument(caseId, documentType);
      setPrefill(data);
      setAnswers(data.prefilled_answers || {});
      setStage("collect");
    } catch (problem) {
      setError(problem);
    } finally {
      setPrefillLoading(false);
    }
  }

  function openDraft(draft) {
    setError(null);
    setStatusNote(null);
    setActiveDraft(draft);
    setSelectedType(draft.document_type);
    setEditor({
      title: draft.title,
      recipient: draft.recipient,
      subject: draft.subject,
      content: draft.content,
      draft_status: draft.draft_status,
    });
    if (draft.intake_answers) {
      setAnswers(draft.intake_answers);
    }
    setViewMode("preview");
    setStage("preview");
  }

  async function handleGenerate(event) {
    event?.preventDefault();
    setError(null);
    setStatusNote(null);
    setBusy(true);
    try {
      const created = await api.generateDocument(caseId, {
        document_type: selectedType,
        intake_answers: answers,
      });
      await loadAll();
      openDraft(created);
      setStatusNote("Draft generated from your case records. Review and edit before submitting.");
    } catch (problem) {
      setError(problem);
    } finally {
      setBusy(false);
      setRegenConfirmOpen(false);
    }
  }

  async function handleSaveDraft(nextStatus) {
    if (!activeDraft) {
      return;
    }
    setError(null);
    setStatusNote(null);
    setBusy(true);
    try {
      const updated = await api.updateDocument(caseId, activeDraft.id, {
        title: editor.title,
        recipient: editor.recipient,
        subject: editor.subject,
        content: editor.content,
        draft_status: nextStatus || editor.draft_status,
      });
      setActiveDraft(updated);
      setEditor({
        title: updated.title,
        recipient: updated.recipient,
        subject: updated.subject,
        content: updated.content,
        draft_status: updated.draft_status,
      });
      await loadAll();
      setStatusNote("Draft changes saved to your case.");
    } catch (problem) {
      setError(problem);
    } finally {
      setBusy(false);
    }
  }

  async function handleDownloadPdf(draftObj = activeDraft) {
    if (!draftObj) {
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const blob = await api.downloadDocumentPdf(caseId, draftObj.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${draftObj.document_type}_draft.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
      await loadAll();
    } catch (problem) {
      setError(problem);
    } finally {
      setBusy(false);
    }
  }

  async function handleCopy() {
    const fullText = `To:\n${editor.recipient}\n\nSubject: ${editor.subject}\n\n${editor.content}`;
    try {
      await navigator.clipboard.writeText(fullText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError(new Error("Could not copy automatically. Switch to Edit mode to copy manually."));
    }
  }

  const groupedFields = useMemo(() => {
    const fields = prefill?.spec?.extra_fields || [];
    const groups = new Map();
    fields.forEach((field) => {
      if (!groups.has(field.section)) {
        groups.set(field.section, []);
      }
      groups.get(field.section).push(field);
    });
    return [...groups.entries()];
  }, [prefill]);

  const estimatedPages = useMemo(() => {
    const lines = (editor.content || "").split("\n").length;
    return Math.max(1, Math.ceil(lines / 42));
  }, [editor.content]);

  if (loading) {
    return <Loading label="Loading Document & Complaint Assistant…" />;
  }

  return (
    <div className="stack">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      {statusNote && <Notice tone="info">{statusNote}</Notice>}

      <Notice tone="warning">
        <strong>Document &amp; Complaint Assistant:</strong> FINTRACE prepares editable draft
        letters from the facts you recorded. Drafts are not legal advice, never fabricate
        legal sections, and are <strong>never submitted automatically</strong> to any bank,
        police station, or government portal.
      </Notice>

      {drafts.length > 0 && (
        <Card
          title="Saved document drafts"
          subtitle="Return to edit, export to PDF, or review before submitting."
        >
          <div className="draft-list">
            {drafts.map((draft) => (
              <div
                key={draft.id}
                className={`draft-row ${activeDraft?.id === draft.id && stage === "preview" ? "active" : ""}`.trim()}
              >
                <div className="draft-row-main">
                  <div className="draft-row-title">
                    <Icon name="documents" size={16} />
                    <strong>{draft.title}</strong>
                    <Badge value={draft.draft_status} />
                  </div>
                  <p className="small muted">
                    Recipient: {draft.recipient.split("\n")[0]} · Updated{" "}
                    {formatDateTime(draft.updated_at)}
                  </p>
                </div>
                <div className="draft-row-actions">
                  <button
                    type="button"
                    className="button button-small button-ghost"
                    onClick={() => openDraft(draft)}
                  >
                    <Icon name="edit" size={14} /> Open &amp; Edit
                  </button>
                  <button
                    type="button"
                    className="button button-small button-primary"
                    onClick={() => handleDownloadPdf(draft)}
                    disabled={busy}
                  >
                    <Icon name="download" size={14} /> PDF
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {stage === "select" && (
        <Card
          title="What document do you need assistance preparing?"
          subtitle="Select a document type. Existing case, transaction, and evidence details are prefilled automatically."
        >
          {prefillLoading ? (
            <Loading label="Prefilling case facts…" />
          ) : (
            <div className="doc-grid">
              {catalog.map((item) => (
                <article key={item.document_type} className="doc-card">
                  <div className="doc-card-head">
                    <span className="doc-code">{item.code}</span>
                    <div>
                      <h3>{item.title}</h3>
                      <p className="doc-recipient">
                        Recipient: {item.default_recipient.split("\n")[0]}
                      </p>
                    </div>
                  </div>
                  <p className="doc-desc">{item.short_description}</p>
                  <div className="doc-reqs">
                    <span className="doc-reqs-label">Required information:</span>
                    <ul>
                      {item.required_information.map((req) => (
                        <li key={req}>{req}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="doc-card-foot">
                    <button
                      type="button"
                      className="button button-primary button-small"
                      disabled={isArchived}
                      onClick={() => startDocument(item.document_type)}
                    >
                      Generate document →
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </Card>
      )}

      {stage === "collect" && prefill && (
        <Card
          title={`Prepare: ${prefill.spec.title}`}
          subtitle="Details from your case are prefilled below. Add only what you know — unknown fields stay marked as 'Not provided'."
          actions={
            <button
              type="button"
              className="button button-ghost button-small"
              onClick={() => setStage("select")}
            >
              ← All documents
            </button>
          }
        >
          <div className="prefill-strip">
            <div>
              <span className="kv-label">Case reference</span>
              <span className="kv-value mono">{prefill.case_summary.public_reference}</span>
            </div>
            <div>
              <span className="kv-label">Category</span>
              <span className="kv-value">
                {labelFor(FRAUD_CATEGORIES, prefill.case_summary.incident_type)}
              </span>
            </div>
            <div>
              <span className="kv-label">Reported loss</span>
              <span className="kv-value">
                {formatMoney(
                  prefill.case_summary.estimated_loss_amount,
                  prefill.case_summary.currency,
                )}
              </span>
            </div>
            <div>
              <span className="kv-label">Transactions</span>
              <span className="kv-value">{prefill.case_summary.transaction_count}</span>
            </div>
            <div>
              <span className="kv-label">Evidence files</span>
              <span className="kv-value">{prefill.case_summary.evidence_count}</span>
            </div>
          </div>

          {prefill.missing_information.length > 0 && (
            <div className="missing-box">
              <strong>Missing or recommended information</strong>
              <p className="small muted">
                You can still generate a draft now; missing fields will appear as &ldquo;Not
                provided&rdquo; for you to verify before submitting.
              </p>
              <ul>
                {prefill.missing_information.map((item) => (
                  <li key={item.key}>{item.label}</li>
                ))}
              </ul>
            </div>
          )}

          <form onSubmit={handleGenerate} className="stack" style={{ marginTop: "1rem" }}>
            {groupedFields.map(([sectionName, fields]) => (
              <div key={sectionName} className="intake-section">
                <h3 className="subhead" style={{ marginTop: 0 }}>
                  {sectionName}
                </h3>
                <div className="form-grid">
                  {fields.map((field) => (
                    <Field
                      key={field.key}
                      label={field.label}
                      htmlFor={`doc-${field.key}`}
                    >
                      {field.type === "select" ? (
                        <select
                          id={`doc-${field.key}`}
                          value={answers[field.key] ?? ""}
                          onChange={(event) =>
                            setAnswers((cur) => ({ ...cur, [field.key]: event.target.value }))
                          }
                        >
                          {(field.options || []).map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>
                      ) : field.type === "textarea" ? (
                        <textarea
                          id={`doc-${field.key}`}
                          rows={2}
                          value={answers[field.key] ?? ""}
                          onChange={(event) =>
                            setAnswers((cur) => ({ ...cur, [field.key]: event.target.value }))
                          }
                        />
                      ) : (
                        <input
                          id={`doc-${field.key}`}
                          value={answers[field.key] ?? ""}
                          onChange={(event) =>
                            setAnswers((cur) => ({ ...cur, [field.key]: event.target.value }))
                          }
                        />
                      )}
                    </Field>
                  ))}
                </div>
              </div>
            ))}

            <div className="sensitive-note">
              <Icon name="emergency" size={16} />
              <span>
                Never enter an OTP, UPI PIN, CVV, or banking password. FINTRACE rejects
                authentication secrets in all fields.
              </span>
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="button button-ghost"
                onClick={() => setStage("select")}
              >
                ← Back to document types
              </button>
              <button type="submit" className="button button-primary" disabled={busy || isArchived}>
                {busy ? "Generating draft…" : "Generate draft document →"}
              </button>
            </div>
          </form>
        </Card>
      )}

      {stage === "preview" && activeDraft && (
        <div className="stack">
          <div className="draft-warning-banner" role="note">
            <Icon name="emergency" size={18} />
            <span>
              <strong>DRAFT — Please review all information before submitting this document to the relevant authority.</strong>{" "}
              This draft is not an official submission.
            </span>
          </div>

          <Card
            title={editor.title}
            subtitle={`Status: ${editor.draft_status} · Estimated ${estimatedPages} A4 page(s)`}
            actions={
              <button
                type="button"
                className="button button-ghost button-small"
                onClick={() => setStage("select")}
              >
                + Prepare another document
              </button>
            }
          >
            <div className="doc-toolbar">
              <div className="doc-mode-tabs" role="tablist" aria-label="Document view mode">
                <button
                  type="button"
                  role="tab"
                  aria-selected={viewMode === "preview"}
                  className={`button button-small ${viewMode === "preview" ? "button-primary" : "button-ghost"}`}
                  onClick={() => setViewMode("preview")}
                >
                  A4 Preview
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={viewMode === "edit"}
                  className={`button button-small ${viewMode === "edit" ? "button-primary" : "button-ghost"}`}
                  onClick={() => setViewMode("edit")}
                >
                  <Icon name="edit" size={14} /> Edit Draft
                </button>
              </div>

              <div className="doc-action-buttons">
                {!isArchived && (
                  <button
                    type="button"
                    className="button button-small button-teal"
                    onClick={() => handleSaveDraft()}
                    disabled={busy}
                  >
                    {busy ? "Saving…" : "Save draft"}
                  </button>
                )}
                <button
                  type="button"
                  className="button button-small button-primary"
                  onClick={() => handleDownloadPdf(activeDraft)}
                  disabled={busy}
                >
                  <Icon name="download" size={14} /> Download PDF
                </button>
                <button
                  type="button"
                  className="button button-small button-ghost"
                  onClick={handleCopy}
                >
                  <Icon name="copy" size={14} /> {copied ? "Copied!" : "Copy text"}
                </button>
                {!isArchived && (
                  <button
                    type="button"
                    className="button button-small button-ghost"
                    onClick={() => setRegenConfirmOpen(true)}
                    disabled={busy}
                  >
                    Regenerate
                  </button>
                )}
              </div>
            </div>

            <div className="doc-workspace-split">
              <div>
                {viewMode === "preview" ? (
                  <div className="a4-stage">
                    <article className="a4-sheet" aria-label="A4 document preview">
                      <header className="a4-sheet-head">
                        <span>FINTRACE · DRAFT COMPLAINT DOCUMENT</span>
                        <span className="mono">{activeDraft.document_type.replaceAll("_", " ")}</span>
                      </header>
                      <div className="a4-draft-stamp">
                        DRAFT — Review before submitting to the relevant authority
                      </div>
                      <div className="a4-meta">
                        <div>
                          <strong>To:</strong>
                          <pre className="a4-pre-inline">{editor.recipient}</pre>
                        </div>
                        <div>
                          <strong>Subject:</strong> {editor.subject}
                        </div>
                      </div>
                      <hr className="a4-rule" />
                      <pre className="a4-body">{editor.content}</pre>
                      <footer className="a4-sheet-foot">
                        <span>Prepared by user with FINTRACE · Not officially submitted</span>
                        <span>Page 1 of {estimatedPages}</span>
                      </footer>
                    </article>
                  </div>
                ) : (
                  <div className="stack">
                    <div className="form-grid">
                      <Field label="Draft title" htmlFor="edit-title">
                        <input
                          id="edit-title"
                          value={editor.title}
                          disabled={isArchived}
                          onChange={(event) =>
                            setEditor((cur) => ({ ...cur, title: event.target.value }))
                          }
                        />
                      </Field>
                      <Field label="Draft status" htmlFor="edit-status">
                        <select
                          id="edit-status"
                          value={editor.draft_status}
                          disabled={isArchived}
                          onChange={(event) =>
                            setEditor((cur) => ({ ...cur, draft_status: event.target.value }))
                          }
                        >
                          <option value="draft">Draft</option>
                          <option value="reviewed">Reviewed</option>
                          <option value="exported">Exported</option>
                        </select>
                      </Field>
                    </div>
                    <Field label="Recipient" htmlFor="edit-recipient">
                      <textarea
                        id="edit-recipient"
                        rows={2}
                        value={editor.recipient}
                        disabled={isArchived}
                        onChange={(event) =>
                          setEditor((cur) => ({ ...cur, recipient: event.target.value }))
                        }
                      />
                    </Field>
                    <Field label="Subject" htmlFor="edit-subject">
                      <input
                        id="edit-subject"
                        value={editor.subject}
                        disabled={isArchived}
                        onChange={(event) =>
                          setEditor((cur) => ({ ...cur, subject: event.target.value }))
                        }
                      />
                    </Field>
                    <Field
                      label="Document content"
                      hint="Edit or correct any placeholders marked 'Not provided' before saving or downloading PDF."
                      htmlFor="edit-content"
                    >
                      <textarea
                        id="edit-content"
                        rows={20}
                        className="mono"
                        value={editor.content}
                        disabled={isArchived}
                        onChange={(event) =>
                          setEditor((cur) => ({ ...cur, content: event.target.value }))
                        }
                      />
                    </Field>
                    {!isArchived && (
                      <div className="form-actions">
                        <button
                          type="button"
                          className="button button-primary"
                          onClick={() => handleSaveDraft()}
                          disabled={busy}
                        >
                          {busy ? "Saving…" : "Save changes"}
                        </button>
                        <button
                          type="button"
                          className="button button-ghost"
                          onClick={() => setViewMode("preview")}
                        >
                          Preview A4 layout
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <aside className="doc-checklist-aside">
                <div className="card subtle-card">
                  <h3>Attachment checklist</h3>
                  <p className="small muted" style={{ marginTop: "0.25rem", marginBottom: "0.75rem" }}>
                    Include supporting records when submitting externally.
                  </p>
                  {!(activeDraft.attachments_checklist || []).length ? (
                    <EmptyState title="No checklist items" />
                  ) : (
                    <ul className="checklist">
                      {(activeDraft.attachments_checklist || []).map((item) => (
                        <li key={item.label} className={item.available ? "ready" : "pending"}>
                          <span className="checklist-dot">{item.available ? "✓" : "!"}</span>
                          <div>
                            <div className="small">
                              <strong>{item.label}</strong>
                            </div>
                            {item.note && <div className="small muted">{item.note}</div>}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                  <div style={{ marginTop: "0.85rem" }}>
                    <Link to={`/cases/${caseId}/evidence`} className="text-button">
                      Manage case evidence →
                    </Link>
                  </div>
                </div>

                <div className="card subtle-card" style={{ marginTop: "0.9rem" }}>
                  <h3>Submission reminder</h3>
                  <p className="small muted" style={{ marginTop: "0.3rem" }}>
                    After submitting externally (e.g. on{" "}
                    <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer">
                      cybercrime.gov.in
                    </a>{" "}
                    or with your bank), record the reference number in the{" "}
                    <Link to={`/cases/${caseId}/complaints`}>Complaint tracker</Link>.
                  </p>
                </div>
              </aside>
            </div>
          </Card>
        </div>
      )}

      <ConfirmModal
        open={regenConfirmOpen}
        title="Regenerate draft from case records?"
        message="This creates a new draft using the latest case, transaction, and evidence records. Your previous draft remains saved in the draft list."
        confirmLabel="Regenerate draft"
        busy={busy}
        onConfirm={handleGenerate}
        onCancel={() => setRegenConfirmOpen(false)}
      />
    </div>
  );
}
