import { useEffect, useState } from "react";

import { Card, EmptyState, ErrorBanner, Loading } from "../ui";
import { formatDateTime } from "../../constants";
import { api } from "../../services/api";

export default function AuditTab({ caseId }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    api
      .caseAudit(caseId)
      .then((items) => active && setEvents(items))
      .catch((problem) => active && setError(problem))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [caseId]);

  if (loading) {
    return <Loading label="Loading audit trail…" />;
  }

  return (
    <div className="stack">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <Card
        title="Audit trail"
        subtitle="Append-only. Records cannot be edited or deleted by any user."
      >
        {events.length === 0 ? (
          <EmptyState title="No events recorded" />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>Actor role</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td>{formatDateTime(event.created_at)}</td>
                    <td className="mono">{event.action}</td>
                    <td className="muted small">
                      {event.entity_type || "—"}
                      {event.entity_id ? ` · ${event.entity_id.slice(0, 8)}` : ""}
                    </td>
                    <td>{event.actor_role || "system"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
