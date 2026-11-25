import { Link } from "../router";

const FIRST_STEPS = [
  {
    title: "Call 1930 now",
    body: "The national cybercrime helpline can act while the money is still traceable. Note the time and any reference you are given.",
  },
  {
    title: "Tell your bank immediately",
    body: "Use the fraud number on your card or in the bank app — never a number from the suspect conversation. Ask for a freeze or hold.",
  },
  {
    title: "Report on cybercrime.gov.in",
    body: "File the complaint yourself and keep the acknowledgement number. Add it to the complaint tracker afterwards.",
  },
  {
    title: "Preserve the evidence",
    body: "Do not delete messages. Take screenshots of the chat, the caller ID and the bank alert before anything changes.",
  },
];

export default function EmergencyPage() {
  return (
    <div className="stack stack-lg" style={{ maxWidth: 980, margin: "0 auto" }}>
      <div className="roadmap-hero" style={{ background: "linear-gradient(135deg, #7f1d1d, #101c35)" }}>
        <div>
          <span className="hero-urgent" style={{ marginBottom: "0.6rem" }}>
            Emergency
          </span>
          <h2 style={{ fontSize: "1.5rem" }}>If money is still moving, act before anything else</h2>
          <p>
            These are official channels you contact yourself. FINTRACE does not call, file
            or submit anything on your behalf.
          </p>
        </div>
        <div className="roadmap-score">
          <div className="score-label">Cybercrime helpline</div>
          <div className="score-value">
            <a href="tel:1930" style={{ color: "#fff", textDecoration: "none" }}>
              1930
            </a>
          </div>
          <a href="tel:1930" className="button button-danger button-small">
            Call 1930
          </a>
        </div>
      </div>

      <div className="callout-grid">
        <div className="contact-card">
          <div className="contact-name">National cybercrime helpline</div>
          <div className="contact-value emergency">
            <a href="tel:1930">1930</a>
          </div>
          <p className="small muted">Free, 24×7. Report the transaction as soon as possible.</p>
        </div>
        <div className="contact-card">
          <div className="contact-name">Cybercrime reporting portal</div>
          <div className="contact-value" style={{ fontSize: "1rem" }}>
            <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer">
              cybercrime.gov.in
            </a>
          </div>
          <p className="small muted">File the complaint yourself and save the acknowledgement.</p>
        </div>
        <div className="contact-card">
          <div className="contact-name">Your bank’s fraud desk</div>
          <div className="contact-value" style={{ fontSize: "1rem" }}>
            Number on your card
          </div>
          <p className="small muted">Ask for a transaction dispute and a block on further debits.</p>
        </div>
      </div>

      <div className="grid-two">
        <section className="card">
          <h2 style={{ marginBottom: "0.75rem" }}>Do these first</h2>
          <ol className="plain-list numbered">
            {FIRST_STEPS.map((step) => (
              <li key={step.title}>
                <strong>{step.title}</strong>
                <p className="small muted" style={{ marginTop: "0.15rem" }}>
                  {step.body}
                </p>
              </li>
            ))}
          </ol>
        </section>

        <div className="stack">
          <section className="card" style={{ borderColor: "#fecaca" }}>
            <h2 style={{ color: "var(--emergency)", marginBottom: "0.6rem" }}>
              Never do this
            </h2>
            <ul className="plain-list">
              <li>Never share an OTP, UPI PIN, CVV or banking password — not even to “recover” money.</li>
              <li>Do not install a screen-sharing or remote-access app at a caller’s request.</li>
              <li>Do not pay a “recovery agent” or “cyber officer” who contacts you first.</li>
              <li>Do not edit or delete the original messages and screenshots.</li>
            </ul>
          </section>

          <section className="card">
            <h2 style={{ marginBottom: "0.4rem" }}>Then open a case file</h2>
            <p className="small muted" style={{ marginBottom: "0.8rem" }}>
              Record the incident, attach evidence and get a prioritised roadmap for the
              next hours and days.
            </p>
            <Link to="/report" className="button button-primary">
              Start a fraud report
            </Link>
          </section>
        </div>
      </div>

      <div className="alert alert-warning">
        <div>
          <strong>If you are in immediate physical danger, call 112.</strong> FINTRACE is a
          record-keeping and planning tool, not an emergency service.
        </div>
      </div>
    </div>
  );
}
