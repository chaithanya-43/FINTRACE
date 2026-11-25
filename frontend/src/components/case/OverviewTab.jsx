import { Card, Stat } from "../ui";
import { formatDateTime, formatMoney } from "../../constants";

export default function OverviewTab({ caseData, summary }) {
  return (
    <div className="stack">
      <div className="grid-two">
        <Card title="Incident details">
          <dl className="detail-list">
            <div>
              <dt>Case reference</dt>
              <dd className="mono">{caseData.public_reference}</dd>
            </div>
            <div>
              <dt>Occurred</dt>
              <dd>{formatDateTime(caseData.incident_occurred_at)}</dd>
            </div>
            <div>
              <dt>Fraud channel</dt>
              <dd>{caseData.fraud_channel.replaceAll("_", " ")}</dd>
            </div>
            <div>
              <dt>Estimated loss</dt>
              <dd>{formatMoney(caseData.estimated_loss_amount, caseData.currency)}</dd>
            </div>
            <div>
              <dt>Completeness</dt>
              <dd>{caseData.completeness_status}</dd>
            </div>
            <div>
              <dt>Disputed facts</dt>
              <dd>{caseData.is_disputed ? "Marked disputed" : "No"}</dd>
            </div>
          </dl>
        </Card>

        <Card title="Description">
          <p className="prose">{caseData.description || "No description recorded yet."}</p>
          {caseData.reporting_details && (
            <>
              <h3 className="subhead">Reporting so far</h3>
              <p className="prose">{caseData.reporting_details}</p>
            </>
          )}
        </Card>
      </div>

      {summary && (
        <Card title="What is recorded">
          <div className="stat-grid stat-grid-compact">
            <Stat label="Transactions" value={summary.transaction_count} />
            <Stat label="Evidence files" value={summary.evidence_count} />
            <Stat label="Assessments" value={summary.assessment_count} />
            <Stat label="Complaints" value={summary.complaint_count} />
            <Stat label="Open actions" value={summary.open_recovery_actions} />
            <Stat
              label="Transaction total"
              value={formatMoney(summary.total_transaction_amount, caseData.currency)}
            />
          </div>
        </Card>
      )}
    </div>
  );
}
