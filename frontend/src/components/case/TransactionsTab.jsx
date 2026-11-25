import { useCallback, useEffect, useState } from "react";

import { Badge, Card, EmptyState, ErrorBanner, Field, Loading } from "../ui";
import {
  AUTHORIZATION_TYPES,
  formatDateTime,
  formatMoney,
  labelFor,
} from "../../constants";
import { api } from "../../services/api";

const emptyForm = {
  amount: "",
  transaction_at: "",
  authorization_type: "unknown",
  direction: "debit",
  channel: "",
  counterparty_name: "",
  utr_reference: "",
  notes: "",
};

export default function TransactionsTab({ caseId, onChanged, isArchived }) {
  const [transactions, setTransactions] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const items = await api.listTransactions(caseId);
    setTransactions(items);
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

  function update(field) {
    return (event) => setForm((current) => ({ ...current, [field]: event.target.value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    if (!form.amount || Number(form.amount) <= 0) {
      setError(new Error("Enter an amount greater than zero."));
      return;
    }

    setSaving(true);
    try {
      await api.createTransaction(caseId, {
        amount: form.amount,
        transaction_at: form.transaction_at
          ? new Date(form.transaction_at).toISOString()
          : null,
        authorization_type: form.authorization_type,
        direction: form.direction,
        channel: form.channel || null,
        counterparty_name: form.counterparty_name || null,
        utr_reference: form.utr_reference || null,
        notes: form.notes || null,
      });
      setForm(emptyForm);
      await load();
      onChanged?.();
    } catch (problem) {
      setError(problem);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <Loading label="Loading transactions…" />;
  }

  return (
    <div className="stack">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <Card title="Recorded transactions" subtitle="What you have reported so far.">
        {transactions.length === 0 ? (
          <EmptyState title="No transactions recorded">
            Add the debit or credit you are disputing, with its UTR if you have it.
          </EmptyState>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Amount</th>
                  <th>Direction</th>
                  <th>Authorised?</th>
                  <th>Counterparty</th>
                  <th>UTR</th>
                  <th>Status</th>
                  <th>Provenance</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((item) => (
                  <tr key={item.id}>
                    <td>{formatDateTime(item.transaction_at)}</td>
                    <td>{formatMoney(item.amount, item.currency)}</td>
                    <td>{item.direction}</td>
                    <td>{labelFor(AUTHORIZATION_TYPES, item.authorization_type)}</td>
                    <td>{item.counterparty_name || "—"}</td>
                    <td className="mono">{item.utr_reference || "—"}</td>
                    <td>
                      <Badge value={item.status} />
                    </td>
                    <td>
                      <span className="muted small">
                        {item.source} · {item.verification_status.replaceAll("_", " ")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {!isArchived && (
        <Card title="Add a transaction">
          <form onSubmit={handleSubmit} noValidate>
            <div className="form-grid">
              <Field label="Amount" htmlFor="amount">
                <input
                  id="amount"
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.amount}
                  onChange={update("amount")}
                  required
                />
              </Field>
              <Field label="When" htmlFor="transaction_at">
                <input
                  id="transaction_at"
                  type="datetime-local"
                  value={form.transaction_at}
                  onChange={update("transaction_at")}
                />
              </Field>
              <Field label="Direction" htmlFor="direction">
                <select id="direction" value={form.direction} onChange={update("direction")}>
                  <option value="debit">Debit (money left)</option>
                  <option value="credit">Credit (money received)</option>
                </select>
              </Field>
              <Field label="Did you authorise it?" htmlFor="authorization_type">
                <select
                  id="authorization_type"
                  value={form.authorization_type}
                  onChange={update("authorization_type")}
                >
                  {AUTHORIZATION_TYPES.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Channel" htmlFor="channel">
                <input id="channel" value={form.channel} onChange={update("channel")} placeholder="upi, card, net_banking…" />
              </Field>
              <Field label="Counterparty" htmlFor="counterparty_name">
                <input
                  id="counterparty_name"
                  value={form.counterparty_name}
                  onChange={update("counterparty_name")}
                />
              </Field>
              <Field
                label="UTR / reference"
                hint="A UTR cannot repeat within the same case."
                htmlFor="utr_reference"
              >
                <input
                  id="utr_reference"
                  value={form.utr_reference}
                  onChange={update("utr_reference")}
                  maxLength={64}
                />
              </Field>
              <Field label="Notes" htmlFor="notes">
                <input id="notes" value={form.notes} onChange={update("notes")} />
              </Field>
            </div>
            <div className="form-actions">
              <button type="submit" className="button button-primary" disabled={saving}>
                {saving ? "Saving…" : "Add transaction"}
              </button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
