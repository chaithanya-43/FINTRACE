import { useCallback, useEffect, useState } from "react";

import { Badge, Card, EmptyState, ErrorBanner, Field, Loading, Notice } from "../ui";
import { formatDateTime } from "../../constants";
import { api } from "../../services/api";

export default function EvidenceTab({ caseId, isArchived }) {
  const [items, setItems] = useState([]);
  const [file, setFile] = useState(null);
  const [evidenceType, setEvidenceType] = useState("bank_alert");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [verification, setVerification] = useState({});
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    setItems(await api.listEvidence(caseId));
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

  async function handleUpload(event) {
    event.preventDefault();
    setError(null);
    if (!file) {
      setError(new Error("Choose a file to upload."));
      return;
    }
    setUploading(true);
    try {
      await api.uploadEvidence(caseId, file, {
        evidence_type: evidenceType,
        description,
      });
      setFile(null);
      setDescription("");
      event.target.reset();
      await load();
    } catch (problem) {
      setError(problem);
    } finally {
      setUploading(false);
    }
  }

  async function handleVerify(evidenceId) {
    setBusyId(evidenceId);
    setError(null);
    try {
      const result = await api.verifyEvidence(caseId, evidenceId);
      setVerification((current) => ({ ...current, [evidenceId]: result }));
      await load();
    } catch (problem) {
      setError(problem);
    } finally {
      setBusyId(null);
    }
  }

  async function handleSign(evidenceId) {
    setBusyId(evidenceId);
    setError(null);
    try {
      await api.signEvidence(caseId, evidenceId);
      await load();
    } catch (problem) {
      setError(problem);
    } finally {
      setBusyId(null);
    }
  }

  async function handleDownload(item) {
    setError(null);
    try {
      const blob = await api.downloadEvidence(caseId, item.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = item.original_filename;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (problem) {
      setError(problem);
    }
  }

  if (loading) {
    return <Loading label="Loading evidence…" />;
  }

  return (
    <div className="stack">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <Notice>
        A SHA-256 hash shows that the stored file matches the bytes recorded at upload. It
        does not prove the file came from the claimed source or existed at a particular
        time.
      </Notice>

      <Card title="Evidence files">
        {items.length === 0 ? (
          <EmptyState title="No evidence uploaded">
            Upload bank alerts, chat screenshots or a statement. Files are stored privately
            and only served through an authorised request.
          </EmptyState>
        ) : (
          <div className="stack">
            {items.map((item) => (
              <article key={item.id} className="evidence-row">
                <div className="evidence-main">
                  <div className="evidence-title">
                    <strong>{item.original_filename}</strong>
                    <Badge value={item.verification_status} />
                    <span className="muted small">
                      {item.evidence_type.replaceAll("_", " ")} ·{" "}
                      {(item.byte_size / 1024).toFixed(1)} KB · {formatDateTime(item.created_at)}
                    </span>
                  </div>
                  <p className="hash mono" title="SHA-256 of the stored bytes">
                    {item.sha256_hash}
                  </p>
                  {item.description && <p className="muted small">{item.description}</p>}
                  {verification[item.id] && (
                    <div className="verify-result">
                      <p>
                        Recomputed hash matches:{" "}
                        <strong>{verification[item.id].hash_matches ? "yes" : "no"}</strong>
                        {" · "}signature: {verification[item.id].signature_status}
                      </p>
                      {verification[item.id].notes.map((note) => (
                        <p key={note} className="muted small">
                          {note}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
                <div className="evidence-actions">
                  <button
                    type="button"
                    className="button button-small"
                    onClick={() => handleVerify(item.id)}
                    disabled={busyId === item.id}
                  >
                    {busyId === item.id ? "Checking…" : "Verify"}
                  </button>
                  <button
                    type="button"
                    className="button button-small button-ghost"
                    onClick={() => handleDownload(item)}
                  >
                    Download
                  </button>
                  {verification[item.id]?.hash_matches && (
                    <button
                      type="button"
                      className="button button-small button-ghost"
                      onClick={() => handleSign(item.id)}
                      disabled={busyId === item.id}
                    >
                      Sign
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </Card>

      {!isArchived && (
        <Card title="Upload evidence">
          <form onSubmit={handleUpload}>
            <div className="form-grid">
              <Field label="File" hint="PDF, image, text or zip up to 10 MB.">
                <input
                  type="file"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
              </Field>
              <Field label="Evidence type" htmlFor="evidence_type">
                <select
                  id="evidence_type"
                  value={evidenceType}
                  onChange={(event) => setEvidenceType(event.target.value)}
                >
                  <option value="bank_alert">Bank alert</option>
                  <option value="statement">Statement</option>
                  <option value="chat_screenshot">Chat screenshot</option>
                  <option value="transaction_receipt">Transaction receipt</option>
                  <option value="complaint_receipt">Complaint receipt</option>
                  <option value="other">Other</option>
                </select>
              </Field>
              <Field label="Description" htmlFor="evidence_description">
                <input
                  id="evidence_description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                />
              </Field>
            </div>
            <div className="form-actions">
              <button type="submit" className="button button-primary" disabled={uploading}>
                {uploading ? "Uploading…" : "Upload"}
              </button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
