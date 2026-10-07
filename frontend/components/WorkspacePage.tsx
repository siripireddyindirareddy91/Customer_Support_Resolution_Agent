import type { ReactNode } from "react";
import Sidebar from "./Sidebar";

type Props = { section: string; title: string; description: string; children: ReactNode };

export default function WorkspacePage({ section, title, description, children }: Props) {
  return <div className="shell"><Sidebar /><main className="main">
    <div className="topbar"><div className="eyebrow">Customer space / {section}</div><div className="avatar">JM</div></div>
    <section className="intro-row"><div><div className="eyebrow">Workspace</div><h1>{title}</h1><p className="lead">{description}</p></div></section>
    {children}
  </main></div>;
}