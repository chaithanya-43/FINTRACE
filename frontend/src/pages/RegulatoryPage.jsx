import { useCallback, useEffect, useState } from "react";

import { Badge, Card, ErrorBanner, Loading, Notice } from "../components/ui";
import { CaseGate, CasePicker, useCaseSelection } from "../components/CaseSelector";
import RegulatoryTab from "../components/case/RegulatoryTab";
import { formatDate } from "../constants";
import { api } from "../services/api";

export default function RegulatoryPage() {
  const { cases, selectedId, setSelectedId, selectedCase, loading, error } =
    useCaseSelection();
  const [rules, setRules] = useState([]);
  const [rulesLoading, setRulesLoading] = useState(true);
  const [rulesError, setRulesError] = useState(null);

  const loadRules = useCallback(async () => {
    setRules(await api.listRules());
  }, []);

  useEffect(() => {
    let active = true;
    loadRules()
      .catch((problem) => active && setRulesError(problem))
      .finally(() => active && setRulesLoading(false));
    return () => {
      active = false;
    };
  }, [loadRules]);

  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Intelligence</p>
          <h1>Regulatory intelligence</h1>
          <p>
            Versioned rules, deterministic evaluation and a permanent assessment history
            for each case.
          </p>
        </div>
      </div>

      <div className="demo-banner">
        <span aria-hidden="true">◆</span>
        <span>
          <strong>Demonstration data.</strong> The rule set below is seeded example
          content for this hackathon prototype. It has not been verified against primary
          legal sources and is not legal advice. Each rule shows its verification status.
        </span>
      </div>

      <Card
        title="Rule library"
        subtitle="Every version is retained. A rule is only evaluated between its effective dates."
      >
        <ErrorBanner error={rulesError} onDismiss={() => setRulesError(null)} />
        {rulesLoading ? (
          <Loading label="Loading rule library…" />
        ) : rules.length === 0 ? (
          <p className="muted small">
            No rules seeded. Run <code>python scripts/seed_regulatory_rules.py</code>.
          </p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Rule</th>
                  <th>Version</th>
                  <th>Authority</th>
                  <th>Effective from</th>
                  <th>Status</th>
                  <th>Source verification</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => (
                  <tr key={rule.id}>
                    <td>
                      <strong>{rule.title}</strong>
                      <div className="small muted mono">{rule.rule_code}</div>
                    </td>
                    <td>v{rule.version}</td>
                    <td>{rule.authority}</td>
                    <td>{formatDate(rule.effective_from)}</td>
                    <td>
                      <Badge value={rule.status} />
                    </td>
                    <td>
                      <Badge value={rule.verification_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <div className="page-heading" style={{ marginTop: "0.4rem" }}>
        <div>
          <h2>Run an assessment for a case</h2>
          <p className="small muted">
            The result is stored with the rule snapshot, input hash and engine version.
          </p>
        </div>
      </div>

      <CaseGate loading={loading} error={error} cases={cases}>
        <CasePicker
          cases={cases}
          selectedId={selectedId}
          onChange={setSelectedId}
          selectedCase={selectedCase}
        />
        {selectedId && <RegulatoryTab key={selectedId} caseId={selectedId} />}
      </CaseGate>

      <Notice tone="warning">
        An assessment applies a stored rule to recorded facts. It does not decide your
        legal position, and FINTRACE cannot submit anything to a regulator.
      </Notice>
    </div>
  );
}
