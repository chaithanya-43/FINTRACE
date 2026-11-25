import { Link } from "../router";
import { CaseGate, CasePicker, useCaseSelection } from "../components/CaseSelector";
import RoadmapView from "../components/case/RoadmapView";

export default function RoadmapPage() {
  const { cases, selectedId, setSelectedId, selectedCase, loading, error } = useCaseSelection();

  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Recovery</p>
          <h1>Recovery roadmap</h1>
          <p>Prioritised actions with deadlines. Tick them off as you complete them.</p>
        </div>
        <div className="heading-actions">
          <Link to="/emergency" className="button button-danger">
            Emergency help
          </Link>
          <Link to="/report" className="button button-primary">
            + New report
          </Link>
        </div>
      </div>

      <CaseGate loading={loading} error={error} cases={cases}>
        <CasePicker
          cases={cases}
          selectedId={selectedId}
          onChange={setSelectedId}
          selectedCase={selectedCase}
        />
        {selectedId && (
          <RoadmapView key={selectedId} caseId={selectedId} isArchived={Boolean(selectedCase?.is_archived)} />
        )}
      </CaseGate>
    </div>
  );
}
