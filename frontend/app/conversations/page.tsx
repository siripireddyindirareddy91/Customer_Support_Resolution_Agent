import Link from "next/link";
import { MessagesSquare } from "lucide-react";
import WorkspacePage from "../../components/WorkspacePage";

export default function ConversationsPage() {
  return <WorkspacePage section="Conversations" title="Conversations" description="Customer support conversation history.">
    <section className="empty-state"><div className="empty-icon"><MessagesSquare size={22} /></div><h2>Conversation history is not persisted</h2><p>Live requests are traced and measured, but customer messages are not saved as conversation records in this increment.</p><Link className="text-link" href="/traces">View request traces</Link></section>
  </WorkspacePage>;
}