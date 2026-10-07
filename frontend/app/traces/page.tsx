import WorkspacePage from "../../components/WorkspacePage";
import TelemetryExplorer from "../../components/TelemetryExplorer";

export default function TracesPage() {
  return <WorkspacePage section="Traces" title="Request traces" description="Follow API requests through the support workflow and open a trace to inspect its spans.">
    <TelemetryExplorer endpoint="/api/traces" emptyMessage="No traces recorded yet. A trace is created for every API request." />
  </WorkspacePage>;
}