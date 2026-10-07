import { Settings, ShieldCheck } from "lucide-react";
import WorkspacePage from "../../components/WorkspacePage";

export default function SettingsPage() {
  return <WorkspacePage section="Settings" title="Account settings" description="Your customer profile and support preferences.">
    <div className="settings-list">
      <section className="settings-row"><div className="settings-icon"><Settings size={18} /></div><div><h2>Customer profile</h2><p>Jordan Miller</p><span>Demo customer account · CUS-1001</span></div><span className="settings-readonly">Read only</span></section>
      <section className="settings-row"><div className="settings-icon"><ShieldCheck size={18} /></div><div><h2>Privacy and security</h2><p>Your order information is checked against your signed-in customer identity.</p><span>Demo authentication is enabled for local development.</span></div><span className="settings-readonly">Protected</span></section>
    </div>
  </WorkspacePage>;
}