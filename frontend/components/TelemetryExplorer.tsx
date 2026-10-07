"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";

type Row = Record<string, unknown>;

export default function TelemetryExplorer({ endpoint, emptyMessage }: { endpoint: string; emptyMessage: string }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const pageSize = 25;

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
    if (search.trim()) params.set("search", search.trim());
    setBusy(true);
    fetch(`${endpoint}?${params}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Request failed (${response.status})`);
        return response.json();
      })
      .then((payload) => setRows(payload.items ?? []))
      .catch((caught: unknown) => {
        if (caught instanceof Error && caught.name !== "AbortError") setError(caught.message);
      })
      .finally(() => setBusy(false));
    return () => controller.abort();
  }, [endpoint, offset, search]);

  const columns = rows.length ? Object.keys(rows[0]).filter((key) => !["metadata", "output", "input"].includes(key)).slice(0, 8) : [];

  return <section className="telemetry-panel">
    <div className="explorer-toolbar"><label className="explorer-search"><Search size={15} /><input aria-label="Search records" placeholder="Search records" value={search} onChange={(event) => { setOffset(0); setSearch(event.target.value); }} /></label><span className="data-source">Live SQLite data</span></div>
    {busy ? <div className="table-empty">Loading records…</div> : error ? <div className="table-empty error-note">Observability API unavailable: {error}</div> : rows.length === 0 ? <div className="table-empty">{emptyMessage}</div> : <div className="table-scroll"><table className="data-table"><thead><tr>{columns.map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={String(row.id ?? row.trace_id ?? row.request_id ?? index)}>{columns.map((column) => <td key={column}>
      {column === "trace_id" && typeof row[column] === "string" ? <Link className="text-link" href={`/traces/${row[column]}`}>{String(row[column]).slice(0, 12)}…</Link> : column === "metadata" && typeof row[column] === "string" ? <details><summary>View data</summary><pre>{JSON.stringify(JSON.parse(row[column] as string), null, 2)}</pre></details> : String(row[column] ?? "—")}
    </td>)}</tr>)}</tbody></table></div>}
    <footer className="explorer-footer"><span>Showing {rows.length ? offset + 1 : 0}–{offset + rows.length}</span><div><button className="pager-button" aria-label="Previous page" disabled={offset === 0 || busy} onClick={() => setOffset(Math.max(0, offset - pageSize))}><ChevronLeft size={16} /></button><button className="pager-button" aria-label="Next page" disabled={rows.length < pageSize || busy} onClick={() => setOffset(offset + pageSize)}><ChevronRight size={16} /></button></div></footer>
  </section>;
}