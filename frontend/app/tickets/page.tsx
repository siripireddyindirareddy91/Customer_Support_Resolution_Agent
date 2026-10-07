import Link from "next/link";
import { ArrowRight, ClipboardList } from "lucide-react";
import WorkspacePage from "../../components/WorkspacePage";

export default function TicketsPage() {
  return <WorkspacePage section="Tickets" title="Support tickets" description="Follow up on requests that need a closer look.">
    <section className="empty-state"><div className="empty-icon"><ClipboardList size={22} /></div><h2>No open tickets</h2><p>When a support request needs follow-up, it will appear here. You can start a conversation about an order at any time.</p><Link className="primary-link" href="/chat">Contact support <ArrowRight size={15} /></Link></section>
  </WorkspacePage>;
}