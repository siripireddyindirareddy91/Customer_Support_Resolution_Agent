import WorkspacePage from "../../components/WorkspacePage";
import TelemetryExplorer from "../../components/TelemetryExplorer";

export default function LogsPage() {
  return <WorkspacePage section="Logs" title="Application logs" description="Search structured events recorded by the running support API.">
    <TelemetryExplorer endpoint="/api/logs" emptyMessage="No API events recorded yet. Send a support request to populate this view." />
  </WorkspacePage>;
}