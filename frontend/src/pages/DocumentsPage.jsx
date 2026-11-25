import { Link } from "../router";
import { CaseGate, CasePicker, useCaseSelection } from "../components/CaseSelector";
import DocumentsTab from "../components/case/DocumentsTab";

export default function DocumentsPage() {
  const { cases, selectedId, setSelectedId, selectedCase, loading, error } = useCaseSelection();

  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Case records</p>
          <h1>Document &amp; Complaint Assistant</h1>
          <p>
            Prepare structured complaint letters, dispute notices, follow-ups, and escalations
            prefilled from your case records.
          </p>
        </div>
        <Link to="/complaints" className="button button-ghost">
          Complaint tracker
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
          <DocumentsTab
            key={selectedId}
            caseId={selectedId}
            isArchived={Boolean(selectedCase?.is_archived)}
          />
        )}
      </CaseGate>
    </div>
  );
}
