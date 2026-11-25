import { Link } from "../router";

const CAPABILITIES = [
  {
    icon: "◎",
    title: "Personalised recovery roadmap",
    body: "A prioritised plan built from your incident type, transaction authorisation and evidence — not generic advice.",
  },
  {
    icon: "⇄",
    title: "Unauthorised vs deceived",
    body: "A payment you never approved and a payment you approved under deception need different first actions. FINTRACE separates them.",
  },
  {
    icon: "▤",
    title: "Evidence integrity",
    body: "Upload alerts, screenshots and statements. Every file is hashed with SHA-256 and verified on demand.",
  },
  {
    icon: "§",
    title: "Regulatory intelligence",
    body: "Versioned, dated rules evaluated deterministically. Each result cites its source and is marked verified or unverified.",
  },
  {
    icon: "✉",
    title: "Complaint tracking",
    body: "Record what you filed and what the bank or portal told you, with an append-only status history.",
  },
  {
    icon: "◷",
    title: "Audit history",
    body: "Every change to a case is recorded in an append-only trail, so the sequence of events stays intact.",
  },
];

const STEPS = [
  ["Tell us what happened", "Answer a guided questionnaire about the incident and the contact you received."],
  ["Add the transaction", "Record the amount, UTR and — crucially — whether you authorised the payment."],
  ["Preserve evidence", "Upload the bank alert or chat screenshot so the record has verifiable support."],
  ["Work the roadmap", "Follow prioritised actions with deadlines, and tick them off as you complete them."],
];

export default function LandingPage() {
  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <div>
            <span className="hero-eyebrow">Financial fraud recovery workspace</span>
            <h1>
              After the money moves, know exactly <em>what to do next</em>.
            </h1>
            <p className="hero-lead">
              FINTRACE turns a chaotic fraud incident into a clear, prioritised recovery
              plan — with the evidence, complaints and audit history kept together in one
              case file.
            </p>
            <div className="hero-actions">
              <Link to="/register" className="button button-primary button-large">
                Report an incident
              </Link>
              <Link
                to="/emergency"
                className="button button-large"
                style={{ background: "transparent", color: "#fff", borderColor: "rgba(255,255,255,0.3)" }}
              >
                Emergency assistance
              </Link>
            </div>
            <div className="hero-trust">
              <div>
                <strong>Deterministic</strong>
                Rules, not guesses
              </div>
              <div>
                <strong>SHA-256</strong>
                Evidence integrity
              </div>
              <div>
                <strong>Append-only</strong>
                Audit trail
              </div>
              <div>
                <strong>No credentials</strong>
                Never an OTP or PIN
              </div>
            </div>
          </div>

          <div className="hero-panel" aria-label="Illustrative recovery roadmap">
            <div className="hero-panel-head">
              <span>Illustrative roadmap</span>
              <span className="hero-urgent">First hours</span>
            </div>
            <div className="hero-action done">
              <span className="hero-check">✓</span>
              <div>
                <strong>Call the 1930 cybercrime helpline</strong>
                <span>Done · reference noted</span>
              </div>
            </div>
            <div className="hero-action">
              <span className="hero-check" />
              <div>
                <strong>Report on cybercrime.gov.in</strong>
                <span>Due within 24 hours</span>
              </div>
            </div>
            <div className="hero-action">
              <span className="hero-check" />
              <div>
                <strong>Notify your bank’s fraud desk</strong>
                <span>Ask about a freeze on further debits</span>
              </div>
            </div>
            <div className="hero-progress">
              <span style={{ width: "33%" }} />
            </div>
            <p style={{ fontSize: "0.72rem", color: "#93a4c0" }}>
              1 of 3 complete · Example content, not a real case
            </p>
          </div>
        </div>
      </section>

      <section className="public-section" id="how">
        <div className="section-head">
          <div className="section-eyebrow">How it works</div>
          <h2 className="section-title">A guided path from incident to action</h2>
          <p className="section-lead">
            The questionnaire takes a few minutes. Everything you record stays in one case
            file you can return to.
          </p>
        </div>
        <div className="step-grid">
          {STEPS.map(([title, body], index) => (
            <div className="step-card" key={title}>
              <div className="step-number">{index + 1}</div>
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="public-section" id="capabilities" style={{ paddingTop: 0 }}>
        <div className="section-head">
          <div className="section-eyebrow">What is inside</div>
          <h2 className="section-title">Built for the first 72 hours — and the follow-up</h2>
          <p className="section-lead">
            Recovery is not one phone call. FINTRACE keeps the plan, the proof and the
            official responses in the same place.
          </p>
        </div>
        <div className="feature-grid">
          {CAPABILITIES.map((item) => (
            <div className="feature-card" key={item.title}>
              <div className="feature-icon" aria-hidden="true">
                {item.icon}
              </div>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="public-section" style={{ paddingTop: 0 }}>
        <div className="cta-band">
          <div>
            <h2>Start with what you know. Add the rest later.</h2>
            <p>
              You do not need every reference number to begin. Unknown details stay marked
              as unknown.
            </p>
          </div>
          <div className="hero-actions" style={{ margin: 0 }}>
            <Link to="/register" className="button button-primary button-large">
              Create your case file
            </Link>
            <Link to="/login" className="button button-large" style={{ background: "transparent", color: "#fff", borderColor: "rgba(255,255,255,0.3)" }}>
              Sign in
            </Link>
          </div>
        </div>
        <p className="small muted" style={{ marginTop: "1rem", maxWidth: "48rem" }}>
          FINTRACE is a hackathon prototype. It does not contact your bank, police or any
          government portal, and it cannot recover money. Regulatory content that has not
          been verified is labelled as demonstration data.
        </p>
      </section>
    </>
  );
}
