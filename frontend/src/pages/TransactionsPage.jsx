import { Link } from "../router";
import { CaseGate, CasePicker, useCaseSelection } from "../components/CaseSelector";
import TransactionsTab from "../components/case/TransactionsTab";

export default function TransactionsPage() {
  const { cases, selectedId, setSelectedId, selectedCase, loading, error, reload } =
    useCaseSelection();

  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Case records</p>
          <h1>Transaction details</h1>
          <p>
            Every disputed debit or credit, with its UTR and — most importantly — whether
            you authorised it.
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
          <TransactionsTab
            key={selectedId}
            caseId={selectedId}
            onChanged={reload}
            isArchived={Boolean(selectedCase?.is_archived)}
          />
        )}
      </CaseGate>
    </div>
  );
}
