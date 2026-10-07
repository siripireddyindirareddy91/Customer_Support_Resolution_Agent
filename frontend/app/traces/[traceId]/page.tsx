"use client";

import { useParams } from "next/navigation";
import WorkspacePage from "../../../components/WorkspacePage";
import TraceDetail from "../../../components/TraceDetail";

export default function TracePage() {
  const params = useParams<{ traceId: string }>();
  return <WorkspacePage section="Trace detail" title="Trace waterfall" description={`Correlated API, LangGraph, and log events for ${params.traceId}`}>
    <TraceDetail traceId={params.traceId} />
  </WorkspacePage>;
}