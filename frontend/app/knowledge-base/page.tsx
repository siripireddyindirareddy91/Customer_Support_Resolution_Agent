import WorkspacePage from "../../components/WorkspacePage";
import TelemetryExplorer from "../../components/TelemetryExplorer";

export default function KnowledgeBasePage() {
  return <WorkspacePage section="Knowledge Base" title="Knowledge base" description="Local policy sources available to the support workflow.">
    <TelemetryExplorer endpoint="/api/knowledge-base" emptyMessage="No policy documents found." />
  </WorkspacePage>;
}