import { useState } from "react";

import { Card, ErrorBanner, Field, Notice } from "../components/ui";
import {
  AUTHORIZATION_TYPES,
  FRAUD_CATEGORIES,
  FRAUD_CHANNELS,
} from "../constants";
import { navigate } from "../router";
import { api } from "../services/api";

const initialForm = {
  title: "",
  description: "",
  incident_type: "unknown",
  fraud_channel: "unknown",
  incident_occurred_at: "",
  estimated_loss_amount: "",
  currency: "INR",
  reporting_details: "",
};

const initialTransaction = {
  amount: "",
  utr_reference: "",
  authorization_type: "unknown",
  transaction_at: "",
};

export default function NewCasePage() {
  const [form, setForm] = useState(initialForm);
  const [transaction, setTransaction] = useState(initialTransaction);
  const [addTransaction, setAddTransaction] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function update(field) {
    return (event) => setForm((current) => ({ ...current, [field]: event.target.value }));
  }

  function updateTransaction(field) {
    return (event) =>
      setTransaction((current) => ({ ...current, [field]: event.target.value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    if (form.title.trim().length < 3) {
      setError(new Error("Give the case a title of at least 3 characters."));
      return;
    }
    if (form.description.length > 0 && form.description.trim().length < 20) {
      setError(
        new Error("Describe what happened in at least a couple of sentences, or leave it empty."),
      );
      return;
    }

    const payload = {
      title: form.title.trim(),
      description: form.description.trim() || null,
      incident_type: form.incident_type,
      fraud_channel: form.fraud_channel,
      currency: form.currency.toUpperCase() || "INR",
      reporting_details: form.reporting_details.trim() || null,
    };
    if (form.incident_occurred_at) {
      payload.incident_occurred_at = new Date(form.incident_occurred_at).toISOString();
    }
    if (form.estimated_loss_amount !== "") {
      payload.estimated_loss_amount = form.estimated_loss_amount;
    }

    setSubmitting(true);
    try {
      const created = await api.createCase(payload);
      if (addTransaction && transaction.amount !== "") {
        await api.createTransaction(created.id, {
          amount: transaction.amount,
          authorization_type: transaction.authorization_type,
          utr_reference: transaction.utr_reference.trim() || null,
          transaction_at: transaction.transaction_at
            ? new Date(transaction.transaction_at).toISOString()
            : null,
        });
      }
      navigate(`/cases/${created.id}`);
    } catch (problem) {
      setError(problem);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <h1>New case</h1>
          <p className="muted">
            Record only what you know. Unknown details can stay empty or marked
            &ldquo;not sure&rdquo;, and you can update the case later.
          </p>
        </div>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <Notice tone="warning">
        Never enter an OTP, UPI PIN, card CVV, password or banking credential. FINTRACE
        rejects text containing them.
      </Notice>

      <form onSubmit={handleSubmit} noValidate className="stack">
        <Card title="What happened">
          <div className="form-grid">
            <Field label="Incident title" htmlFor="title">
              <input
                id="title"
                value={form.title}
                onChange={update("title")}
                placeholder="Unauthorised UPI debit of ₹15,000"
                required
              />
            </Field>

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
              label="Estimated loss"
              hint="Leave empty if the amount is still unclear."
              htmlFor="estimated_loss_amount"
            >
              <input
                id="estimated_loss_amount"
                type="number"
                min="0"
                step="0.01"
                value={form.estimated_loss_amount}
                onChange={update("estimated_loss_amount")}
              />
            </Field>

            <Field label="Currency" htmlFor="currency">
              <input
                id="currency"
                value={form.currency}
                maxLength={3}
                onChange={update("currency")}
              />
            </Field>

            <Field
              label="What happened, in your words"
              hint="Mention amounts, reference numbers and who contacted you."
              htmlFor="description"
            >
              <textarea
                id="description"
                rows={5}
                value={form.description}
                onChange={update("description")}
              />
            </Field>

            <Field
              label="Where have you already reported it?"
              hint="For example: bank fraud desk, cybercrime portal, police station."
              htmlFor="reporting_details"
            >
              <textarea
                id="reporting_details"
                rows={3}
                value={form.reporting_details}
                onChange={update("reporting_details")}
              />
            </Field>
          </div>
        </Card>

        <Card
          title="First transaction"
          subtitle="Optional now; you can add more transactions after the case is created."
        >
          <label className="checkbox">
            <input
              type="checkbox"
              checked={addTransaction}
              onChange={(event) => setAddTransaction(event.target.checked)}
            />
            Add a transaction with this case
          </label>

          {addTransaction && (
            <div className="form-grid">
              <Field label="Amount" htmlFor="transaction_amount">
                <input
                  id="transaction_amount"
                  type="number"
                  min="0"
                  step="0.01"
                  value={transaction.amount}
                  onChange={updateTransaction("amount")}
                />
              </Field>
              <Field
                label="UTR / reference"
                hint="From your bank statement or alert. Optional."
                htmlFor="utr_reference"
              >
                <input
                  id="utr_reference"
                  value={transaction.utr_reference}
                  onChange={updateTransaction("utr_reference")}
                  maxLength={64}
                />
              </Field>
              <Field label="Did you authorise it?" htmlFor="authorization_type">
                <select
                  id="authorization_type"
                  value={transaction.authorization_type}
                  onChange={updateTransaction("authorization_type")}
                >
                  {AUTHORIZATION_TYPES.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Transaction time" htmlFor="transaction_at">
                <input
                  id="transaction_at"
                  type="datetime-local"
                  value={transaction.transaction_at}
                  onChange={updateTransaction("transaction_at")}
                />
              </Field>
            </div>
          )}
        </Card>

        <div className="form-actions">
          <button type="submit" className="button button-primary" disabled={submitting}>
            {submitting ? "Creating case…" : "Create case"}
          </button>
        </div>
      </form>
    </div>
  );
}
