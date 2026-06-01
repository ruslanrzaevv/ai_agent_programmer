  import { useEffect, useState } from "react";
  import { COLORS } from "../utils/constants";
  import { Alert, Button, Card, Empty, Input, Select, Spinner } from "../components/ui";
  import { useProjectStore } from "../store/projectStore";
  import { timeAgo } from "../utils/helpers";
  import SetupWizardModal from "../components/ai/SetupWizardModal";
  import { aiAPI } from "../services/api";


  const EMPTY_FORM = {
    name: "", description: "", environment: "production",
    docker_engine_url: "", docker_tls_enabled: false,
    docker_tls_cert: "", docker_tls_key: "", docker_tls_ca: "",
    gitlab_url: "https://gitlab.com", gitlab_token: "",
    gitlab_project_id: "", gitlab_webhook_secret: "",
    error_threshold_per_minute: 5,
    notify_channels: ["email"],
    log_level_filter: ["error", "critical"],
  };

  function ProjectForm({ onClose }) {
    const [form, setForm] = useState(EMPTY_FORM);
    const [error, setError] = useState("");
    const [showWizard, setShowWizard] = useState(false);
    const [analysis, setAnalysis] = useState(null);
    const [explanation, setExplanation] = useState("");

    const scoreColor =
    analysis?.status === "excellent"
      ? "#22c55e"
      : analysis?.status === "good"
      ? "#84cc16"
      : analysis?.status === "warning"
      ? "#f59e0b"
      : "#ef4444";

      
      async function explain(
        issue,
        level
      ) {
        try {
      
          const { data } =
            await aiAPI.explainIssue(
              issue,
              level
            );
      
          setExplanation(
            data.explanation
          );
      
        } catch (err) {
          console.error(err);
        }
      }

    async function analyzeSetup() {
      try {
        const { data } =
          await aiAPI.analyzeSetup(form);

        console.log(data)
        setAnalysis(data)

        } catch (err) {
          console.error(err);
      }
    }
    
    const { create, loading } = useProjectStore();
    function handle(e) {
      const { name, value, type, checked } = e.target;
      setForm(f => ({ ...f, [name]: type === "checkbox" ? checked : value }));
      setError("");
    }

    async function submit(e) {
      e.preventDefault();
      if (!form.name || !form.docker_engine_url || !form.gitlab_token || !form.gitlab_project_id) {
        setError("Please fill in all required fields");
        return;
      }
      const payload = {
        ...form,
        error_threshold_per_minute: Number(form.error_threshold_per_minute),
        docker_tls_enabled: Boolean(form.docker_tls_enabled),
        docker_tls_cert: form.docker_tls_cert || undefined,
        docker_tls_key: form.docker_tls_key || undefined,
        docker_tls_ca: form.docker_tls_ca || undefined,
        gitlab_webhook_secret: form.gitlab_webhook_secret || undefined,
        description: form.description || undefined,
      };
      const res = await create(payload);
      if (res.ok) onClose();
      else setError(res.error || "Failed to create project");
    }

    const row = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 };
    const full = { gridColumn: "1 / -1" };
    const divider = {
      gridColumn: "1 / -1", borderTop: `1px solid ${COLORS.border}`,
      paddingTop: 16, marginTop: 4,
      fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace",
      textTransform: "uppercase", letterSpacing: "0.1em",
    };

    return (
      <Card style={{ padding: 28 }} glow="rgba(79,142,247,0.06)">
        <div style={{ fontSize: 12, color: COLORS.accent, fontFamily: "'Space Mono', monospace",
          letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 20 }}>
          ◈ New Project
        </div>
        <form onSubmit={submit}>
          <div style={row}>
            {/* Basic */}
            <div style={full}>
              <Input label="Project Name *" name="name" value={form.name} onChange={handle}
                placeholder="my-production-app" />
            </div>
            <div style={full}>
              <Input label="Description" name="description" value={form.description} onChange={handle}
                placeholder="Optional description" />
            </div>
            <Select label="Environment" name="environment" value={form.environment} onChange={handle}>
              <option value="production">Production</option>
              <option value="staging">Staging</option>
              <option value="development">Development</option>
            </Select>
            <Input label="Error Threshold / min" name="error_threshold_per_minute" type="number"
              value={form.error_threshold_per_minute} onChange={handle} min={1} max={1000} />

            {/* Docker */}
            <div style={divider}>
              Docker Engine
              <Button
                type="button"
                small
                style={{ marginLeft: 12 }}
                onClick={() => setShowWizard(true)}
              >
                🤖 AI Setup
              </Button>
              <Button
                type="button"
                onClick={analyzeSetup}
              >
                ✨ Analyze Setup
              </Button>
              {analysis && (
    <Card
      style={{
        marginTop: 20,
        padding: 20,
      }}
    >
      <h2>
        OpsMind Health Score
      </h2>

      <h1
        style={{
          color: scoreColor,
          fontSize: 48,
        }}
      >
      {analysis.score}/100
      </h1>

      <p>
        {analysis.summary}
      </p>

      <h3>Issues</h3>

      <ul>
        {analysis.issues?.map((item, i) => (
          <li key={i}>
            {item}

            <div
              style={{
                display: "flex",
                gap: 8,
                marginTop: 6,
                marginBottom: 12,
              }}
            > 
              <Button
                type="button"
                onClick={() =>
                  explain(item, "junior")
                }
              >
                Junior
              </Button>

              <Button
                type="button"
                onClick={() =>
                  explain(item, "middle")
                }
              >
                Middle
              </Button>

              <Button
                type="button"
                onClick={() =>
                  explain(item, "senior")
                }
              >
                Senior
              </Button>
            </div>
          </li>
        ))}
      </ul>

      <h3>Recommendations</h3>

      {explanation && (
  <Card
    style={{
      marginTop: 20,
      padding: 16,
    }}
  >
    <h3>
      🤖 AI Explanation
    </h3>

    <p>
      {explanation}
    </p>
  </Card>
)}  

      <ul>
        {analysis.recommendations?.map(
          (item, i) => (
            <li key={i}>{item}</li>
          )
        )}
      </ul>
    </Card>
  )}
            </div>
            <div style={full}>
              <Input label="Docker Engine URL *" name="docker_engine_url" value={form.docker_engine_url}
                onChange={handle} placeholder="tcp://your-server.com:2376" />
            </div>
            <div style={{ ...full, display: "flex", alignItems: "center", gap: 10 }}>
              <input type="checkbox" id="tls" name="docker_tls_enabled"
                checked={form.docker_tls_enabled} onChange={handle} />
              <label htmlFor="tls" style={{ fontSize: 13, color: COLORS.textSecondary, cursor: "pointer" }}>
                Enable TLS
              </label>
            </div>
            {form.docker_tls_enabled && (
              <>
                <div style={full}>
                  <Input label="TLS Certificate (PEM)" name="docker_tls_cert" value={form.docker_tls_cert}
                    onChange={handle} placeholder="-----BEGIN CERTIFICATE-----" />
                </div>
                <div style={full}>
                  <Input label="TLS Key (PEM)" name="docker_tls_key" value={form.docker_tls_key}
                    onChange={handle} placeholder="-----BEGIN RSA PRIVATE KEY-----" />
                </div>
                <div style={full}>
                  <Input label="CA Certificate (PEM)" name="docker_tls_ca" value={form.docker_tls_ca}
                    onChange={handle} placeholder="-----BEGIN CERTIFICATE-----" />
                </div>
              </>
            )}

            {/* GitLab */}
            <div style={divider}>GitLab</div>
            <Input label="GitLab URL" name="gitlab_url" value={form.gitlab_url} onChange={handle} />
            <Input label="Project ID *" name="gitlab_project_id" value={form.gitlab_project_id}
              onChange={handle} placeholder="12345" />
            <div style={full}>
              <Input label="Access Token *" name="gitlab_token" type="password"
                value={form.gitlab_token} onChange={handle} placeholder="glpat-xxxxxxxxxxxxxxxxxxxx" />
            </div>
            <div style={full}>
              <Input label="Webhook Secret (optional)" name="gitlab_webhook_secret"
                value={form.gitlab_webhook_secret} onChange={handle} placeholder="mysecret" />
            </div>

            {/* Alerts */}
            <div style={divider}>Alerts & Notifications</div>
            <div style={full}>
              <div style={{ fontSize: 11, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace",
                textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
                Notify via
              </div>
              <div style={{ display: "flex", gap: 12 }}>
                {["email","sms"].map(ch => (
                  <label key={ch} style={{ display: "flex", alignItems: "center", gap: 7,
                    cursor: "pointer", fontSize: 13, color: COLORS.textSecondary }}>
                    <input type="checkbox" checked={form.notify_channels.includes(ch)}
                      onChange={e => {
                        const channels = e.target.checked
                          ? [...form.notify_channels, ch]
                          : form.notify_channels.filter(c => c !== ch);
                        setForm(f => ({ ...f, notify_channels: channels }));
                      }} />
                    {ch.toUpperCase()}
                  </label>
                ))}
              </div>
            </div>

            {/* Error + Submit */}
            {error && <div style={full}><Alert type="error">{error}</Alert></div>}
            <div style={{ ...full, display: "flex", gap: 10, marginTop: 6 }}>
              <Button primary type="submit" disabled={loading} style={{ flex: 1 }}>
                {loading ? <Spinner size={16} /> : "⚡ Start Monitoring"}
              </Button>
              <Button onClick={onClose} style={{ flex: 1 }}>Cancel</Button>
            </div>
          </div>
        </form>
        {showWizard && (  
          <SetupWizardModal
            category="docker"
            onClose={() => setShowWizard(false)}
            onApply={(values) =>
              setForm((prev) => ({
                ...prev,
                ...values,
              }))
            }
          />
        )}
      </Card>
    );
  }

  export default function ProjectsPage() {
    const { projects, activeProject, fetch, delete: deleteProject, setActive, loading } = useProjectStore();
    const [showForm, setShowForm] = useState(false);
    const [deleting, setDeleting] = useState(null);

    useEffect(() => { fetch(); }, []);

    async function handleDelete(id) {
      if (!window.confirm("Delete this project and stop monitoring?")) return;
      setDeleting(id);
      await deleteProject(id);
      setDeleting(null);
    }

    return (
      <div style={{ padding: "32px 36px", maxWidth: 860, animation: "fade-in 0.3s ease" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 600, color: COLORS.textPrimary,
              letterSpacing: "-0.02em", marginBottom: 4 }}>Projects</h1>
            <div style={{ fontSize: 13, color: COLORS.textMuted }}>
              {projects.length} project{projects.length !== 1 ? "s" : ""} connected
            </div>
          </div>
          <Button primary onClick={() => setShowForm(f => !f)}>
            {showForm ? "✕ Cancel" : "+ Add Project"}
          </Button>
        </div>

        {showForm && (
          <div style={{ marginBottom: 24 }}>
            <ProjectForm onClose={() => setShowForm(false)} />
          </div>
        )}

        {/* Project list */}
        {loading && projects.length === 0 ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 48 }}>
            <Spinner size={28} />
          </div>
        ) : projects.length === 0 ? (
          <Empty icon="◈" title="No projects yet"
            description="Connect your first project to start monitoring Docker logs and GitLab pipelines"
            action={<Button primary onClick={() => setShowForm(true)}>+ Add First Project</Button>} />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {projects.map(project => (
              <Card key={project.id} style={{ padding: "20px 24px" }}
                glow={activeProject?.id === project.id ? "rgba(79,142,247,0.06)" : undefined}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
                      <div style={{ width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                        background: project.monitoring_enabled ? COLORS.green : COLORS.textMuted,
                        boxShadow: project.monitoring_enabled ? `0 0 6px ${COLORS.green}` : "none",
                        animation: project.monitoring_enabled ? "pulse-dot 2s infinite" : "none" }} />
                      <span style={{ fontSize: 15, fontWeight: 600, color: COLORS.textPrimary }}>
                        {project.name}
                      </span>
                      <span style={{ fontSize: 11, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace",
                        background: COLORS.bg, padding: "2px 8px", borderRadius: 4,
                        border: `1px solid ${COLORS.border}` }}>
                        {project.environment}
                      </span>
                      {activeProject?.id === project.id && (
                        <span style={{ fontSize: 10, color: COLORS.accent, fontFamily: "'Space Mono', monospace",
                          letterSpacing: "0.08em" }}>ACTIVE</span>
                      )}
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginBottom: 12 }}>
                      {[
                        { label: "Docker", value: project.docker_engine_url },
                        { label: "GitLab", value: `${project.gitlab_url} / ${project.gitlab_project_id}` },
                        { label: "Threshold", value: `${project.error_threshold_per_minute} errors/min` },
                        { label: "Notify", value: (project.notify_channels || []).join(", ") || "—" },
                      ].map(item => (
                        <div key={item.label}>
                          <span style={{ fontSize: 10, color: COLORS.textMuted,
                            fontFamily: "'Space Mono', monospace", textTransform: "uppercase",
                            letterSpacing: "0.08em" }}>{item.label}: </span>
                          <span style={{ fontSize: 12, color: COLORS.textSecondary,
                            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {item.value}
                          </span>
                        </div>
                      ))}
                    </div>

                    <div style={{ fontSize: 11, color: COLORS.textMuted }}>
                      Created {timeAgo(project.created_at)}
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: "flex", gap: 7, marginLeft: 16, flexShrink: 0 }}>
                    {activeProject?.id !== project.id && (
                      <Button small onClick={() => setActive(project)}>Select</Button>
                    )}
                    <Button small danger onClick={() => handleDelete(project.id)}
                      disabled={deleting === project.id}>
                      {deleting === project.id ? <Spinner size={14} /> : "Delete"}
                    </Button>
                  </div>
                </div>

                {/* GitLab webhook tip */}
                {project.gitlab_webhook_secret && (
                  <div style={{ marginTop: 12, padding: "9px 12px", borderRadius: 7,
                    background: COLORS.bg, border: `1px solid ${COLORS.border}`,
                    fontSize: 11, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace" }}>
                    Webhook URL: <span style={{ color: COLORS.accent }}>
                      {window.location.origin}/api/v1/webhooks/gitlab/{project.id}
                    </span>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    );
  }