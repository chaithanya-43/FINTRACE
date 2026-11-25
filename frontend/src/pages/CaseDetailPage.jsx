import { useCallback, useEffect, useState } from "react";

import AnalysisTab from "../components/case/AnalysisTab";
import AuditTab from "../components/case/AuditTab";
import ComplaintsTab from "../components/case/ComplaintsTab";
import EvidenceTab from "../components/case/EvidenceTab";
import OverviewTab from "../components/case/OverviewTab";
import RoadmapView from "../components/case/RoadmapView";
import RegulatoryTab from "../components/case/RegulatoryTab";
import TransactionsTab from "../components/case/TransactionsTab";
import { Badge, Card, ErrorBanner, Loading, Notice } from "../components/ui";
import { CASE_STATUSES, formatDate, labelFor, FRAUD_CATEGORIES } from "../constants";
import { Link, navigate } from "../router";
import { api } from "../services/api";

const TABS = [
  ["overview", "Overview"],
  ["transactions", "Transactions"],
  ["evidence", "Evidence"],
  ["analysis", "Analysis"],
  ["regulations", "Regulations"],
  ["roadmap", "Roadmap"],
  ["complaints", "Complaints"],
  ["audit", "Audit"],
];

export default function CaseDetailPage({ caseId, section = "overview" }) {
  const [caseData, setCaseData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const tab = TABS.some(([value]) => value === section) ? section : "overview";

  const load = useCallback(async () => {
    const [caseRecord, counts] = await Promise.all([
      api.getCase(caseId),
      api.caseSummary(caseId),
    ]);
    setCaseData(caseRecord);
    setSummary(counts);
  }, [caseId]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    load()
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
  }, [load]);

  async function handleStatusChange(event) {
    setActionError(null);
    try {
      const updated = await api.changeCaseStatus(caseId, event.target.value);
      setCaseData(updated);
    } catch (problem) {
      setActionError(problem);
      await load().catch(() => undefined);
    }
  }

  async function handleArchive() {
    setActionError(null);
    try {
      await api.archiveCase(caseId);
      await load();
    } catch (problem) {
      setActionError(problem);
    }
  }

  if (loading) {
    return <Loading label="Loading case…" />;
  }

  if (error || !caseData) {
    return (
      <div className="stack">
        <ErrorBanner error={error || new Error("Case not found.")} />
        <Link to="/dashboard" className="button">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="stack">
      <p className="breadcrumb">
        <Link to="/dashboard">Case dashboard</Link> /{" "}
        <span className="mono">{caseData.public_reference}</span>
      </p>

      <div className="page-heading">
        <div>
          <h1>{caseData.title}</h1>
          <p>
            {labelFor(FRAUD_CATEGORIES, caseData.incident_type)} · created{" "}
            {formatDate(caseData.created_at)} · {caseData.completeness_status.replaceAll("_", " ")}
          </p>
        </div>
        <div className="heading-actions">
          <Badge value={caseData.internal_status} />
          {caseData.is_archived && <Badge value="archived" />}
          <label className="inline-field">
            <span className="sr-only">Change status</span>
            <select value={caseData.internal_status} onChange={handleStatusChange}>
              {CASE_STATUSES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          {!caseData.is_archived && (
            <button type="button" className="button button-ghost" onClick={handleArchive}>
              Archive
            </button>
          )}
        </div>
      </div>

      <ErrorBanner error={actionError} onDismiss={() => setActionError(null)} />

      {caseData.is_archived && (
        <Notice tone="warning">
          This case is archived. Records are retained but no further changes are accepted.
        </Notice>
      )}

      <nav className="tabs" aria-label="Case sections">
        {TABS.map(([value, label]) => (
          <button
            key={value}
            type="button"
            className={`tab ${tab === value ? "tab-active" : ""}`.trim()}
            onClick={() => {
              navigate(`/cases/${caseId}/${value}`);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            {label}
          </button>
        ))}
      </nav>

      {tab === "overview" && (
        <OverviewTab caseData={caseData} summary={summary} onCaseChange={load} />
      )}
      {tab === "transactions" && (
        <TransactionsTab
          caseId={caseId}
          onChanged={load}
          isArchived={caseData.is_archived}
        />
      )}
      {tab === "evidence" && <EvidenceTab caseId={caseId} isArchived={caseData.is_archived} />}
      {tab === "analysis" && <AnalysisTab caseId={caseId} />}
      {tab === "regulations" && <RegulatoryTab caseId={caseId} />}
      {tab === "roadmap" && (
        <RoadmapView caseId={caseId} isArchived={caseData.is_archived} />
      )}
      {tab === "complaints" && (
        <ComplaintsTab caseId={caseId} isArchived={caseData.is_archived} />
      )}
      {tab === "audit" && <AuditTab caseId={caseId} />}

      <Card title="About this workspace" className="subtle-card">
        <p className="muted small">
          FINTRACE records what you report and evaluates stored rules against it. It does
          not contact your bank, file complaints for you, or make legal determinations.
        </p>
      </Card>
    </div>
  );
}
