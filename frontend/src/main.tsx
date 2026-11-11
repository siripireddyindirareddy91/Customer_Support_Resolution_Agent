import { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BookOpen,
  Box,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Clock,
  FlaskConical,
  GitBranch,
  History,
  LayoutDashboard,
  Menu,
  Moon,
  Plus,
  Settings,
  ShieldCheck,
  Sun,
  Truck,
  TriangleAlert,
  Workflow,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./style.css";

type Row = Record<string, any>;
const pages = [
  ["Overview", LayoutDashboard],
  ["Live Investigations", Activity],
  ["New Investigation", Plus],
  ["Agent Workflow", Workflow],
  ["Order Intelligence", Box],
  ["Shipment Tracking", Truck],
  ["Policy Knowledge Base", BookOpen],
  ["Resolution Center", CheckCircle2],
  ["Human Review Queue", ClipboardCheck],
  ["Evaluation Lab", FlaskConical],
  ["Analytics & Reports", BarChart3],
  ["Audit Trail", History],
  ["Settings", Settings],
] as const;
const slug = (title: string) =>
  title
    .toLowerCase()
    .replace(/[^a-z ]/g, "")
    .trim()
    .replace(/ +/g, "-");
const stages = [
  "Order Lookup",
  "Delivery Classification",
  "Policy Retrieval",
  "Resolution & Handoff",
];
const initialPage = () =>
  pages.find(([name]) => slug(name) === location.hash.slice(1))?.[0] ||
  "Overview";

async function api(
  path: string,
  token = "",
  data?: object,
  method = data === undefined ? "GET" : "POST",
) {
  const response = await fetch("/api/v1/" + path, {
    method,
    headers: {
      ...(token ? { Authorization: "Bearer " + token } : {}),
      ...(data === undefined || data instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
    },
    body:
      data === undefined
        ? undefined
        : data instanceof FormData
          ? data
          : JSON.stringify(data),
  });
  const result = await response.json().catch(() => null);
  if (!response.ok || result === null)
    throw new Error(
      typeof result?.detail === "string"
        ? result.detail
        : "The request could not be completed. Try again.",
    );
  return result;
}

function App() {
  const [token, setToken] = useState(
    sessionStorage.getItem("resolveflow") || "",
  );
  const [user, setUser] = useState<Row>();
  const [page, setPage] = useState<string>(initialPage);
  const [items, setItems] = useState<Row[]>([]);
  const [rows, setRows] = useState<Row[]>([]);
  const [metrics, setMetrics] = useState<Row>({});
  const [selected, setSelected] = useState<Row>();
  const [order, setOrder] = useState<Row>();
  const [timeline, setTimeline] = useState<Row[]>([]);
  const [matches, setMatches] = useState<Row[]>();
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [register, setRegister] = useState(false);
  const [filter, setFilter] = useState("");
  const [date, setDate] = useState("");
  const [reportFilters, setReportFilters] = useState({
    start: "",
    end: "",
    issue: "",
    severity: "",
    status: "",
    agent: "",
  });
  const [mobile, setMobile] = useState(false);
  const [light, setLight] = useState(localStorage.getItem("theme") === "light");
  const [revision, setRevision] = useState(0);
  const [lastEvaluation, setLastEvaluation] = useState<Row>();
  const [report, setReport] = useState<Row>();
  const [notes, setNotes] = useState("");
  const [reviewEvents, setReviewEvents] = useState<Row[]>([]);
  const [draft, setDraft] = useState<{ id: string; value: string }>();
  const navigate = (name: string, status = "") => {
    location.hash = slug(name);
    setPage(name);
    setFilter(status);
    setMobile(false);
  };
  const signOut = () => {
    sessionStorage.removeItem("resolveflow");
    setToken("");
    setUser(undefined);
    setItems([]);
    setRows([]);
    setSelected(undefined);
    setMetrics({});
    setOrder(undefined);
    setTimeline([]);
    setMatches(undefined);
    setReport(undefined);
    setLastEvaluation(undefined);
    setNotes("");
    setReviewEvents([]);
    setDraft(undefined);
    setNotice("");
  };
  useEffect(() => {
    const update = () => setPage(initialPage());
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = light ? "light" : "dark";
    localStorage.setItem("theme", light ? "light" : "dark");
  }, [light]);
  useEffect(() => {
    if (!token) return;
    let active = true;
    api("auth/me", token)
      .then((value) => {
        if (active) setUser(value);
      })
      .catch((error) => {
        if (active) {
          signOut();
          setNotice(error.message);
        }
      });
    return () => {
      active = false;
    };
  }, [token]);
  useEffect(() => {
    if (!token) return;
    let active = true;
    const paths: Record<string, string> = {
      "Order Intelligence": "orders",
      "Shipment Tracking": "orders",
      "Policy Knowledge Base": "policies",
      "Resolution Center": "resolutions",
      "Human Review Queue": "approvals",
      "Audit Trail": "audit-events",
      "Evaluation Lab": "evaluations/results",
    };
    setRows([]);
    setLoading(true);
    const analyticsQuery =
      page === "Analytics & Reports"
        ? new URLSearchParams(
            Object.entries(reportFilters).filter(([, value]) => value),
          ).toString()
        : "";
    Promise.all([
      api("investigations", token),
      api(
        "analytics/overview" + (analyticsQuery ? "?" + analyticsQuery : ""),
        token,
      ),
      paths[page] ? api(paths[page], token) : Promise.resolve([]),
    ])
      .then(([investigations, stats, records]) => {
        if (active) {
          setItems(investigations);
          setMetrics(stats);
          setRows(records);
        }
      })
      .catch((error) => {
        if (active) setNotice(error.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [token, page, revision, reportFilters]);

  async function action(operation: () => Promise<void>) {
    setBusy(true);
    setNotice("");
    try {
      await operation();
    } catch (error) {
      setNotice(
        error instanceof Error ? error.message : "Something went wrong.",
      );
    } finally {
      setBusy(false);
    }
  }
  function auth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = Object.fromEntries(new FormData(event.currentTarget));
    void action(async () => {
      const result = await api(
        "auth/" + (register ? "register" : "login"),
        "",
        form,
      );
      sessionStorage.setItem("resolveflow", result.token);
      setToken(result.token);
    });
  }
  async function run(identifier: string) {
    const polling = window.setInterval(() => {
      void api("investigations/" + identifier, token)
        .then((value) =>
          setSelected((current) =>
            current?.id === identifier &&
            ["Queued", "Running"].includes(current.status)
              ? value
              : current,
          ),
        )
        .catch(() => {});
    }, 350);
    try {
      setSelected(
        await api("investigations/" + identifier + "/run", token, {}),
      );
    } catch (error) {
      setSelected(await api("investigations/" + identifier, token));
      throw error;
    } finally {
      clearInterval(polling);
      setRevision((current) => current + 1);
    }
  }
  function investigate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    void action(async () => {
      const item = await api("investigations", token, data);
      setSelected(item);
      await run(item.id);
    });
  }
  function show(item: Row) {
    setSelected(item);
    navigate("Agent Workflow");
  }
  function evidence(id: string, context: string) {
    void action(async () => {
      setSelected(
        await api("investigations/" + id + "/evidence", token, { context }),
      );
      await run(id);
    });
  }
  function exportCsv(records: Row[], keys: string[], filename: string) {
    const quote = (value: unknown) => {
      const cell = String(value ?? "");
      return (
        '"' +
        (/^[=+@\-\t\r]/.test(cell) ? "'" : "") +
        cell.replaceAll('"', '""') +
        '"'
      );
    };
    const csv = [
      keys.join(","),
      ...records.map((row) => keys.map((key) => quote(row[key])).join(",")),
    ].join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const visible = items.filter(
    (item) =>
      (!date || item.created_at.slice(0, 10) >= date) &&
      (!filter ||
        (filter === "High risk"
          ? item.classification?.severity === "HIGH"
          : filter === "Recommendations ready"
            ? ["Recommended", "Approved"].includes(item.status)
            : filter === "Awaiting review"
              ? ["Pending review", "Supervisor review"].includes(item.status)
              : item.status === filter)),
  );
  const reportItems = items.filter(
    (item) =>
      (!reportFilters.start ||
        item.created_at.slice(0, 10) >= reportFilters.start) &&
      (!reportFilters.end ||
        item.created_at.slice(0, 10) <= reportFilters.end) &&
      (!reportFilters.issue ||
        item.classification?.issue_type === reportFilters.issue) &&
      (!reportFilters.severity ||
        item.classification?.severity === reportFilters.severity) &&
      (!reportFilters.status || item.status === reportFilters.status) &&
      (!reportFilters.agent ||
        item.trace?.some((stage: Row) => stage.agent === reportFilters.agent)),
  );
  const caseTable = (records: Row[]) => (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Order</th>
            <th>Customer issue</th>
            <th>Classification</th>
            <th>Status</th>
            <th>Opened</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {records.map((item) => (
            <tr key={item.id}>
              <td className="mono">{item.order_id}</td>
              <td className="truncate">{item.complaint}</td>
              <td>
                {human(item.classification?.issue_type || "Unclassified")}
              </td>
              <td>
                <span className="pill">{item.status}</span>
              </td>
              <td>{item.created_at.slice(0, 10)}</td>
              <td>
                <button
                  className="icon"
                  aria-label={"Open " + item.order_id}
                  onClick={() => show(item)}
                >
                  <ChevronRight size={17} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!records.length && (
        <p className="empty">
          {loading
            ? "Loading investigations…"
            : "No investigations match this view."}
        </p>
      )}
    </div>
  );
  const filters = (
    <div className="toolbar">
      <label>
        From{" "}
        <input
          type="date"
          value={date}
          onChange={(event) => setDate(event.target.value)}
        />
      </label>
      <select
        aria-label="Investigation status"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
      >
        {[
          "",
          "Queued",
          "Running",
          "Recommendations ready",
          "Awaiting review",
          "Recommended",
          "Pending review",
          "Supervisor review",
          "Approved",
          "Rejected",
          "Evidence requested",
          "Revision requested",
          "Failed",
          "High risk",
        ].map((value) => (
          <option key={value} value={value}>
            {value || "All statuses"}
          </option>
        ))}
      </select>
    </div>
  );
  const brand = (
    <div className="brand">
      <div className="mark">
        <GitBranch size={22} />
      </div>
      <div>
        ResolveFlow <em>AI</em>
        <small>SUPPORT OPERATIONS</small>
      </div>
    </div>
  );

  if (!token)
    return (
      <main className="auth">
        <section className="auth-intro">
          {brand}
          <div>
            <div className="pill">
              <i /> SYNTHETIC DEMO
            </div>
            <h1>
              Investigate delivery
              <br />
              exceptions with <em>AI.</em>
            </h1>
            <p>
              Connect shipment evidence, support policies, and human review in
              one workspace.
            </p>
          </div>
          <div className="auth-steps">
            {stages.map((stage, index) => (
              <span key={stage}>
                <b>0{index + 1}</b>
                {stage}
              </span>
            ))}
          </div>
        </section>
        <section className="auth-form">
          <form className="panel stack" onSubmit={auth}>
            <h2>
              {register ? "Create your account" : "Sign in to ResolveFlow"}
            </h2>
            <label>
              Email
              <input
                type="email"
                name="email"
                autoComplete="email"
                required
                placeholder="you@example.com"
              />
            </label>
            <label>
              Password
              <input
                type="password"
                name="password"
                autoComplete={register ? "new-password" : "current-password"}
                minLength={10}
                required
                placeholder="At least 10 characters"
              />
            </label>
            {notice && (
              <p className="notice" role="alert">
                {notice}
              </p>
            )}
            <button className="primary" disabled={busy}>
              {busy ? "Please wait…" : register ? "Create account" : "Sign in"}
              <ArrowRight size={16} />
            </button>
            <button
              type="button"
              onClick={() => {
                setRegister(!register);
                setNotice("");
              }}
            >
              {register ? "Back to sign in" : "Create a demo account"}
            </button>
          </form>
        </section>
      </main>
    );

  const dashboard = page === "Overview" || page === "Analytics & Reports";
  const values = [
    ["Total investigations", metrics.total ?? 0, Activity, ""],
    [
      "Recommendations ready",
      metrics.resolved ?? 0,
      CheckCircle2,
      "Recommendations ready",
    ],
    [
      "Pending human review",
      metrics.pending ?? 0,
      ClipboardCheck,
      "Awaiting review",
    ],
    ["High-risk cases", metrics.high_risk ?? 0, TriangleAlert, "High risk"],
    ["Mean agent time", (metrics.average_ms ?? 0) + " ms", Clock, ""],
    [
      "Policy citation coverage",
      (metrics.citation_rate ?? 0) + "%",
      ShieldCheck,
      "",
    ],
  ] as const;
  return (
    <div className="app">
      <aside className={mobile ? "sidebar open" : "sidebar"}>
        {brand}
        <nav aria-label="Workspace">
          {pages.map(([name, Icon]) => (
            <button
              key={name}
              onClick={() => navigate(name)}
              aria-current={page === name ? "page" : undefined}
            >
              <Icon size={17} />
              {name}
            </button>
          ))}
        </nav>
        <div className="profile">
          <div className="avatar">{user?.email[0].toUpperCase() || "S"}</div>
          <div>
            <strong>{user?.email || "Support team"}</strong>
            <small>{human(user?.role || "SUPPORT_AGENT")}</small>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header>
          <div className="breadcrumb">
            <button
              className="icon mobile-toggle"
              aria-label="Toggle navigation"
              onClick={() => setMobile(!mobile)}
            >
              <Menu size={20} />
            </button>
            Workspace <ChevronRight size={14} /> <strong>{page}</strong>
          </div>
          <div className="toolbar">
            <span className="pill demo">
              <i /> Synthetic demo
            </span>
            <button
              className="icon"
              aria-label="Toggle theme"
              onClick={() => setLight(!light)}
            >
              {light ? <Moon size={17} /> : <Sun size={17} />}
            </button>
          </div>
        </header>
        <main className="content">
          {notice && (
            <div className="notice" role="alert">
              {notice}
              <button
                className="icon"
                aria-label="Dismiss notification"
                onClick={() => setNotice("")}
              >
                ×
              </button>
            </div>
          )}
          <div className="page-head">
            <div>
              <h1>
                {page === "Overview"
                  ? "Support Operations Overview"
                  : page === "New Investigation"
                    ? "Start New Investigation"
                    : page}
              </h1>
              {page === "Overview" && (
                <p>
                  Monitor delivery exceptions and manage AI-assisted
                  resolutions.
                </p>
              )}
            </div>
            {page === "Overview" && (
              <button
                className="primary"
                onClick={() => navigate("New Investigation")}
              >
                <Plus size={17} /> New investigation
              </button>
            )}
            {page === "Analytics & Reports" && (
              <button
                onClick={() =>
                  exportCsv(
                    reportItems.map((item) => ({
                      ...item,
                      issue: item.classification?.issue_type,
                      severity: item.classification?.severity,
                    })),
                    [
                      "id",
                      "order_id",
                      "issue",
                      "severity",
                      "status",
                      "priority",
                      "created_at",
                    ],
                    "resolveflow-investigations.csv",
                  )
                }
              >
                Export CSV
              </button>
            )}
          </div>
          {page === "Analytics & Reports" && (
            <section className="panel stack">
              <div className="toolbar wrap">
                {(["start", "end"] as const).map((key) => (
                  <label key={key}>
                    {key === "start" ? "From" : "To"}
                    <input
                      type="date"
                      value={reportFilters[key]}
                      onChange={(event) =>
                        setReportFilters({
                          ...reportFilters,
                          [key]: event.target.value,
                        })
                      }
                    />
                  </label>
                ))}
                {(
                  [
                    [
                      "issue",
                      Array.from(
                        new Set(
                          items
                            .map((item) => item.classification?.issue_type)
                            .filter(Boolean),
                        ),
                      ),
                    ],
                    ["severity", ["LOW", "MEDIUM", "HIGH", "CRITICAL"]],
                    [
                      "status",
                      Array.from(new Set(items.map((item) => item.status))),
                    ],
                    ["agent", [...stages]],
                  ] as const
                ).map(([key, options]) => (
                  <select
                    key={key}
                    aria-label={human(key)}
                    value={reportFilters[key]}
                    onChange={(event) =>
                      setReportFilters({
                        ...reportFilters,
                        [key]: event.target.value,
                      })
                    }
                  >
                    <option value="">
                      All {key === "status" ? "statuses" : key + "s"}
                    </option>
                    {options.map((option) => (
                      <option key={option} value={option}>
                        {human(option)}
                      </option>
                    ))}
                  </select>
                ))}
                <button
                  onClick={() =>
                    setReportFilters({
                      start: "",
                      end: "",
                      issue: "",
                      severity: "",
                      status: "",
                      agent: "",
                    })
                  }
                >
                  Clear filters
                </button>
              </div>
              <div className="toolbar wrap">
                <span className="pill">
                  Approval rate ·{" "}
                  {metrics.approval_rate == null
                    ? "—"
                    : metrics.approval_rate + "%"}
                </span>
                <span className="pill">
                  Escalation rate ·{" "}
                  {metrics.escalation_rate == null
                    ? "—"
                    : metrics.escalation_rate + "%"}
                </span>
              </div>
            </section>
          )}
          {dashboard && (
            <>
              <div className="metrics">
                {values.map(([label, value, Icon, status]) => (
                  <button
                    key={label}
                    className="panel metric"
                    onClick={() => navigate("Live Investigations", status)}
                  >
                    <Icon size={19} />
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </button>
                ))}
              </div>
              <div className="charts">
                <Chart
                  title="Delivery issue distribution"
                  data={metrics.issues}
                  color="#8b5cf6"
                />
                <Chart
                  title="Resolution status"
                  data={metrics.statuses}
                  color="#22d3ee"
                />
                <Chart
                  title="Daily investigation volume"
                  data={metrics.volume}
                  color="#8b5cf6"
                />
                <Chart
                  title="Mean agent time (ms)"
                  data={metrics.agents}
                  color="#22d3ee"
                />
              </div>
              <section className="panel">
                <div className="section-head">
                  <h2>Recent investigations</h2>
                  {page === "Overview" && filters}
                </div>
                {caseTable(
                  (page === "Overview" ? visible : reportItems).slice(0, 10),
                )}
              </section>
            </>
          )}
          {page === "Live Investigations" && (
            <section className="panel">
              <div className="section-head">
                <h2>Investigation records</h2>
                {filters}
              </div>
              {caseTable(visible)}
            </section>
          )}
          {page === "New Investigation" && (
            <div className="split">
              <form className="panel stack" onSubmit={investigate}>
                <label>
                  Order ID
                  <input
                    name="order_id"
                    placeholder="ORD-10452"
                    pattern="ORD-[0-9]+"
                    maxLength={32}
                  />
                </label>
                <label>
                  Customer ID <small>Optional</small>
                  <input
                    name="customer_id"
                    placeholder="C-1000"
                    maxLength={32}
                  />
                </label>
                <label>
                  Customer complaint
                  <textarea
                    name="complaint"
                    minLength={8}
                    maxLength={4000}
                    required
                    placeholder="My package was due yesterday and tracking has not updated."
                  />
                </label>
                <div className="form-row">
                  <label>
                    Issue category
                    <select name="category">
                      {[
                        "Delivery",
                        "Missing package",
                        "Damage",
                        "Tracking conflict",
                        "Other",
                      ].map((name) => (
                        <option key={name}>{name}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Priority
                    <select name="priority">
                      <option>Normal</option>
                      <option>Urgent</option>
                    </select>
                  </label>
                </div>
                <label>
                  Additional context
                  <textarea name="context" maxLength={4000} />
                </label>
                <button className="primary" disabled={busy}>
                  <Workflow size={17} />
                  {busy ? "Investigating…" : "Investigate with AI"}
                </button>
              </form>
              <CaseDetails
                item={selected}
                busy={busy}
                retry={(id) => void action(() => run(id))}
                evidence={evidence}
              />
            </div>
          )}
          {page === "Agent Workflow" && (
            <>
              <div className="toolbar">
                <select
                  aria-label="Select investigation"
                  value={selected?.id || ""}
                  onChange={(event) =>
                    setSelected(
                      items.find((item) => item.id === event.target.value),
                    )
                  }
                >
                  <option value="">Select investigation</option>
                  {items.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.order_id} · {item.status} ·{" "}
                      {item.created_at.slice(0, 10)}
                    </option>
                  ))}
                </select>
              </div>
              <CaseDetails
                item={selected}
                busy={busy}
                retry={(id) => void action(() => run(id))}
                evidence={evidence}
              />
            </>
          )}
          {(page === "Order Intelligence" || page === "Shipment Tracking") && (
            <div className="split">
              <section className="panel">
                <div className="section-head">
                  <h2>Synthetic order records</h2>
                </div>
                <div className="scroll">
                  {rows.map((item) => (
                    <button
                      className="list-row"
                      key={item.order_id}
                      onClick={() =>
                        void action(async () => {
                          const [record, events] = await Promise.all([
                            api("orders/" + item.order_id, token),
                            api("orders/" + item.order_id + "/tracking", token),
                          ]);
                          setOrder(record);
                          setTimeline(events);
                        })
                      }
                    >
                      <span className="mono">{item.order_id}</span>
                      <span>{item.product}</span>
                      <ChevronRight size={16} />
                    </button>
                  ))}
                </div>
              </section>
              <section className="panel stack">
                {order ? (
                  <>
                    <h2>{order.order_id}</h2>
                    <dl>
                      {[
                        "customer_id",
                        "order_date",
                        "product",
                        "payment",
                        "carrier",
                        "shipment_id",
                        "expected",
                        "status",
                      ].map((key) => (
                        <div key={key}>
                          <dt>{human(key)}</dt>
                          <dd>{order[key]}</dd>
                        </div>
                      ))}
                    </dl>
                    <h3>Tracking timeline</h3>
                    {timeline.map((event) => (
                      <div className="timeline" key={event.record_id}>
                        <strong>{event.status}</strong>
                        <small>
                          {event.source} ·{" "}
                          {new Date(event.timestamp).toLocaleString()}
                        </small>
                      </div>
                    ))}
                  </>
                ) : (
                  <p className="empty">
                    Select an order to inspect its shipment and tracking
                    history.
                  </p>
                )}
              </section>
            </div>
          )}
          {page === "Policy Knowledge Base" && (
            <div className="split">
              <section className="panel stack">
                <h2>Indexed documents</h2>
                <form
                  className="stack"
                  onSubmit={(event) => {
                    event.preventDefault();
                    const data = new FormData(event.currentTarget);
                    void action(async () => {
                      await api("policies/upload", token, data);
                      setRevision((value) => value + 1);
                      setNotice("Policy indexed.");
                    });
                  }}
                >
                  <label>
                    Document title
                    <input name="name" maxLength={120} />
                  </label>
                  <label>
                    Version
                    <input name="version" defaultValue="1.0" maxLength={30} />
                  </label>
                  <label>
                    Issue tags{" "}
                    <small>
                      Optional. Use tags such as MAJOR_DELAY or DAMAGED.
                    </small>
                    <input name="tags" maxLength={200} />
                  </label>
                  <label>
                    Policy file
                    <input
                      type="file"
                      name="file"
                      accept=".pdf,.docx,.txt"
                      required
                    />
                  </label>
                  <button disabled={busy}>Upload and index policy</button>
                </form>
                <details>
                  <summary>Add policy manually</summary>
                  <form
                    className="stack manual-policy"
                    onSubmit={(event) => {
                      event.preventDefault();
                      const data = Object.fromEntries(
                        new FormData(event.currentTarget),
                      );
                      void action(async () => {
                        await api("policies", token, data);
                        setRevision((value) => value + 1);
                        setNotice("Policy indexed.");
                      });
                    }}
                  >
                    <label>
                      Title
                      <input name="name" maxLength={120} required />
                    </label>
                    <label>
                      Version
                      <input
                        name="version"
                        defaultValue="1.0"
                        maxLength={30}
                        required
                      />
                    </label>
                    <label>
                      Issue tags
                      <input name="tags" maxLength={200} />
                    </label>
                    <label>
                      Policy text
                      <textarea name="content" maxLength={250000} required />
                    </label>
                    <button disabled={busy}>Save policy</button>
                  </form>
                </details>
                <button
                  disabled={busy}
                  onClick={() =>
                    void action(async () => {
                      const result = await api("policies/reindex", token, {});
                      setNotice(result.status + ".");
                    })
                  }
                >
                  Refresh search index
                </button>
                {rows.map((item) => (
                  <details key={item.id}>
                    <summary>
                      {item.name} · v{item.version}
                    </summary>
                    {item.passage ? (
                      <p>{item.passage}</p>
                    ) : (
                      item.chunks?.map((chunk: Row) => (
                        <article key={chunk.section}>
                          <small>
                            Section {chunk.section} · {chunk.effective_date} ·{" "}
                            {chunk.source}
                          </small>
                          <p>{chunk.passage}</p>
                        </article>
                      ))
                    )}
                  </details>
                ))}
              </section>
              <section className="panel stack">
                <h2>Test policy retrieval</h2>
                <form
                  className="toolbar"
                  onSubmit={(event) => {
                    event.preventDefault();
                    const data = Object.fromEntries(
                      new FormData(event.currentTarget),
                    );
                    void action(async () =>
                      setMatches(await api("policies/search", token, data)),
                    );
                  }}
                >
                  <input
                    name="query"
                    aria-label="Policy search"
                    placeholder="Search policy passages"
                    required
                  />
                  <button className="primary" disabled={busy}>
                    Search
                  </button>
                </form>
                {matches && <Citations matches={matches} />}
              </section>
            </div>
          )}
          {page === "Resolution Center" && (
            <div className="split">
              <section className="panel">
                <div className="section-head">
                  <h2>Resolution records</h2>
                </div>
                {rows.map((item) => (
                  <button
                    key={item.id}
                    className="list-row"
                    onClick={() => {
                      setSelected(item);
                      setDraft({ id: item.id, value: item.resolution.draft });
                    }}
                  >
                    <strong>{item.order_id}</strong>
                    <span>{item.status}</span>
                    <ChevronRight size={16} />
                  </button>
                ))}
                {!rows.length && (
                  <p className="empty">Completed investigations appear here.</p>
                )}
              </section>
              {selected?.resolution &&
                draft &&
                draft.id === selected.id &&
                rows.some((item) => item.id === selected.id) && (
                  <section className="panel stack">
                    <h2>
                      {selected.order_id} · {selected.status}
                    </h2>
                    <strong>{selected.resolution.action}</strong>
                    <p>{selected.complaint}</p>
                    <p>{selected.resolution.reason}</p>
                    <Citations matches={selected.policies} />
                    <label>
                      Customer response draft
                      {selected.resolution.draft_source && (
                        <small>
                          {selected.resolution.draft_source === "llm"
                            ? "Model-generated draft"
                            : selected.resolution.draft_source === "manual"
                              ? "Edited by a support agent"
                              : "Evidence-based template"}
                        </small>
                      )}
                      <textarea
                        value={draft.value}
                        maxLength={4000}
                        onChange={(event) =>
                          setDraft({
                            id: selected.id,
                            value: event.target.value,
                          })
                        }
                      />
                    </label>
                    <div className="toolbar wrap">
                      <button
                        disabled={
                          busy ||
                          draft.value.trim().length < 5 ||
                          ![
                            "Recommended",
                            "Pending review",
                            "Supervisor review",
                            "Approved",
                          ].includes(selected.status)
                        }
                        onClick={() =>
                          void action(async () => {
                            setSelected(
                              await api(
                                "resolutions/" + selected.id,
                                token,
                                { draft: draft.value },
                                "PATCH",
                              ),
                            );
                            setRevision((value) => value + 1);
                            setNotice("Draft saved.");
                          })
                        }
                      >
                        Save draft
                      </button>
                      <button
                        disabled={!draft.value}
                        onClick={() =>
                          void action(async () => {
                            await navigator.clipboard.writeText(draft.value);
                            setNotice("Draft copied.");
                          })
                        }
                      >
                        Copy draft
                      </button>
                      <button onClick={() => show(selected)}>
                        View workflow
                      </button>
                    </div>
                  </section>
                )}
            </div>
          )}
          {page === "Human Review Queue" && (
            <div className="split">
              <section className="panel">
                <div className="section-head">
                  <h2>Pending decisions</h2>
                </div>
                {rows.map((item) => (
                  <button
                    key={item.id}
                    className="list-row"
                    onClick={() => {
                      setSelected(item);
                      setNotes("");
                      setReviewEvents([]);
                      void action(async () =>
                        setReviewEvents(
                          await api(
                            "investigations/" + item.id + "/events",
                            token,
                          ),
                        ),
                      );
                    }}
                  >
                    <strong>{item.order_id}</strong>
                    <span>{item.status}</span>
                    <ChevronRight size={16} />
                  </button>
                ))}
                {!rows.length && (
                  <p className="empty">
                    No investigations are awaiting a decision.
                  </p>
                )}
              </section>
              {selected?.resolution &&
                ["Pending review", "Supervisor review"].includes(
                  selected.status,
                ) && (
                  <section className="panel stack">
                    <h2>{selected.order_id}</h2>
                    <small>
                      {selected.id} · {selected.created_at.slice(0, 10)} ·{" "}
                      {Math.round(selected.resolution.confidence * 100)}%
                      confidence
                    </small>
                    <p>{selected.complaint}</p>
                    <p>{selected.resolution.action}</p>
                    <p>{selected.resolution.reason}</p>
                    <span className="pill">
                      {selected.classification.severity} ·{" "}
                      {human(selected.classification.issue_type)}
                    </span>
                    {!!selected.classification.flags.length && (
                      <p>
                        Risk flags {selected.classification.flags.join(", ")}
                      </p>
                    )}
                    <details>
                      <summary>Evidence</summary>
                      <pre>
                        {JSON.stringify(
                          {
                            order: selected.order,
                            tracking: selected.tracking,
                            carrier: selected.carrier,
                          },
                          null,
                          2,
                        )}
                      </pre>
                    </details>
                    <details>
                      <summary>Audit history</summary>
                      {reviewEvents.map((event) => (
                        <p key={event.id}>
                          {event.type} · {event.actor} ·{" "}
                          {new Date(event.created_at).toLocaleString()}
                        </p>
                      ))}
                    </details>
                    <Citations matches={selected.policies} />
                    {user?.role === "ADMIN" ||
                    (user?.role === "SUPPORT_MANAGER" &&
                      selected.status === "Pending review") ? (
                      <>
                        <label>
                          Decision notes
                          <textarea
                            value={notes}
                            onChange={(event) => setNotes(event.target.value)}
                          />
                        </label>
                        <div className="toolbar wrap">
                          {[
                            ["approve", "Approve"],
                            ["reject", "Reject"],
                            ["request-evidence", "Request evidence"],
                            ["request-revision", "Send for revision"],
                            ...(selected.status === "Pending review"
                              ? [["escalate", "Escalate"]]
                              : []),
                          ].map(([path, label]) => (
                            <button
                              key={path}
                              disabled={busy || notes.trim().length < 3}
                              onClick={() =>
                                void action(async () => {
                                  setSelected(
                                    await api(
                                      "approvals/" + selected.id + "/" + path,
                                      token,
                                      { notes },
                                    ),
                                  );
                                  setRevision((value) => value + 1);
                                  setNotes("");
                                })
                              }
                            >
                              {label}
                            </button>
                          ))}
                        </div>
                      </>
                    ) : (
                      <p className="pill">
                        Support manager authorization required
                      </p>
                    )}
                  </section>
                )}
            </div>
          )}
          {page === "Evaluation Lab" && (
            <section className="panel stack">
              <div className="toolbar wrap">
                <button
                  className="primary"
                  disabled={busy}
                  onClick={() =>
                    void action(async () => {
                      const result = await api("evaluations/run", token, {});
                      setLastEvaluation(result);
                      setReport(result);
                      setRevision((value) => value + 1);
                    })
                  }
                >
                  <FlaskConical size={17} />
                  {busy ? "Evaluating…" : "Run 15 evaluation cases"}
                </button>
                {report && (
                  <button
                    onClick={() =>
                      exportCsv(
                        report.cases,
                        [
                          "order_id",
                          "category",
                          "expected_issue",
                          "actual_issue",
                          "expected_review",
                          "actual_review",
                          "passed",
                        ],
                        "resolveflow-evaluation.csv",
                      )
                    }
                  >
                    Export report
                  </button>
                )}
              </div>
              {rows.length > 0 && (
                <label>
                  Run history
                  <select
                    value={report?.id || ""}
                    onChange={(event) =>
                      setReport(
                        rows.find((row) => row.id === event.target.value) ||
                          lastEvaluation,
                      )
                    }
                  >
                    <option value="">Select a run</option>
                    {rows.map((row) => (
                      <option key={row.id} value={row.id}>
                        {new Date(row.created_at).toLocaleString()} ·{" "}
                        {row.passed}/{row.total}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {report && (
                <>
                  <h2>
                    {report.passed} of {report.total} passed
                  </h2>
                  <div className="toolbar wrap">
                    {Object.entries(report.categories || {}).map(
                      ([category, counts]) => {
                        const result = counts as {
                          passed: number;
                          total: number;
                        };
                        return (
                          <span className="pill" key={category}>
                            {human(category)} · {result.passed}/{result.total}
                          </span>
                        );
                      },
                    )}
                    {report.regression_delta != null && (
                      <span className="pill">
                        Change from previous run · {report.regression_delta}
                      </span>
                    )}
                  </div>
                  {report.confusion && (
                    <details>
                      <summary>Classification confusion matrix</summary>
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Expected / Actual</th>
                              {Object.keys(report.confusion).map((key) => (
                                <th key={key}>{human(key)}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(report.confusion).map(
                              ([key, counts]) => (
                                <tr key={key}>
                                  <th>{human(key)}</th>
                                  {Object.keys(report.confusion).map(
                                    (label) => (
                                      <td key={label}>
                                        {(counts as Record<string, number>)[
                                          label
                                        ] ?? 0}
                                      </td>
                                    ),
                                  )}
                                </tr>
                              ),
                            )}
                          </tbody>
                        </table>
                      </div>
                    </details>
                  )}
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Order</th>
                          <th>Category</th>
                          <th>Expected</th>
                          <th>Actual</th>
                          <th>Result</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.cases.map((item: Row, index: number) => (
                          <tr key={index}>
                            <td>{item.order_id}</td>
                            <td>{item.category}</td>
                            <td>{human(item.expected_issue)}</td>
                            <td>{human(item.actual_issue)}</td>
                            <td>{item.passed ? "Passed" : "Failed"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </section>
          )}
          {page === "Audit Trail" && (
            <section className="panel table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Actor</th>
                    <th>Investigation</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((item) => (
                    <tr key={item.id}>
                      <td>{item.type}</td>
                      <td>{item.actor}</td>
                      <td className="mono">
                        {item.investigation_id.slice(0, 8)}
                      </td>
                      <td>{new Date(item.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!rows.length && (
                <p className="empty">
                  Audit events appear after the first investigation is created.
                </p>
              )}
            </section>
          )}
          {page === "Settings" && (
            <section className="panel stack">
              <h2>Account</h2>
              <p>{user?.email}</p>
              <p>{human(user?.role || "")}</p>
              <div className="toolbar">
                <button onClick={() => setLight(!light)}>
                  Switch to {light ? "dark" : "light"} theme
                </button>
                <button onClick={signOut}>Sign out</button>
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}

const human = (value: string) =>
  value
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/^./, (first) => first.toUpperCase());

function Citations({ matches }: { matches: Row[] }) {
  return (
    <div className="citations">
      {matches.length ? (
        matches.map((item) => (
          <article key={item.id + item.section}>
            <strong>{item.name}</strong>
            <small>
              {item.id} · §{item.section} · v{item.version} ·{" "}
              {item.effective_date} · {item.score.toFixed(2)} relevance
            </small>
            <small>{item.source}</small>
            <p>{item.passage}</p>
          </article>
        ))
      ) : (
        <p className="empty">No matching policy passages.</p>
      )}
    </div>
  );
}

function CaseDetails({
  item,
  busy,
  retry,
  evidence,
}: {
  item?: Row;
  busy: boolean;
  retry: (id: string) => void;
  evidence: (id: string, context: string) => void;
}) {
  return (
    <section className="panel stack">
      <div className="toolbar wrap">
        <h2>{item?.order_id || "Investigation workflow"}</h2>
        {item && <span className="pill">{item.status}</span>}
      </div>
      <div className="stages">
        {stages.map((stage, index) => {
          const trace = item?.trace?.find(
            (entry: Row) => entry.agent === stage,
          );
          const running =
            item?.status === "Running" && (item.trace?.length ?? 0) === index;
          return (
            <details key={stage} className={trace ? "complete" : ""}>
              <summary>
                <span className="stage-icon">
                  {trace ? <CheckCircle2 size={16} /> : index + 1}
                </span>
                <strong>{stage}</strong>
                <small>
                  {trace
                    ? trace.duration_ms + " ms"
                    : running
                      ? "Running"
                      : "Waiting"}
                </small>
              </summary>
              {trace && (
                <>
                  <p>
                    {new Date(trace.at).toLocaleString()} ·{" "}
                    {trace.references?.length ?? 0} evidence references
                  </p>
                  {!!trace.tool_calls?.length && (
                    <p>{trace.tool_calls.join(" · ")}</p>
                  )}
                  <pre>{JSON.stringify(trace.output, null, 2)}</pre>
                </>
              )}
            </details>
          );
        })}
      </div>
      {!item && (
        <p className="empty">
          Run or select an investigation to inspect its agent outputs.
        </p>
      )}
      {item && ["Queued", "Failed"].includes(item.status) && !busy && (
        <button onClick={() => retry(item.id)}>Run investigation</button>
      )}
      {item?.classification && (
        <div className="finding">
          <h3>{human(item.classification.issue_type)}</h3>
          <span className="pill">{item.classification.severity}</span>
          <p>{item.classification.reasoning}</p>
        </div>
      )}
      {item?.resolution && (
        <>
          <h3>Recommended resolution</h3>
          <strong>{item.resolution.action}</strong>
          <p>{item.resolution.draft}</p>
          <Citations matches={item.policies} />
        </>
      )}
      {item?.decision && (
        <p>
          Decision recorded by {item.decision.actor}. {item.decision.notes}
        </p>
      )}
      {item &&
        ["Evidence requested", "Revision requested"].includes(item.status) && (
          <form
            className="stack"
            onSubmit={(event) => {
              event.preventDefault();
              evidence(
                item.id,
                String(new FormData(event.currentTarget).get("context") || ""),
              );
            }}
          >
            <label>
              Additional context
              <textarea
                name="context"
                minLength={5}
                maxLength={4000}
                required
              />
            </label>
            <button disabled={busy}>Submit context and rerun</button>
          </form>
        )}
    </section>
  );
}

function Chart({
  title,
  data,
  color,
}: {
  title: string;
  data?: Record<string, number>;
  color: string;
}) {
  const points = Object.entries(data || {}).map(([key, value]) => ({
    name: human(key),
    value,
  }));
  return (
    <section className="panel chart">
      <h2>{title}</h2>
      {points.some((point) => point.value > 0) ? (
        <ResponsiveContainer width="100%" height={190}>
          <BarChart
            data={points}
            margin={{ left: -18, right: 5, top: 10, bottom: 10 }}
          >
            <CartesianGrid vertical={false} stroke="var(--line)" />
            <XAxis
              dataKey="name"
              tick={{ fill: "var(--muted)", fontSize: 10 }}
              interval={0}
            />
            <YAxis tick={{ fill: "var(--muted)", fontSize: 11 }} />
            <Tooltip
              cursor={{ fill: "var(--line)" }}
              contentStyle={{
                background: "var(--card)",
                borderColor: "var(--line)",
              }}
            />
            <Bar
              dataKey="value"
              fill={color}
              radius={[4, 4, 0, 0]}
              maxBarSize={42}
            />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div className="chart-empty">
          <BarChart3 size={25} />
          <span>No investigation data yet</span>
        </div>
      )}
    </section>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
