"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, AlertTriangle, BarChart3, BookOpen, Box, CircleHelp, ClipboardList, GitBranch, MessagesSquare, PackageCheck, ScrollText, Settings, Users } from "lucide-react";

const groups = [
  { label: "Support", links: [
    { label: "Overview", href: "/", icon: PackageCheck },
    { label: "Customers", href: "/customers", icon: Users },
    { label: "Conversations", href: "/conversations", icon: MessagesSquare },
    { label: "Support chat", href: "/chat", icon: CircleHelp },
    { label: "Orders", href: "/orders", icon: Box },
    { label: "Tickets", href: "/tickets", icon: ClipboardList },
    { label: "Knowledge Base", href: "/knowledge-base", icon: BookOpen },
  ] },
  { label: "Operations", links: [
    { label: "Logs", href: "/logs", icon: ScrollText },
    { label: "Metrics", href: "/metrics", icon: BarChart3 },
    { label: "Traces", href: "/traces", icon: GitBranch },
    { label: "Drift", href: "/drift", icon: Activity },
    { label: "Alerts", href: "/alerts", icon: AlertTriangle },
    { label: "Settings", href: "/settings", icon: Settings },
  ] },
];

export default function Sidebar() {
  const pathname = usePathname();

  return <aside className="sidebar">
    <Link className="brand" href="/"><span className="brand-mark"><Box size={17} /></span><span className="brand-name">parcelcare</span></Link>
    <nav className="nav" aria-label="Main navigation">
      {groups.map((group) => <div className="nav-group" key={group.label}>
        <div className="side-label">{group.label}</div>
        {group.links.map(({ label, href, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return <Link className={`nav-link${active ? " active" : ""}`} href={href} key={href} aria-current={active ? "page" : undefined} title={label}>
            <Icon size={17} /><span className="nav-text">{label}</span>
          </Link>;
        })}
      </div>)}
    </nav>
    <div className="sidebar-bottom"><div className="side-label">Signed in as</div><div className="demo-user"><div className="avatar">JM</div><div><strong>Jordan Miller</strong><span>Customer account</span></div></div></div>
  </aside>;
}