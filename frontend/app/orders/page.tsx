import Link from "next/link";
import { ArrowRight, Box, Truck } from "lucide-react";
import WorkspacePage from "../../components/WorkspacePage";

const orders = [
  { id: "ORD-1001", item: "Everyday Backpack", date: "October 02, 2026", total: "$64.00", status: "In transit", eta: "Estimated October 08" },
  { id: "ORD-1002", item: "Ceramic Travel Mug · 2", date: "September 27, 2026", total: "$45.00", status: "Delivered", eta: "Delivered September 29" },
];

export default function OrdersPage() {
  return <WorkspacePage section="Orders" title="Your orders" description="Track the latest status and delivery details for your purchases.">
    <div className="workspace-list">{orders.map((order) => <article className="workspace-order" key={order.id}>
      <div className="workspace-order-icon"><Box size={19} /></div>
      <div className="workspace-order-info"><div className="order-name">{order.item}</div><div className="order-id">{order.id} · Placed {order.date}</div><div className="workspace-order-eta"><Truck size={14} />{order.eta}</div></div>
      <div className="workspace-order-side"><span className="status-pill"><span className="status-dot" />{order.status}</span><span className="order-total">{order.total}</span><Link href="/chat" className="text-link">Get help <ArrowRight size={13} /></Link></div>
    </article>)}</div>
  </WorkspacePage>;
}