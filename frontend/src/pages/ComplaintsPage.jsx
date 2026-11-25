import { Link } from "../router";
import { CaseGate, CasePicker, useCaseSelection } from "../components/CaseSelector";
import ComplaintsTab from "../components/case/ComplaintsTab";

export default function ComplaintsPage() {
  const { cases, selectedId, setSelectedId, selectedCase, loading, error } = useCaseSelection();

  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Case records</p>
          <h1>Complaint tracker</h1>
          <p>
            Record complaints you filed yourself, their reference numbers, and what each
            organisation tells you over time.
          </p>
        </div>
        <Link to="/emergency" className="button button-ghost">
          Official channels
        </Link>
      </div>

      <div className="alert alert-warning">
        <div>
          <strong>Nothing is submitted automatically.</strong> FINTRACE has no integration
          with banks, police or government portals. It records what you filed and what you
          were told; it cannot create an official acknowledgement.
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
          <ComplaintsTab
            key={selectedId}
            caseId={selectedId}
            isArchived={Boolean(selectedCase?.is_archived)}
          />
        )}
      </CaseGate>

      <div className="grid-three">
        <div className="contact-card">
          <div className="contact-name">Cybercrime helpline</div>
          <div className="contact-value emergency">
            <a href="tel:1930">1930</a>
          </div>
          <p className="small muted">Record the reference you are given as a complaint.</p>
        </div>
        <div className="contact-card">
          <div className="contact-name">Reporting portal</div>
          <div className="contact-value" style={{ fontSize: "1rem" }}>
            <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer">
              cybercrime.gov.in
            </a>
          </div>
          <p className="small muted">File the complaint yourself and save the acknowledgement.</p>
        </div>
        <div className="contact-card">
          <div className="contact-name">Bank fraud desk</div>
          <div className="contact-value" style={{ fontSize: "1rem" }}>
            Number on your card
          </div>
          <p className="small muted">Ask for a written ticket number and add it here.</p>
        </div>
      </div>
    </div>
  );
}
