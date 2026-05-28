import {
  AlertTriangle,
  CheckCircle2,
  History,
  KeyRound,
  Loader2,
  Network,
  RefreshCw,
  RotateCcw,
  Route,
  Shield,
  TerminalSquare,
  Trash2,
  Power,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const emptyRule = {
  source_ip: "10.0.1.2",
  destination_ip: "10.0.2.2",
  protocol: "tcp",
  port: "80",
  action: "ALLOW",
  enabled: true,
};

const emptyRoute = {
  namespace: "client",
  destination_cidr: "10.0.99.0/24",
  next_hop: "10.0.1.1",
};

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = typeof payload === "string" ? payload : JSON.stringify(payload);
    throw new Error(detail || `Request failed with HTTP ${response.status}`);
  }

  return payload;
}

function apiHeaders(apiKey, extra = {}) {
  return {
    ...extra,
    ...(apiKey ? { "X-NetGuard-API-Key": apiKey } : {}),
  };
}

function formatDate(value) {
  if (!value) return "never";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function StatusPill({ children, tone = "neutral" }) {
  const tones = {
    success: "bg-guard-100 text-guard-700",
    danger: "bg-red-100 text-signal-red",
    warning: "bg-amber-100 text-signal-amber",
    neutral: "bg-slate-100 text-slate-700",
  };

  return (
    <span className={`inline-flex min-h-6 items-center rounded-full px-2.5 py-0.5 text-xs font-bold ${tones[tone]}`}>
      {children}
    </span>
  );
}

function MetricCard({ icon: Icon, label, value }) {
  return (
    <section className="rounded-lg border border-line bg-white p-4 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-semibold text-slate-500">{label}</span>
        <Icon className="h-5 w-5 text-guard-600" aria-hidden="true" />
      </div>
      <strong className="mt-3 block text-3xl">{value}</strong>
    </section>
  );
}

function Panel({ title, subtitle, children, action }) {
  return (
    <section className="rounded-lg border border-line bg-white shadow-panel">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3">
        <div>
          <h2 className="text-base font-bold">{title}</h2>
          {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
        </div>
        {action}
      </header>
      <div className="p-4">{children}</div>
    </section>
  );
}

function TextField({ label, value, onChange, placeholder, type = "text" }) {
  return (
    <label className="grid gap-1.5">
      <span className="text-xs font-bold uppercase text-slate-500">{label}</span>
      <input
        className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none ring-guard-600/20 focus:ring-4"
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function SelectField({ label, value, onChange, children }) {
  return (
    <label className="grid gap-1.5">
      <span className="text-xs font-bold uppercase text-slate-500">{label}</span>
      <select
        className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none ring-guard-600/20 focus:ring-4"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {children}
      </select>
    </label>
  );
}

function PrimaryButton({ children, onClick, disabled, tone = "primary", type = "button", icon: Icon }) {
  const tones = {
    primary: "bg-guard-600 text-white hover:bg-guard-700",
    secondary: "bg-slate-800 text-white hover:bg-slate-950",
    danger: "bg-signal-red text-white hover:bg-red-800",
  };

  return (
    <button
      className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-md px-3 text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-55 ${tones[tone]}`}
      disabled={disabled}
      type={type}
      onClick={onClick}
    >
      {Icon ? <Icon className="h-4 w-4" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}

function ApiKeyBox({ apiKey, setApiKey }) {
  return (
    <Panel title="Protected Actions" subtitle="Write operations use the same X-NetGuard-API-Key as the REST API.">
      <label className="grid gap-1.5">
        <span className="flex items-center gap-2 text-xs font-bold uppercase text-slate-500">
          <KeyRound className="h-4 w-4" aria-hidden="true" />
          API key
        </span>
        <input
          className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none ring-guard-600/20 focus:ring-4"
          type="password"
          value={apiKey}
          placeholder="Paste demo key for create/apply/rollback"
          onChange={(event) => setApiKey(event.target.value)}
        />
      </label>
      <p className="mt-3 text-sm text-slate-500">GET views stay public. This key is only sent when you click a write action.</p>
    </Panel>
  );
}

function App() {
  const [apiKey, setApiKey] = useState("");
  const [firewallRules, setFirewallRules] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [ruleForm, setRuleForm] = useState(emptyRule);
  const [routeForm, setRouteForm] = useState(emptyRoute);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState("");
  const [notice, setNotice] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [rulesData, routesData, snapshotsData, alertsData] = await Promise.all([
        requestJson("/api/firewall-rules/"),
        requestJson("/api/routes/"),
        requestJson("/api/config-history/"),
        requestJson("/api/alerts/"),
      ]);
      setFirewallRules(rulesData);
      setRoutes(routesData);
      setSnapshots(snapshotsData);
      setAlerts(alertsData);
      setNotice(null);
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const latestSnapshot = snapshots[0];
  const highAlerts = useMemo(() => alerts.filter((alert) => alert.severity === "HIGH").length, [alerts]);

  async function runWriteAction(label, action) {
    if (!apiKey) {
      setNotice({ type: "error", text: "Paste the NetGuard API key before running a write action." });
      return;
    }

    setSubmitting(label);
    try {
      const result = await action();
      setNotice({ type: "success", text: result });
      await refresh();
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    } finally {
      setSubmitting("");
    }
  }

  function createFirewallRule(event) {
    event.preventDefault();
    runWriteAction("rule", async () => {
      const payload = {
        ...ruleForm,
        port: ruleForm.protocol.toLowerCase() === "icmp" || ruleForm.port === "" ? null : Number(ruleForm.port),
      };
      const created = await requestJson("/api/firewall-rules/", {
        method: "POST",
        headers: apiHeaders(apiKey, { "Content-Type": "application/json" }),
        body: JSON.stringify(payload),
      });
      setRuleForm(emptyRule);
      return `Created firewall rule #${created.id}.`;
    });
  }

  function createRoute(event) {
    event.preventDefault();
    runWriteAction("route", async () => {
      const created = await requestJson("/api/routes/", {
        method: "POST",
        headers: apiHeaders(apiKey, { "Content-Type": "application/json" }),
        body: JSON.stringify(routeForm),
      });
      setRouteForm(emptyRoute);
      return `Created static route #${created.id}.`;
    });
  }

  function applyConfig() {
    runWriteAction("apply", async () => {
      const result = await requestJson("/api/apply-config/", {
        method: "POST",
        headers: apiHeaders(apiKey),
      });
      return `${result.message} Snapshot #${result.snapshot.id}.`;
    });
  }

  function rollback(snapshotId) {
    runWriteAction(`rollback-${snapshotId}`, async () => {
      const result = await requestJson(`/api/rollback/${snapshotId}/`, {
        method: "POST",
        headers: apiHeaders(apiKey),
      });
      return `${result.message} Snapshot #${result.snapshot.id}.`;
    });
  }

  function toggleFirewallRule(rule) {
    runWriteAction(`toggle-rule-${rule.id}`, async () => {
      const updated = await requestJson(`/api/firewall-rules/${rule.id}/`, {
        method: "PATCH",
        headers: apiHeaders(apiKey, { "Content-Type": "application/json" }),
        body: JSON.stringify({ enabled: !rule.enabled }),
      });
      return `Rule #${updated.id} is now ${updated.enabled ? "enabled" : "disabled"}. Click Apply Config to push the change.`;
    });
  }

  function deleteFirewallRule(rule) {
    const shouldDelete = window.confirm(`Delete firewall rule #${rule.id}? Apply Config after deleting to update iptables.`);
    if (!shouldDelete) return;

    runWriteAction(`delete-rule-${rule.id}`, async () => {
      await requestJson(`/api/firewall-rules/${rule.id}/`, {
        method: "DELETE",
        headers: apiHeaders(apiKey),
      });
      return `Deleted firewall rule #${rule.id}. Click Apply Config to push the change.`;
    });
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white/90">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-5 lg:px-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-guard-600 text-white">
                <Shield className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl font-black tracking-normal">NetGuardAutomator</h1>
                <p className="text-sm text-slate-500">Network security automation lab</p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <a className="rounded-md border border-line px-3 py-2 text-sm font-bold text-slate-700" href="/api/firewall-rules/">
              API
            </a>
            <PrimaryButton disabled={loading} icon={RefreshCw} onClick={refresh} tone="secondary">
              Refresh
            </PrimaryButton>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-5 px-4 py-5 lg:px-6">
        {notice ? (
          <div
            className={`rounded-lg border px-4 py-3 text-sm font-semibold ${
              notice.type === "error"
                ? "border-red-200 bg-red-50 text-signal-red"
                : "border-guard-100 bg-guard-50 text-guard-700"
            }`}
          >
            {notice.text}
          </div>
        ) : null}

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard icon={Shield} label="Firewall Rules" value={firewallRules.length} />
          <MetricCard icon={Route} label="Static Routes" value={routes.length} />
          <MetricCard icon={History} label="Config Snapshots" value={snapshots.length} />
          <MetricCard icon={AlertTriangle} label="High Alerts" value={highAlerts} />
        </section>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
          <div className="grid gap-5">
            <Panel title="Firewall Policy" subtitle="Enabled records become iptables FORWARD rules when config is applied.">
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Loading rules
                </div>
              ) : firewallRules.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[860px] table-fixed border-collapse">
                    <thead>
                      <tr className="border-b border-line text-left text-xs uppercase text-slate-500">
                        <th className="px-3 py-2">Action</th>
                        <th className="px-3 py-2">Source</th>
                        <th className="px-3 py-2">Destination</th>
                        <th className="px-3 py-2">Protocol</th>
                        <th className="px-3 py-2">Port</th>
                        <th className="px-3 py-2">Enabled</th>
                        <th className="px-3 py-2">Manage</th>
                      </tr>
                    </thead>
                    <tbody>
                      {firewallRules.map((rule) => (
                        <tr className="border-b border-line last:border-0" key={rule.id}>
                          <td className="px-3 py-3">
                            <StatusPill tone={rule.action === "ALLOW" ? "success" : "danger"}>{rule.action}</StatusPill>
                          </td>
                          <td className="break-words px-3 py-3 text-sm">{rule.source_ip}</td>
                          <td className="break-words px-3 py-3 text-sm">{rule.destination_ip}</td>
                          <td className="px-3 py-3 text-sm">{rule.protocol}</td>
                          <td className="px-3 py-3 text-sm">{rule.port || "any"}</td>
                          <td className="px-3 py-3 text-sm">
                            <StatusPill tone={rule.enabled ? "success" : "neutral"}>{rule.enabled ? "yes" : "no"}</StatusPill>
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex flex-wrap gap-2">
                              <PrimaryButton
                                disabled={submitting === `toggle-rule-${rule.id}`}
                                icon={Power}
                                onClick={() => toggleFirewallRule(rule)}
                                tone="secondary"
                              >
                                {rule.enabled ? "Disable" : "Enable"}
                              </PrimaryButton>
                              <PrimaryButton
                                disabled={submitting === `delete-rule-${rule.id}`}
                                icon={Trash2}
                                onClick={() => deleteFirewallRule(rule)}
                                tone="danger"
                              >
                                Delete
                              </PrimaryButton>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-slate-500">No firewall rules yet.</p>
              )}
            </Panel>

            <Panel title="Static Routes" subtitle="Routes stored in PostgreSQL and applied inside network namespaces.">
              {routes.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[520px] table-fixed border-collapse">
                    <thead>
                      <tr className="border-b border-line text-left text-xs uppercase text-slate-500">
                        <th className="px-3 py-2">Namespace</th>
                        <th className="px-3 py-2">Destination</th>
                        <th className="px-3 py-2">Next Hop</th>
                      </tr>
                    </thead>
                    <tbody>
                      {routes.map((route) => (
                        <tr className="border-b border-line last:border-0" key={route.id}>
                          <td className="px-3 py-3 text-sm font-semibold">{route.namespace}</td>
                          <td className="px-3 py-3 text-sm">{route.destination_cidr}</td>
                          <td className="px-3 py-3 text-sm">{route.next_hop}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-slate-500">No static routes yet.</p>
              )}
            </Panel>

            <Panel title="Config History" subtitle="Rendered snapshots, apply state, and rollback controls.">
              {snapshots.length ? (
                <div className="grid gap-3">
                  {snapshots.slice(0, 8).map((snapshot) => (
                    <article className="rounded-md border border-line p-3" key={snapshot.id}>
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <strong>Snapshot #{snapshot.id}</strong>
                            <StatusPill tone={snapshot.applied_successfully ? "success" : "danger"}>
                              {snapshot.applied_successfully ? "applied" : "failed"}
                            </StatusPill>
                          </div>
                          <p className="mt-1 text-sm text-slate-500">
                            {snapshot.config_type} · {formatDate(snapshot.created_at)}
                          </p>
                        </div>
                        <PrimaryButton
                          disabled={submitting === `rollback-${snapshot.id}`}
                          icon={RotateCcw}
                          onClick={() => rollback(snapshot.id)}
                          tone="secondary"
                        >
                          Rollback
                        </PrimaryButton>
                      </div>
                      <pre className="mt-3 max-h-40 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">
                        {snapshot.rendered_config}
                      </pre>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No config snapshots yet.</p>
              )}
            </Panel>

            <Panel title="Alerts" subtitle="Health, drift, route, rollback, and traffic-volume findings.">
              {alerts.length ? (
                <div className="grid gap-3">
                  {alerts.slice(0, 8).map((alert) => (
                    <article className="rounded-md border border-line p-3" key={alert.id}>
                      <div className="flex flex-wrap items-center gap-2">
                        <StatusPill tone={alert.severity === "HIGH" ? "danger" : alert.severity === "MEDIUM" ? "warning" : "neutral"}>
                          {alert.severity}
                        </StatusPill>
                        <strong>{alert.alert_type}</strong>
                        <span className="text-sm text-slate-500">{formatDate(alert.created_at)}</span>
                      </div>
                      <p className="mt-2 line-clamp-3 text-sm text-slate-600">{alert.description}</p>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No alerts yet.</p>
              )}
            </Panel>
          </div>

          <aside className="grid content-start gap-5">
            <ApiKeyBox apiKey={apiKey} setApiKey={setApiKey} />

            <Panel
              title="Apply Current Config"
              subtitle={latestSnapshot ? `Latest snapshot #${latestSnapshot.id} created ${formatDate(latestSnapshot.created_at)}` : "No snapshots yet"}
              action={
                latestSnapshot?.applied_successfully ? (
                  <CheckCircle2 className="h-5 w-5 text-guard-600" aria-hidden="true" />
                ) : (
                  <TerminalSquare className="h-5 w-5 text-slate-500" aria-hidden="true" />
                )
              }
            >
              <PrimaryButton disabled={submitting === "apply"} icon={Network} onClick={applyConfig}>
                {submitting === "apply" ? "Applying..." : "Apply Config"}
              </PrimaryButton>
            </Panel>

            <Panel title="Add Firewall Rule" subtitle="Create ALLOW or DENY policy rows.">
              <form className="grid gap-3" onSubmit={createFirewallRule}>
                <TextField
                  label="Source IP"
                  value={ruleForm.source_ip}
                  onChange={(value) => setRuleForm({ ...ruleForm, source_ip: value })}
                />
                <TextField
                  label="Destination IP"
                  value={ruleForm.destination_ip}
                  onChange={(value) => setRuleForm({ ...ruleForm, destination_ip: value })}
                />
                <div className="grid gap-3 sm:grid-cols-2">
                  <SelectField
                    label="Protocol"
                    value={ruleForm.protocol}
                    onChange={(value) => setRuleForm({ ...ruleForm, protocol: value, port: value === "icmp" ? "" : ruleForm.port })}
                  >
                    <option value="tcp">tcp</option>
                    <option value="udp">udp</option>
                    <option value="icmp">icmp</option>
                  </SelectField>
                  <TextField
                    label="Port"
                    type="number"
                    value={ruleForm.port}
                    onChange={(value) => setRuleForm({ ...ruleForm, port: value })}
                    placeholder="80"
                  />
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <SelectField label="Action" value={ruleForm.action} onChange={(value) => setRuleForm({ ...ruleForm, action: value })}>
                    <option value="ALLOW">ALLOW</option>
                    <option value="DENY">DENY</option>
                  </SelectField>
                  <label className="flex min-h-10 items-center gap-2 pt-5 text-sm font-semibold text-slate-700">
                    <input
                      checked={ruleForm.enabled}
                      className="h-4 w-4"
                      type="checkbox"
                      onChange={(event) => setRuleForm({ ...ruleForm, enabled: event.target.checked })}
                    />
                    Enabled
                  </label>
                </div>
                <PrimaryButton disabled={submitting === "rule"} type="submit">
                  {submitting === "rule" ? "Adding..." : "Add Rule"}
                </PrimaryButton>
              </form>
            </Panel>

            <Panel title="Add Static Route" subtitle="Store a route for Ansible to apply.">
              <form className="grid gap-3" onSubmit={createRoute}>
                <TextField
                  label="Namespace"
                  value={routeForm.namespace}
                  onChange={(value) => setRouteForm({ ...routeForm, namespace: value })}
                />
                <TextField
                  label="Destination CIDR"
                  value={routeForm.destination_cidr}
                  onChange={(value) => setRouteForm({ ...routeForm, destination_cidr: value })}
                />
                <TextField label="Next Hop" value={routeForm.next_hop} onChange={(value) => setRouteForm({ ...routeForm, next_hop: value })} />
                <PrimaryButton disabled={submitting === "route"} type="submit">
                  {submitting === "route" ? "Adding..." : "Add Route"}
                </PrimaryButton>
              </form>
            </Panel>
          </aside>
        </div>
      </main>
    </div>
  );
}

export default App;
