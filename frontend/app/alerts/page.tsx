import { AlertTriangle } from "lucide-react";
import WorkspacePage from "../../components/WorkspacePage";

export default function AlertsPage() {
  return <WorkspacePage section="Alerts" title="Alerts" description="Operational alerts will appear when threshold rules are configured.">
    <section className="empty-state"><div className="empty-icon"><AlertTriangle size={22} /></div><h2>No alert rules configured</h2><p>Threshold evaluation and notifications are not enabled in this local increment. No healthy status is inferred when alert coverage is absent.</p><div className="status-pill status-warning"><span className="status-dot" />Unconfigured</div></section>
  </WorkspacePage>;
}