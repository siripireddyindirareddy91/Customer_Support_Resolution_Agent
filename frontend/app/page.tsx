import Link from "next/link";
import { ArrowRight, Bell, CircleHelp } from "lucide-react";
import Sidebar from "../components/Sidebar";
import MetricsSummary from "../components/MetricsSummary";

const orders = [
  { name: "Everyday Backpack", id: "ORD-1001", date: "Placed Oct 02", status: "In transit" },
  { name: "Ceramic Travel Mug · 2", id: "ORD-1002", date: "Placed Sep 27", status: "Delivered" },
];

export default function HomePage() {
  return <div className="shell"><Sidebar /><main className="main">
    <div className="topbar"><div className="eyebrow">Customer space / Overview</div><div className="top-actions"><button className="icon-button" aria-label="Notifications"><Bell size={16} /></button><div className="avatar">JM</div></div></div>
    <section className="intro-row"><div><div className="eyebrow">Wednesday, October 7</div><h1>Good morning, Jordan.</h1><p className="lead">Your deliveries, all in one place.</p></div><Link className="primary-link" href="/chat">Ask for help <ArrowRight size={16} /></Link></section>
    <MetricsSummary />
    <div className="content-grid">
      <section id="orders"><div className="section-head"><h2>Recent orders</h2><Link className="text-link" href="/orders">View all</Link></div><div className="order-list">{orders.map((order) => <article className="order-row" key={order.id}><div><div className="order-name">{order.name}</div><div className="order-id">{order.id}</div></div><div className="order-date">{order.date}</div><div className="status-pill"><span className="status-dot" />{order.status}</div></article>)}</div></section>
      <aside className="support-card"><div className="card-icon"><CircleHelp size={19} /></div><h3>Need a hand?</h3><p>Get a clear answer about an order, delivery, or support policy. We’ll check the details before suggesting next steps.</p><Link className="subtle-link" href="/chat">Start a conversation <ArrowRight size={14} /></Link></aside>
    </div>
  </main></div>;
}