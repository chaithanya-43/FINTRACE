import { useCallback, useEffect, useState } from "react";

import { EmptyState, Loading } from "./ui";
import { formatDate, labelFor, FRAUD_CATEGORIES } from "../constants";
import { Link } from "../router";
import { api } from "../services/api";

const SELECTED_CASE_KEY = "fintrace.selected_case";

export function useCaseSelection(preferredId) {
  const [cases, setCases] = useState([]);
  const [selectedId, setSelectedIdState] = useState(
    preferredId || window.localStorage.getItem(SELECTED_CASE_KEY),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const setSelectedId = useCallback((caseId) => {
    setSelectedIdState(caseId);
    if (caseId) {
      window.localStorage.setItem(SELECTED_CASE_KEY, caseId);
    }
  }, []);

  const load = useCallback(async () => {
    const items = await api.listCases();
    setCases(items);
    setSelectedIdState((current) => {
      const stored = window.localStorage.getItem(SELECTED_CASE_KEY);
      const candidates = [preferredId, current, stored];
      const match = candidates.find(
        (candidate) => candidate && items.some((item) => item.id === candidate),
      );
      const next = match || items[0]?.id || null;
      if (next) {
        window.localStorage.setItem(SELECTED_CASE_KEY, next);
      }
      return next;
    });
    return items;
  }, [preferredId]);

  useEffect(() => {
    let active = true;
    load()
      .catch((problem) => active && setError(problem))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [load]);

  const selectedCase = cases.find((item) => item.id === selectedId) || null;

  return { cases, selectedId, setSelectedId, selectedCase, loading, error, reload: load };
}

export function CasePicker({ cases, selectedId, onChange, selectedCase }) {
  if (cases.length === 0) {
    return null;
  }

  return (
    <div className="picker-bar">
      <label htmlFor="case-picker">Case</label>
      <select
        id="case-picker"
        value={selectedId || ""}
        onChange={(event) => onChange(event.target.value)}
      >
        {cases.map((item) => (
          <option key={item.id} value={item.id}>
            {item.public_reference} · {item.title}
          </option>
        ))}
      </select>
      {selectedCase && (
        <div className="picker-meta">
          {labelFor(FRAUD_CATEGORIES, selectedCase.incident_type)} · created{" "}
          {formatDate(selectedCase.created_at)} ·{" "}
          <Link to={`/cases/${selectedCase.id}`}>Open case</Link>
        </div>
      )}
    </div>
  );
}

export function NoCases({ children }) {
  return (
    <div className="card">
      <EmptyState title="No cases yet">
        {children || "Report an incident first, then this screen will show its records."}
      </EmptyState>
      <div className="form-actions">
        <Link to="/report" className="button button-primary">
          Report an incident
        </Link>
      </div>
    </div>
  );
}

export function CaseGate({ loading, error, cases, children }) {
  if (loading) {
    return <Loading label="Loading your cases…" />;
  }
  if (error) {
    return (
      <div className="alert alert-error">
        {error.message || "Could not load your cases."}
      </div>
    );
  }
  if (!cases || cases.length === 0) {
    return <NoCases />;
  }
  return children;
}
