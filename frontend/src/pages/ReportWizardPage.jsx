import { useState } from "react";

import { ErrorBanner, Field, Notice } from "../components/ui";
import {
  AUTHORIZATION_TYPES,
  FRAUD_CATEGORIES,
  FRAUD_CHANNELS,
  formatMoney,
  labelFor,
} from "../constants";
import { Link, navigate } from "../router";
import { api } from "../services/api";

const STEPS = [
  ["incident", "The incident", "What happened and how you were contacted"],
  ["transaction", "The transaction", "Amount, UTR and whether you authorised it"],
  ["evidence", "Evidence", "Optional supporting files"],
  ["review", "Review & confirm", "Check the details before saving"],
];

const EVIDENCE_TYPES = [
  ["bank_alert", "Bank SMS / email alert"],
  ["statement", "Bank statement"],
  ["chat_screenshot", "Chat screenshot"],
  ["transaction_receipt", "Transaction receipt"],
  ["complaint_receipt", "Complaint acknowledgement"],
  ["other", "Other"],
];

function nowLocal() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 16);
}

const initialForm = {
  title: "",
  incident_type: "otp_phishing",
  fraud_channel: "phone_call",
  incident_occurred_at: nowLocal(),
  description: "",
  reporting_details: "",
  amount: "",
  transaction_at: nowLocal(),
  direction: "debit",
  authorization_type: "unauthorized",
  counterparty_name: "",
  utr_reference: "",
  transaction_channel: "upi",
  evidence_type: "bank_alert",
  evidence_description: "",
};

export default function ReportWizardPage() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(initialForm);
  const [file, setFile] = useState(null);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function update(field) {
    return (event) =>
      setForm((current) => ({ ...current, [field]: event.target.value }));
  }

  function validate(currentStep) {
    if (currentStep === 0) {
      if (form.description.trim().length < 20) {
        return "Describe what happened in at least a couple of sentences — this drives the classification.";
      }
      if (!form.incident_occurred_at) {
        return "Enter when the incident happened (an approximate time is fine).";
      }
    }
    if (currentStep === 1) {
      const amount = Number(form.amount);
      if (!form.amount || Number.isNaN(amount) || amount <= 0) {
        return "Enter the amount that left your account. It must be greater than zero.";
      }
    }
    return null;
  }

  function goNext() {
    const problem = validate(step);
    if (problem) {
      setError(new Error(problem));
      return;
    }
    setError(null);
    setStep((current) => Math.min(current + 1, STEPS.length - 1));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function goBack() {
    setError(null);
    setStep((current) => Math.max(current - 1, 0));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleSubmit() {
    setError(null);
    if (!confirmed) {
      setError(new Error("Confirm that the information is accurate before saving the case."));
      return;
    }
    const problem = validate(0) || validate(1);
    if (problem) {
      setError(new Error(problem));
      return;
    }

    const category = labelFor(FRAUD_CATEGORIES, form.incident_type);
    const title =
      form.title.trim() ||
      `${category} incident${form.amount ? ` — ${formatMoney(form.amount)}` : ""}`;

    setSubmitting(true);
    let created;
    try {
      created = await api.createCase({
        title: title.slice(0, 200),
        description: form.description.trim(),
        incident_type: form.incident_type,
        fraud_channel: form.fraud_channel,
        incident_occurred_at: new Date(form.incident_occurred_at).toISOString(),
        estimated_loss_amount: form.amount,
        currency: "INR",
        reporting_details: form.reporting_details.trim() || null,
      });
    } catch (creationProblem) {
      setError(creationProblem);
      setSubmitting(false);
      return;
    }

    try {
      await api.createTransaction(created.id, {
        amount: form.amount,
        currency: "INR",
        transaction_at: new Date(form.transaction_at).toISOString(),
        direction: form.direction,
        authorization_type: form.authorization_type,
        channel: form.transaction_channel || null,
        counterparty_name: form.counterparty_name.trim() || null,
        utr_reference: form.utr_reference.trim() || null,
      });
    } catch {
      // The case exists; the transaction can be added again from the case screen.
    }

    if (file) {
      try {
        await api.uploadEvidence(created.id, file, {
          evidence_type: form.evidence_type,
          description: form.evidence_description.trim() || null,
        });
      } catch {
        // Evidence is optional; the case is still usable without it.
      }
    }

    try {
      await api.analyze(created.id);
    } catch {
      // Analysis is deterministic and can be re-run later.
    }

    try {
      await api.roadmap(created.id);
    } catch {
      // The roadmap is generated on first view if this call fails.
    }

    navigate(`/cases/${created.id}/roadmap`);
  }

  const stepMeta = STEPS[step];
  const progress = Math.round(((step + 1) / STEPS.length) * 100);

  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">
            <Link to="/dashboard">Dashboard</Link> / Report an incident
          </p>
          <h1>Report a fraud incident</h1>
          <p>
            Answer what you can. Unknown details can stay blank or marked “not sure”, and
            you can update the case afterwards.
          </p>
        </div>
        <Link to="/emergency" className="button button-danger">
          Money still moving? Call 1930
        </Link>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="wizard-shell">
        <aside className="wizard-progress">
          <h2>Your progress</h2>
          {STEPS.map(([key, label, hint], index) => (
            <div
              key={key}
              className={`wizard-step ${index === step ? "active" : ""} ${
                index < step ? "complete" : ""
              }`.trim()}
            >
              <span className="wizard-step-index">{index < step ? "✓" : index + 1}</span>
              <span>
                <span className="wizard-step-label">{label}</span>
                <span className="wizard-step-hint">{hint}</span>
              </span>
            </div>
          ))}
          <div className="wizard-progress-bar">
            <span style={{ width: `${progress}%` }} />
          </div>
        </aside>

        <section className="wizard-card">
          <div className="wizard-card-head">
            <div className="step-eyebrow">
              Step {step + 1} of {STEPS.length}
            </div>
            <h2>{stepMeta[1]}</h2>
            <p>{stepMeta[2]}</p>
          </div>

          {step === 0 && (
            <div className="stack">
              <div className="form-grid">
                <Field label="Type of fraud" htmlFor="incident_type">
                  <select id="incident_type" value={form.incident_type} onChange={update("incident_type")}>
                    {FRAUD_CATEGORIES.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="How you were contacted" htmlFor="fraud_channel">
                  <select id="fraud_channel" value={form.fraud_channel} onChange={update("fraud_channel")}>
                    {FRAUD_CHANNELS.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="When it happened" htmlFor="incident_occurred_at">
                  <input
                    id="incident_occurred_at"
                    type="datetime-local"
                    value={form.incident_occurred_at}
                    onChange={update("incident_occurred_at")}
                  />
                </Field>
                <Field
                  label="Case title"
                  hint="Optional — we will create one from the fraud type and amount."
                  htmlFor="title"
                >
                  <input
                    id="title"
                    value={form.title}
                    onChange={update("title")}
                    placeholder="OTP scam — unauthorised UPI debit"
                  />
                </Field>
              </div>

              <Field
                label="What happened, in your words"
                hint="Mention the caller or message, the amount, and any reference numbers. Minimum 20 characters."
                htmlFor="description"
              >
                <textarea
                  id="description"
                  rows={6}
                  value={form.description}
                  onChange={update("description")}
                  placeholder="I received a call from someone claiming to be from my bank. They said my account would be blocked and asked me to share an OTP. Shortly after, ₹25,000 was debited by UPI."
                />
              </Field>

              <Field
                label="Where have you already reported it?"
                hint="Optional. For example: bank fraud desk, cybercrime portal, police station."
                htmlFor="reporting_details"
              >
                <textarea
                  id="reporting_details"
                  rows={2}
                  value={form.reporting_details}
                  onChange={update("reporting_details")}
                />
              </Field>

              <div className="sensitive-note">
                <span aria-hidden="true">⚠</span>
                <span>
                  Never enter an OTP, UPI PIN, CVV, password or banking credential.
                  FINTRACE rejects text containing them and will never ask for them.
                </span>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="stack">
              <div className="form-grid">
                <Field label="Amount debited (INR)" htmlFor="amount">
                  <input
                    id="amount"
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.amount}
                    onChange={update("amount")}
                    placeholder="25000"
                  />
                </Field>
                <Field label="Transaction date & time" htmlFor="transaction_at">
                  <input
                    id="transaction_at"
                    type="datetime-local"
                    value={form.transaction_at}
                    onChange={update("transaction_at")}
                  />
                </Field>
                <Field label="Direction" htmlFor="direction">
                  <select id="direction" value={form.direction} onChange={update("direction")}>
                    <option value="debit">Debit — money left my account</option>
                    <option value="credit">Credit — money was received</option>
                  </select>
                </Field>
                <Field label="Channel" htmlFor="transaction_channel">
                  <select
                    id="transaction_channel"
                    value={form.transaction_channel}
                    onChange={update("transaction_channel")}
                  >
                    <option value="upi">UPI</option>
                    <option value="card">Card</option>
                    <option value="net_banking">Net banking</option>
                    <option value="mobile_app">Mobile app</option>
                    <option value="other">Other</option>
                  </select>
                </Field>
                <Field label="UTR / reference number" hint="Optional, from your bank alert." htmlFor="utr_reference">
                  <input
                    id="utr_reference"
                    value={form.utr_reference}
                    onChange={update("utr_reference")}
                    maxLength={64}
                  />
                </Field>
                <Field label="Paid to (name or UPI ID)" hint="Optional." htmlFor="counterparty_name">
                  <input
                    id="counterparty_name"
                    value={form.counterparty_name}
                    onChange={update("counterparty_name")}
                    maxLength={200}
                  />
                </Field>
              </div>

              <div>
                <h3 className="subhead" style={{ marginTop: 0 }}>
                  Did you authorise this payment?
                </h3>
                <p className="small muted" style={{ marginBottom: "0.7rem" }}>
                  This changes the recovery plan. An unauthorised debit and a payment you
                  approved under deception are handled through different first actions.
                </p>
                <div className="choice-grid">
                  {AUTHORIZATION_TYPES.map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      className={`choice-card ${form.authorization_type === value ? "selected" : ""}`.trim()}
                      onClick={() => setForm((current) => ({ ...current, authorization_type: value }))}
                    >
                      <span className="choice-dot">{form.authorization_type === value ? "✓" : ""}</span>
                      <span>
                        <strong>{label}</strong>
                        <span className="hint">
                          {value === "unauthorized" &&
                            "I did not approve it. Someone else initiated the payment."}
                          {value === "authorized_deceived" &&
                            "I approved the payment, but the recipient or reason was a deception."}
                          {value === "unknown" && "I am not sure how the payment was initiated."}
                        </span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="stack">
              <Field label="Supporting file" hint="Bank alert, statement, chat screenshot, PDF, image or text. Up to 10 MB.">
                <input
                  type="file"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                  accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.zip"
                />
              </Field>
              {file && (
                <p className="small muted">
                  Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
                </p>
              )}
              <div className="form-grid">
                <Field label="Evidence type" htmlFor="evidence_type">
                  <select
                    id="evidence_type"
                    value={form.evidence_type}
                    onChange={update("evidence_type")}
                  >
                    {EVIDENCE_TYPES.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Description" hint="What does this file show?" htmlFor="evidence_description">
                  <input
                    id="evidence_description"
                    value={form.evidence_description}
                    onChange={update("evidence_description")}
                  />
                </Field>
              </div>
              <Notice>
                You can skip this step. Evidence can be uploaded later, and the case still
                works without it — the roadmap will include a reminder to preserve it.
              </Notice>
            </div>
          )}

          {step === 3 && (
            <div className="stack">
              <div className="review-block">
                <h3>Incident</h3>
                <dl className="detail-list detail-list-inline">
                  <div>
                    <dt>Type</dt>
                    <dd>{labelFor(FRAUD_CATEGORIES, form.incident_type)}</dd>
                  </div>
                  <div>
                    <dt>Channel</dt>
                    <dd>{labelFor(FRAUD_CHANNELS, form.fraud_channel)}</dd>
                  </div>
                  <div>
                    <dt>Occurred</dt>
                    <dd>{form.incident_occurred_at?.replace("T", " ")}</dd>
                  </div>
                  <div>
                    <dt>Already reported</dt>
                    <dd>{form.reporting_details.trim() || "Not recorded"}</dd>
                  </div>
                  <div style={{ gridColumn: "1 / -1" }}>
                    <dt>Description</dt>
                    <dd className="prose">{form.description.trim()}</dd>
                  </div>
                </dl>
              </div>

              <div className="review-block">
                <h3>Transaction</h3>
                <dl className="detail-list detail-list-inline">
                  <div>
                    <dt>Amount</dt>
                    <dd>{formatMoney(form.amount || 0)}</dd>
                  </div>
                  <div>
                    <dt>Authorisation</dt>
                    <dd>{labelFor(AUTHORIZATION_TYPES, form.authorization_type)}</dd>
                  </div>
                  <div>
                    <dt>UTR</dt>
                    <dd className="mono">{form.utr_reference || "Not recorded"}</dd>
                  </div>
                  <div>
                    <dt>Transaction time</dt>
                    <dd>{form.transaction_at?.replace("T", " ")}</dd>
                  </div>
                </dl>
              </div>

              <div className="review-block">
                <h3>Evidence</h3>
                <p className="small muted">
                  {file
                    ? `${file.name} · ${(file.size / 1024).toFixed(1)} KB`
                    : "No file selected — you can add evidence later from the Evidence centre."}
                </p>
              </div>

              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(event) => setConfirmed(event.target.checked)}
                />
                <span>
                  I confirm this information is accurate to the best of my knowledge. I
                  understand FINTRACE does not contact my bank or file official complaints
                  for me.
                </span>
              </label>
            </div>
          )}

          <div className="wizard-nav">
            <div>
              {step > 0 && (
                <button type="button" className="button button-ghost" onClick={goBack} disabled={submitting}>
                  ← Back
                </button>
              )}
            </div>
            <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
              {step === 2 && (
                <button
                  type="button"
                  className="button button-ghost"
                  onClick={() => setStep(3)}
                  disabled={submitting}
                >
                  Skip for now
                </button>
              )}
              {step < STEPS.length - 1 ? (
                <button type="button" className="button button-primary" onClick={goNext}>
                  Continue →
                </button>
              ) : (
                <button
                  type="button"
                  className="button button-primary button-large"
                  disabled={submitting}
                  onClick={handleSubmit}
                >
                  {submitting ? "Saving your case…" : "Save case & build roadmap"}
                </button>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
