import { Activity, Clock3 } from "lucide-react";
import WorkspacePage from "../../components/WorkspacePage";

export default function ActivityPage() {
  return <WorkspacePage section="Activity" title="Recent activity" description="A view of your recent delivery and support updates.">
    <section className="empty-state"><div className="empty-icon"><Activity size={22} /></div><h2>Activity will appear here</h2><p>Delivery updates are available from each order. Support activity is kept for the current conversation and is not yet saved as account history.</p><div className="activity-note"><Clock3 size={15} /> History appears as updates are recorded</div></section>
  </WorkspacePage>;
}