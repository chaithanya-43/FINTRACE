import { Link } from "../router";
import { CaseGate, CasePicker, useCaseSelection } from "../components/CaseSelector";
import EvidenceTab from "../components/case/EvidenceTab";

export default function EvidencePage() {
  const { cases, selectedId, setSelectedId, selectedCase, loading, error } = useCaseSelection();

  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Case records</p>
          <h1>Evidence centre</h1>
          <p>
            Private uploads with a SHA-256 hash. Verify the stored bytes at any time — a
            hash proves integrity, not origin.
          </p>
        </div>
        <Link to="/report" className="button button-primary">
          + Report an incident
        </Link>
      </div>

      <CaseGate loading={loading} error={error} cases={cases}>
        <CasePicker
          cases={cases}
          selectedId={selectedId}
          onChange={setSelectedId}
          selectedCase={selectedCase}
        />
        {selectedId && (
          <EvidenceTab
            key={selectedId}
            caseId={selectedId}
            isArchived={Boolean(selectedCase?.is_archived)}
          />
        )}
      </CaseGate>
    </div>
  );
}
