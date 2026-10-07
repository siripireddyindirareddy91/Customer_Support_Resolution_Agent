import WorkspacePage from "../../components/WorkspacePage";
import MetricsSummary from "../../components/MetricsSummary";
import TelemetryExplorer from "../../components/TelemetryExplorer";

export default function MetricsPage() {
  return <WorkspacePage section="Metrics" title="Request metrics" description="Measured request volume, success, and latency from SQLite telemetry.">
    <MetricsSummary />
    <div className="section-head telemetry-heading"><h2>Recent requests</h2></div>
    <TelemetryExplorer endpoint="/api/metrics/requests" emptyMessage="No requests recorded yet." />
  </WorkspacePage>;
}