import WorkspacePage from "../../components/WorkspacePage";
import TelemetryExplorer from "../../components/TelemetryExplorer";

export default function CustomersPage() {
  return <WorkspacePage section="Customers" title="Customers" description="Seeded local customer identities and their order counts.">
    <TelemetryExplorer endpoint="/api/customers" emptyMessage="No customer records are available." />
  </WorkspacePage>;
}