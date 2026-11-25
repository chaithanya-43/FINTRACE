import { useCallback, useEffect, useState } from "react";

import { Badge, Card, EmptyState, ErrorBanner, Loading, Notice } from "../ui";
import { formatDate } from "../../constants";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../services/api";

export default function RegulatoryTab({ caseId }) {
  const { user } = useAuth();
  const [rules, setRules] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [disclaimer, setDisclaimer] = useState("");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    const [activeRules, history] = await Promise.all([
      api.activeRegulations(caseId),
      api.listAssessments(caseId),
    ]);
    setRules(activeRules);
    setAssessments(history.assessments);
    setDisclaimer(history.disclaimer);
  }, [caseId]);

  useEffect(() => {
    let active = true;
    load()
      .catch((problem) => active && setError(problem))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [load]);

  async function handleRun() {
    setRunning(true);
    setError(null);
    try {
      await api.runAssessment(caseId, {});
      await load();
    } catch (problem) {
      setError(problem);
    } finally {
      setRunning(false);
    }
  }

  async function handleReview(assessmentId, reviewStatus) {
    setError(null);
    try {
      await api.reviewAssessment(assessmentId, { review_status: reviewStatus });
      await load();
    } catch (problem) {
      setError(problem);
    }
  }

  if (loading) {
    return <Loading label="Loading regulatory rules…" />;
  }

  return (
    <div className="stack">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      <Notice tone="warning">{disclaimer}</Notice>

      <Card
        title="Rules in force for this case"
        subtitle="Only active, dated rules are evaluated. Every result cites the stored version."
        actions={
          <button
            type="button"
            className="button button-primary"
            onClick={handleRun}
            disabled={running || rules.length === 0}
          >
            {running ? "Assessing…" : "Run assessment"}
          </button>
        }
      >
        {rules.length === 0 ? (
          <EmptyState title="No active rules">
            Seed rules with <code>python scripts/seed_regulatory_rules.py</code> before
            running an assessment.
          </EmptyState>
        ) : (
          <ul className="plain-list">
            {rules.map((rule) => (
              <li key={rule.id}>
                <strong>{rule.title}</strong>{" "}
                <span className="muted small">
                  v{rule.version} · {rule.authority} · effective {formatDate(rule.effective_from)}
                </span>{" "}
                <Badge value={rule.verification_status} />
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="Assessment history" subtitle="Every run is kept; nothing is overwritten.">
        {assessments.length === 0 ? (
          <EmptyState title="No assessments yet">
            Run an assessment once transactions and evidence are recorded.
          </EmptyState>
        ) : (
          <div className="stack">
            {assessments.map((item) => (
              <article key={item.id} className="assessment">
                <header className="assessment-head">
                  <div>
                    <h3>{item.rule_title}</h3>
                    <p className="muted small">
                      <span className="mono">
                        {item.rule_code} v{item.rule_version}
                      </span>{" "}
                      · assessed {formatDate(item.assessed_at)} · applicable on{" "}
                      {formatDate(item.applicable_on_date)}
                    </p>
                  </div>
                  <div className="assessment-badges">
                    <Badge value={item.result_status} />
                    <Badge value={item.rule_verification_status} />
                    {item.review_status !== "unreviewed" && (
                      <Badge value={item.review_status} />
                    )}
                  </div>
                </header>

                <p className="prose">{item.explanation}</p>

                <dl className="detail-list detail-list-inline">
                  <div>
                    <dt>Authority</dt>
                    <dd>{item.rule_authority}</dd>
                  </div>
                  <div>
                    <dt>Source</dt>
                    <dd>
                      {item.rule_source_url ? (
                        <a href={item.rule_source_url} target="_blank" rel="noreferrer">
                          {item.rule_source_reference}
                        </a>
                      ) : (
                        item.rule_source_reference
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Input hash</dt>
                    <dd className="mono small">{item.input_snapshot_hash}</dd>
                  </div>
                </dl>

                {item.rule_verification_status === "unverified" && (
                  <p className="muted small">
                    This rule&rsquo;s source has not been verified. Treat the result as an
                    exercise, not as a claim about the law.
                  </p>
                )}

                {user?.role !== "citizen" && (
                  <div className="form-actions">
                    <button
                      type="button"
                      className="button button-small"
                      onClick={() => handleReview(item.id, "confirmed")}
                    >
                      Mark reviewed as accurate
                    </button>
                    <button
                      type="button"
                      className="button button-small button-ghost"
                      onClick={() => handleReview(item.id, "disputed")}
                    >
                      Mark disputed
                    </button>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
