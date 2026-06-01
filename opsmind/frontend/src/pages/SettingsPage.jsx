import { useState, useEffect } from "react";
import { COLORS } from "../utils/constants";
import { Alert, Button, Card, Input, Select, Spinner } from "../components/ui";
import { useAuthStore } from "../store/authStore";
import { usersAPI } from "../services/api";
import api from "../services/api";

// ── Telegram API вызовы ────────────────────────────────────────────────────────
const telegramAPI = {
  status:     ()  => api.get("/telegram/status"),
  connect:    ()  => api.post("/telegram/connect"),
  disconnect: ()  => api.delete("/telegram/disconnect"),
};

// ── Компонент блока Telegram ──────────────────────────────────────────────────
function TelegramBlock() {
  const [status, setStatus]       = useState(null);   // { connected, telegram_username, ... }
  const [connectUrl, setConnectUrl] = useState("");
  const [loading, setLoading]     = useState(false);
  const [copied, setCopied]       = useState(false);
  const [error, setError]         = useState("");

  // Загрузить статус при монтировании
  useEffect(() => {
    telegramAPI.status()
      .then(r => setStatus(r.data))
      .catch(() => {});
  }, []);

  // Сгенерировать ссылку привязки
  async function handleConnect() {
    setLoading(true); setError("");
    try {
      const { data } = await telegramAPI.connect();
      setConnectUrl(data.connect_url);
      setStatus(prev => ({ ...prev, already_connected: data.already_connected }));
    } catch (e) {
      setError(e.response?.data?.detail || "Ошибка генерации ссылки");
    }
    setLoading(false);
  }

  // Отвязать Telegram
  async function handleDisconnect() {
    if (!window.confirm("Отключить Telegram уведомления?")) return;
    setLoading(true); setError("");
    try {
      await telegramAPI.disconnect();
      setStatus(s => ({ ...s, connected: false, telegram_username: null }));
      setConnectUrl("");
    } catch (e) {
      setError(e.response?.data?.detail || "Ошибка отключения");
    }
    setLoading(false);
  }

  // Скопировать ссылку
  function copyUrl() {
    navigator.clipboard.writeText(connectUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Card style={{ padding: 24, marginBottom: 16 }}>
      {/* Заголовок */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
        <div style={{ fontSize: 12, color: COLORS.accent, fontFamily: "'Space Mono', monospace",
          letterSpacing: "0.1em", textTransform: "uppercase" }}>
          ✈ Telegram уведомления
        </div>
        {status?.connected && (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: COLORS.green,
              boxShadow: `0 0 6px ${COLORS.green}`, animation: "pulse-dot 2s infinite" }} />
            <span style={{ fontSize: 11, color: COLORS.green, fontFamily: "'Space Mono', monospace" }}>
              Подключён
            </span>
          </div>
        )}
      </div>

      {/* Уже подключён */}
      {status?.connected ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ background: COLORS.bg, borderRadius: 8, padding: "12px 16px",
            border: `1px solid ${COLORS.green}30`, display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 22 }}>✈</span>
            <div>
              <div style={{ fontSize: 13, color: COLORS.textPrimary, fontWeight: 500 }}>
                @{status.telegram_username || "Telegram пользователь"}
              </div>
              <div style={{ fontSize: 11, color: COLORS.textMuted, marginTop: 2 }}>
                Уведомления об инцидентах будут приходить в этот чат
              </div>
            </div>
          </div>

          {/* Пример сообщения */}
          <div style={{ background: COLORS.bg, borderRadius: 10, padding: 14,
            border: `1px solid ${COLORS.border}` }}>
            <div style={{ fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace",
              textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
              Пример уведомления
            </div>
            <div style={{ background: "#17212B", borderRadius: 8, padding: "12px 14px",
              fontFamily: "'DM Sans', sans-serif", fontSize: 13, lineHeight: 1.6 }}>
              <div style={{ color: "#FF6B6B", fontWeight: 600, marginBottom: 4 }}>
                🔴 Инцидент — CRITICAL
              </div>
              <div style={{ color: "#8A9BBE", fontSize: 12, marginBottom: 6 }}>
                ━━━━━━━━━━━━━━━━━━━━<br/>
                📦 <b style={{ color: "#E8EDF8" }}>Проект:</b> my-app (production)<br/>
                ⚡ <b style={{ color: "#E8EDF8" }}>Ошибок:</b> 47<br/>
                🕐 <b style={{ color: "#E8EDF8" }}>Время:</b> 2024-01-15 14:32 UTC
              </div>
              <div style={{ color: "#E8EDF8", fontWeight: 500, marginBottom: 6 }}>
                Database connection pool exhausted
              </div>
              <div style={{ color: "#8A9BBE", fontSize: 12 }}>
                💬 Connection pool hit max_size=10 limit...
              </div>
              <div style={{ marginTop: 10, display: "flex", gap: 6 }}>
                <div style={{ background: "#2B5278", borderRadius: 6, padding: "5px 12px",
                  fontSize: 12, color: "#5AABFF" }}>
                  🔍 Открыть инцидент
                </div>
                <div style={{ background: "#2B5278", borderRadius: 6, padding: "5px 12px",
                  fontSize: 12, color: "#5AABFF" }}>
                  ✓ Acknowledge
                </div>
              </div>
            </div>
          </div>

          {error && <Alert type="error">{error}</Alert>}

          <Button danger onClick={handleDisconnect} disabled={loading}>
            {loading ? <Spinner size={16} /> : "Отключить Telegram"}
          </Button>
        </div>

      ) : (
        /* Не подключён */
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ fontSize: 13, color: COLORS.textSecondary, lineHeight: 1.6 }}>
            Подключите Telegram чтобы получать мгновенные уведомления об инцидентах
            прямо в мессенджер. Прямо из сообщения можно нажать <b>Acknowledge</b>.
          </div>

          {/* Шаги */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {[
              { step: "1", text: "Нажмите кнопку ниже — сгенерируется ссылка" },
              { step: "2", text: "Откройте ссылку в Telegram" },
              { step: "3", text: "Нажмите /start в боте" },
              { step: "4", text: "Готово — уведомления будут приходить сюда" },
            ].map(s => (
              <div key={s.step} style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                <div style={{ width: 22, height: 22, borderRadius: "50%",
                  background: COLORS.accentGlow, border: `1px solid ${COLORS.accent}40`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 11, color: COLORS.accent, fontWeight: 700, flexShrink: 0 }}>
                  {s.step}
                </div>
                <span style={{ fontSize: 13, color: COLORS.textSecondary, paddingTop: 2 }}>
                  {s.text}
                </span>
              </div>
            ))}
          </div>

          {error && <Alert type="error">{error}</Alert>}

          {/* Ссылка для привязки */}
          {connectUrl ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div style={{ background: COLORS.bg, borderRadius: 8, padding: "10px 14px",
                border: `1px solid ${COLORS.accent}40`, display: "flex",
                justifyContent: "space-between", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 12, color: COLORS.accent,
                  fontFamily: "'Space Mono', monospace",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
                  {connectUrl}
                </span>
                <button onClick={copyUrl} style={{
                  background: "none", border: `1px solid ${COLORS.border}`,
                  borderRadius: 6, padding: "4px 10px", cursor: "pointer",
                  fontSize: 11, color: copied ? COLORS.green : COLORS.textMuted,
                  fontFamily: "'Space Mono', monospace", flexShrink: 0,
                  transition: "all 0.15s",
                }}>
                  {copied ? "✓ Скопировано" : "Копировать"}
                </button>
              </div>

              <a href={connectUrl} target="_blank" rel="noopener noreferrer" style={{
                display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                padding: "11px", borderRadius: 9, background: "#2AABEE",
                color: "#fff", fontWeight: 600, fontSize: 14, textDecoration: "none",
                boxShadow: "0 0 20px rgba(42,171,238,0.3)",
                transition: "opacity 0.15s",
              }}>
                ✈ Открыть в Telegram
              </a>

              <button onClick={handleConnect} style={{
                background: "none", border: "none", color: COLORS.textMuted,
                fontSize: 12, cursor: "pointer", textAlign: "center",
              }}>
                Сгенерировать новую ссылку
              </button>
            </div>
          ) : (
            <Button primary onClick={handleConnect} disabled={loading}>
              {loading ? <Spinner size={16} /> : "✈ Подключить Telegram"}
            </Button>
          )}
        </div>
      )}
    </Card>
  );
}

// ── Основная страница Settings ────────────────────────────────────────────────
export default function SettingsPage() {
  const { user, logout } = useAuthStore();
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    username: user?.username || "",
    explain_mode: user?.explain_mode || "senior",
  });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  function handle(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
    setSuccess(false); setError("");
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true); setError(""); setSuccess(false);
    try {
      await usersAPI.updateMe({
        full_name:    form.full_name    || undefined,
        username:     form.username     || undefined,
        explain_mode: form.explain_mode,
      });
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save");
    }
    setSaving(false);
  }

  return (
    <div style={{ padding: "32px 36px", maxWidth: 600, animation: "fade-in 0.3s ease" }}>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 26, fontWeight: 600, color: COLORS.textPrimary,
          letterSpacing: "-0.02em", marginBottom: 4 }}>Settings</h1>
        <div style={{ fontSize: 13, color: COLORS.textMuted }}>
          Signed in as <span style={{ color: COLORS.accent }}>{user?.email || user?.username}</span>
        </div>
      </div>

      {/* Profile */}
      <Card style={{ padding: 24, marginBottom: 16 }}>
        <div style={{ fontSize: 12, color: COLORS.accent, fontFamily: "'Space Mono', monospace",
          letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 18 }}>Profile</div>
        <form onSubmit={save} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Input label="Full Name" name="full_name" value={form.full_name} onChange={handle}
            placeholder="Your full name" />
          <Input label="Username" name="username" value={form.username} onChange={handle}
            placeholder="username" />
          <div>
            <div style={{ fontSize: 11, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace",
              textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>Email</div>
            <div style={{ fontSize: 14, color: COLORS.textSecondary, padding: "10px 13px",
              borderRadius: 8, background: COLORS.bg, border: `1px solid ${COLORS.border}` }}>
              {user?.email || "—"}
            </div>
          </div>
          {success && <Alert type="success">✓ Profile saved</Alert>}
          {error && <Alert type="error">{error}</Alert>}
          <Button primary type="submit" disabled={saving}>
            {saving ? <Spinner size={16} /> : "Save Profile"}
          </Button>
        </form>
      </Card>

      {/* AI Explain mode */}
      <Card style={{ padding: 24, marginBottom: 16 }}>
        <div style={{ fontSize: 12, color: COLORS.accent, fontFamily: "'Space Mono', monospace",
          letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 18 }}>
          AI Explanation Mode
        </div>
        <Select label="Default explanation mode" name="explain_mode"
          value={form.explain_mode} onChange={handle}>
          <option value="junior">Junior Dev — simple language, step by step</option>
          <option value="senior">Senior Dev — technical, concise, precise</option>
          <option value="ceo">CEO View — business impact only, no tech jargon</option>
        </Select>
        <div style={{ fontSize: 12, color: COLORS.textMuted, marginTop: 8 }}>
          Controls how AI explains incidents in notifications and dashboard.
        </div>
      </Card>

      {/* ✈ Telegram */}
      <TelegramBlock />

      {/* Account */}
      <Card style={{ padding: 24 }}>
        <div style={{ fontSize: 12, color: COLORS.accent, fontFamily: "'Space Mono', monospace",
          letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 18 }}>Account</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
            padding: "10px 14px", borderRadius: 8, background: COLORS.bg,
            border: `1px solid ${COLORS.border}` }}>
            <div>
              <div style={{ fontSize: 13, color: COLORS.textPrimary, marginBottom: 2 }}>Sign out</div>
              <div style={{ fontSize: 11, color: COLORS.textMuted }}>Sign out from all devices</div>
            </div>
            <Button small onClick={logout}>Sign Out</Button>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
            padding: "10px 14px", borderRadius: 8, background: `${COLORS.red}08`,
            border: `1px solid ${COLORS.red}25` }}>
            <div>
              <div style={{ fontSize: 13, color: COLORS.red, marginBottom: 2 }}>Delete account</div>
              <div style={{ fontSize: 11, color: COLORS.textMuted }}>Permanently delete account and all data</div>
            </div>
            <Button small danger onClick={() => window.confirm("Are you sure?") && usersAPI.deleteMe().then(logout)}>
              Delete
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}