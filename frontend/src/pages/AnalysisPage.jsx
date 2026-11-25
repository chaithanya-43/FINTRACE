import { Link } from "../router";
import { CaseGate, CasePicker, useCaseSelection } from "../components/CaseSelector";
import AnalysisTab from "../components/case/AnalysisTab";
import { Card } from "../components/ui";

export default function AnalysisPage() {
  const { cases, selectedId, setSelectedId, selectedCase, loading, error } = useCaseSelection();

  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Case records</p>
          <h1>Incident analysis</h1>
          <p>
            Deterministic keyword classification, extracted facts and the gaps still
            missing from your record.
          </p>
        </div>
        <Link to="/roadmap" className="button button-ghost">
          View roadmap
        </Link>
      </div>

      <CaseGate loading={loading} error={error} cases={cases}>
        <CasePicker
          cases={cases}
          selectedId={selectedId}
          onChange={setSelectedId}
          selectedCase={selectedCase}
        />
        {selectedId && <AnalysisTab key={selectedId} caseId={selectedId} />}
        <div className="grid-two">
          <Card title="What this does" subtitle="A transparent rules pass, not a language model.">
            <ul className="plain-list">
              <li>Reads the description you recorded and scores fraud-category keywords.</li>
              <li>Extracts amounts, UTRs, UPI IDs and links from free text.</li>
              <li>Lists information that is still missing before a complaint is filed.</li>
              <li>Never overrides a fraud type you already recorded.</li>
            </ul>
          </Card>
          <Card title="How to use the result" subtitle="Confirm before relying on it.">
            <ul className="plain-list">
              <li>Check that the suggested fraud category matches what happened.</li>
              <li>Confirm extracted references against your bank alert.</li>
              <li>Add the missing facts in Transaction details or Evidence centre.</li>
              <li>Re-run the analysis after updating the case.</li>
            </ul>
          </Card>
        </div>
      </CaseGate>
    </div>
  );
}
