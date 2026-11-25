import { Link } from "../router";
import { CaseGate, CasePicker, useCaseSelection } from "../components/CaseSelector";
import AuditTab from "../components/case/AuditTab";

export default function AuditPage() {
  const { cases, selectedId, setSelectedId, selectedCase, loading, error } = useCaseSelection();

  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Assurance</p>
          <h1>Audit history</h1>
          <p>
            An append-only record of every change to a case — who acted, on what, and when.
          </p>
        </div>
        <Link to="/dashboard" className="button button-ghost">
          Back to dashboard
        </Link>
      </div>

      <div className="alert alert-info">
        <div>
          Audit rows are append-only at the database level. No user, including an
          administrator, can edit or delete them through FINTRACE.
        </div>
      </div>

      <CaseGate loading={loading} error={error} cases={cases}>
        <CasePicker
          cases={cases}
          selectedId={selectedId}
          onChange={setSelectedId}
          selectedCase={selectedCase}
        />
        {selectedId && <AuditTab key={selectedId} caseId={selectedId} />}
      </CaseGate>
    </div>
  );
}
