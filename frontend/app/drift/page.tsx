import { Activity } from "lucide-react";
import WorkspacePage from "../../components/WorkspacePage";

export default function DriftPage() {
  return <WorkspacePage section="Drift" title="Drift monitoring" description="Model and retrieval drift need labeled baselines before scores are meaningful.">
    <section className="empty-state"><div className="empty-icon"><Activity size={22} /></div><h2>No drift baseline configured</h2><p>This environment has not collected labeled outcomes or configured a baseline distribution. Drift status is withheld rather than estimated from fabricated values.</p><div className="status-pill status-warning"><span className="status-dot" />Not evaluated</div></section>
  </WorkspacePage>;
}