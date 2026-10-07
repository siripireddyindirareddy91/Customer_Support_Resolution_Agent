"use client";

import { FormEvent, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowUp, Check, CircleHelp, LoaderCircle } from "lucide-react";
import { ChatResult, sendMessage } from "../../services/api";
import Sidebar from "../../components/Sidebar";

type Message = { role: "assistant" | "user"; content: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", content: "Hi Jordan. I can help with an order, delivery, or support policy. What can I look into for you?" }]);
  const [result, setResult] = useState<ChatResult | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const feedRef = useRef<HTMLDivElement>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || busy) return;
    setDraft("");
    setError("");
    setMessages((current) => [...current, { role: "user", content: message }]);
    setBusy(true);
    try {
      const reply = await sendMessage(message);
      setResult(reply);
      setMessages((current) => [...current, { role: "assistant", content: reply.response }]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Support is temporarily unavailable.");
    } finally {
      setBusy(false);
      requestAnimationFrame(() => feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: "smooth" }));
    }
  }

  return <div className="shell"><Sidebar />
    <main className="main"><div className="topbar"><Link href="/" className="subtle-link"><ArrowLeft size={15} /> Back to overview</Link><div className="eyebrow">Support / New conversation</div></div>
      <div className="intro-row"><div><div className="eyebrow">Here to help</div><h1>Let’s sort it out.</h1><p className="lead">Tell us what happened and we’ll check your order and relevant policy.</p></div></div>
      <section className="chat-layout" aria-label="Support conversation"><div className="chat-main"><header className="chat-header"><div className="agent-avatar"><CircleHelp size={18} /></div><div><strong>Parcelcare support</strong><small>{busy ? "Checking your details…" : "Online · Order support"}</small></div></header>
        <div className="chat-feed" ref={feedRef} aria-live="polite">{messages.map((message, index) => <div className={`message ${message.role === "user" ? "user" : ""}`} key={`${index}-${message.role}`}>{message.content}<div className="message-time">{message.role === "assistant" ? "Parcelcare support" : "You"}</div></div>)}{busy && <div className="message"><LoaderCircle size={15} className="activity-check" /> Checking your order and support guidance…</div>}{error && <p className="error-note">{error}</p>}</div>
        <form className="chat-form" onSubmit={submit}><textarea aria-label="Your message" placeholder="Type your message…" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} /><button className="send-button" type="submit" aria-label="Send message" disabled={busy || !draft.trim()}><ArrowUp size={17} /></button></form>
      </div><aside className="chat-context"><div className="context-label">Resolution details</div><div className="context-box"><strong>{result?.order ? `Order ${String(result.order.id)}` : "Order details"}</strong>{result?.order ? <><p>{String(result.order.status)} · ${String(result.order.total)}</p><p>{result.delivery ? `${String(result.delivery.carrier)} · ${String(result.delivery.status).replaceAll("_", " ")}` : "No delivery record returned"}</p>{result.delivery?.estimated_delivery && <p>Estimated {String(result.delivery.estimated_delivery)}</p>}</> : <p>Share an order number to see verified order and delivery information.</p>}</div>
        <div className="context-label">Support status</div><div className="context-box"><strong>{result?.resolution?.status ? String(result.resolution.status).replaceAll("_", " ") : "Waiting for your message"}</strong>{result?.intent && <p>Request type: {result.intent.toLowerCase().replaceAll("_", " ")}</p>}{result?.escalation && <p>Escalated to a support specialist</p>}</div>
        <div className="context-label">Progress</div><ul className="activity-list">{(result?.activity ?? ["Understanding your request", "Checking verified order details", "Reviewing relevant guidance", "Validating next steps"]).map((step, index) => <li key={`${step}-${index}`}><Check size={13} className="activity-check" />{step}</li>)}</ul>
        {result?.citations?.length ? <div className="context-box" style={{ marginTop: 19 }}><div className="context-label">Policy source</div>{result.citations.map((citation) => <p key={citation.source}>{citation.source}</p>)}</div> : null}</aside></section>
    </main></div>;
}