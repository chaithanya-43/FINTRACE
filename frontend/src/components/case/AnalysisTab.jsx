import { useState } from "react";

import { Card, ErrorBanner, Notice } from "../ui";
import { api } from "../../services/api";

export default function AnalysisTab({ caseId }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAnalyse() {
    setLoading(true);
    setError(null);
    try {
      setResult(await api.analyze(caseId));
    } catch (problem) {
      setError(problem);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <Notice>
        Analysis runs a deterministic keyword pass over your written description. No
        external AI provider is configured, and nothing here is a legal or regulatory
        decision.
      </Notice>

      <Card
        title="Incident analysis"
        subtitle="Structured extraction, missing-information review and next steps."
        actions={
          <button type="button" className="button button-primary" onClick={handleAnalyse} disabled={loading}>
            {loading ? "Analysing…" : "Analyse this case"}
          </button>
        }
      >
        {!result && (
          <p className="muted">
            Run the analysis to see suggested classification, extracted facts and what is
            still missing.
          </p>
        )}

        {result && (
          <div className="stack">
            <p className="prose">{result.summary}</p>

            <div className="kv-row">
              <div>
                <span className="kv-label">Suggested type</span>
                <span className="kv-value">{result.suggested_incident_type.replaceAll("_", " ")}</span>
              </div>
              <div>
                <span className="kv-label">Suggested channel</span>
                <span className="kv-value">{result.suggested_fraud_channel.replaceAll("_", " ")}</span>
              </div>
              <div>
                <span className="kv-label">Engine</span>
                <span className="kv-value mono">{result.engine}</span>
              </div>
            </div>
            <p className="muted small">{result.confidence_note}</p>

            <div className="grid-two">
              <div>
                <h3 className="subhead">Missing information</h3>
                {result.missing_information.length === 0 ? (
                  <p className="muted">Nothing obviously missing from the record.</p>
                ) : (
                  <ul className="plain-list">
                    {result.missing_information.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <h3 className="subhead">Suggested next steps</h3>
                <ul className="plain-list">
                  {result.suggested_next_steps.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div>
              <h3 className="subhead">Extracted facts</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Fact</th>
                      <th>Value</th>
                      <th>Provenance</th>
                      <th>Confirmed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.extracted_facts.map((fact, index) => (
                      <tr key={`${fact.fact}-${index}`}>
                        <td>{fact.fact.replaceAll("_", " ")}</td>
                        <td className="mono">
                          {typeof fact.value === "object"
                            ? JSON.stringify(fact.value)
                            : String(fact.value)}
                        </td>
                        <td className="muted small">{fact.provenance.replaceAll("_", " ")}</td>
                        <td>{fact.confirmed ? "Yes" : "Not yet"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
