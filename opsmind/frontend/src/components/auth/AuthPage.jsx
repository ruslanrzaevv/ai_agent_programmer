import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { COLORS } from "../../utils/constants";
import { Button, Alert, Input } from "../ui";
import { useAuthStore } from "../../store/authStore";
import { authAPI } from "../../services/api";

/**
 * Шаги:
 * "form"        — форма логина или регистрации
 * "verify_email" — введи код из письма (email)
 * "verify_phone" — введи код из SMS (телефон)
 */

export default function AuthPage() {
  const [tab, setTab]   = useState("login");   // login | register
  const [step, setStep] = useState("form");    // form | verify_email | verify_phone

  const [form, setForm] = useState({
    email: "", password: "", username: "",
    full_name: "", phone: "",
  });

  // код верификации
  const [code, setCode]               = useState("");
  const [codeLoading, setCodeLoading] = useState(false);
  const [codeError, setCodeError]     = useState("");
  const [resendCooldown, setResendCooldown] = useState(0);

  const navigate = useNavigate();
  const { login, register, loading, error, clearError } = useAuthStore();

  // ── helpers ──────────────────────────────────────────────────────────────────

  function handle(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
    clearError();
  }

  // Запустить таймер кулдауна кнопки «Отправить повторно»
  function startCooldown(sec = 60) {
    setResendCooldown(sec);
    const t = setInterval(() => {
      setResendCooldown(s => {
        if (s <= 1) { clearInterval(t); return 0; }
        return s - 1;
      });
    }, 1000);
  }

  // ── submit формы ─────────────────────────────────────────────────────────────

  async function submit(e) {
    e.preventDefault();

    if (tab === "login") {
      // Логин по email или телефону
      const identifier = form.email || form.phone;
      const res = await login(identifier, form.password);
      if (res.ok) navigate("/");
      return;
    }

    // Регистрация
    const res = await register({
      email:         form.email    || undefined,
      phone:         form.phone    || undefined,
      username:      form.username || undefined,
      full_name:     form.full_name || undefined,
      password:      form.password,
      auth_provider: "email",
    });

    if (!res.ok) return;

    if (form.email) {
      setStep("verify_email");
      startCooldown(60);
    } else if (form.phone) {
      setStep("verify_phone");
      startCooldown(60);
    } else {
      navigate("/");
    }
  }

  // ── верификация кода ──────────────────────────────────────────────────────────

  async function verifyCode(e) {
    console.log('Verify click')
    e.preventDefault();
    if (code.length !== 6) return;
  
    setCodeLoading(true);
    setCodeError("");
  
    const target = step === "verify_email" ? form.email : form.phone;
  
    try {
      console.log("STEP 1");
    
      await authAPI.verify(target, code, "register");
    
      console.log("STEP 2");
    
      const identifier = form.email || form.phone;
    
      console.log("STEP 3");
    
      const res = await login(identifier, form.password);
    
      console.log("LOGIN RESULT", res);
    
      if (res.ok) {
        navigate("/");
      }
    } catch (err) {
      console.error("FULL ERROR:", err);
    
      setCodeError(String(err));
    }finally {
      setCodeLoading(false);
    }
  }

  // ── повторная отправка ────────────────────────────────────────────────────────

  async function resendCode() {
    if (resendCooldown > 0) return;
    const target = step === "verify_email" ? form.email : form.phone;
    try {
      await authAPI.sendCode(target, "register");
      startCooldown(60);
      setCodeError("");
    } catch (err) {
      setCodeError(err.response?.data?.detail || "Не удалось отправить код");
    }
  }

  // ── tabs helper ───────────────────────────────────────────────────────────────

  function switchTab(t) {
    setTab(t);
    setStep("form");
    setCode("");
    setCodeError("");
    clearError();
  }

  // ── стили ─────────────────────────────────────────────────────────────────────

  const isVerifyStep = step === "verify_email" || step === "verify_phone";
  const verifyTarget = step === "verify_email" ? form.email : form.phone;
  const verifyIcon   = step === "verify_email" ? "📬" : "📱";
  const verifyLabel  = step === "verify_email"
    ? "Проверьте почту"
    : "Проверьте телефон";
  const verifyHint   = step === "verify_email"
    ? `Мы отправили 6-значный код на `
    : `Мы отправили SMS с кодом на `;

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex", alignItems: "center", justifyContent: "center",
      background: COLORS.bg, padding: 20,
      backgroundImage: `radial-gradient(ellipse 60% 50% at 50% 0%, rgba(79,142,247,0.08) 0%, transparent 70%)`,
    }}>
      {/* Сетка фона */}
      <div style={{
        position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none", opacity: 0.35,
        backgroundImage: `
          linear-gradient(${COLORS.border}60 1px, transparent 1px),
          linear-gradient(90deg, ${COLORS.border}60 1px, transparent 1px)
        `,
        backgroundSize: "48px 48px",
      }} />

      <div style={{
        position: "relative", zIndex: 1,
        width: "100%", maxWidth: 420,
        animation: "slide-in 0.35s ease",
      }}>
        {/* Логотип */}
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 9, background: COLORS.accent,
              display: "flex", alignItems: "center", justifyContent: "center",
              boxShadow: `0 0 22px ${COLORS.accent}60`, fontSize: 18,
            }}>⚡</div>
            <span style={{
              fontFamily: "'Space Mono', monospace", fontSize: 22, fontWeight: 700,
              color: COLORS.textPrimary, letterSpacing: "-0.02em",
            }}>OpsMind</span>
          </div>
          <div style={{ fontSize: 13, color: COLORS.textMuted }}>
            AI-powered incident monitoring
          </div>
        </div>

        {/* Карточка */}
        <div style={{
          background: COLORS.surface, border: `1px solid ${COLORS.border}`,
          borderRadius: 14, padding: 28, boxShadow: "0 0 40px rgba(0,0,0,0.4)",
        }}>

          {/* ═══ ШАГ: ВЕРИФИКАЦИЯ (email или phone) ═══ */}
          {isVerifyStep && (
            <form onSubmit={verifyCode} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {/* Иконка + заголовок */}
              <div style={{ textAlign: "center", marginBottom: 4 }}>
                <div style={{ fontSize: 36, marginBottom: 12 }}>{verifyIcon}</div>
                <div style={{
                  fontSize: 16, fontWeight: 600, color: COLORS.textPrimary, marginBottom: 8,
                }}>{verifyLabel}</div>
                <div style={{ fontSize: 13, color: COLORS.textMuted, lineHeight: 1.5 }}>
                  {verifyHint}
                  <span style={{ color: COLORS.accent, fontWeight: 500 }}>{verifyTarget}</span>
                </div>
              </div>

              {/* Поле кода */}
              <div>
                <div style={{
                  fontSize: 11, color: COLORS.textMuted,
                  fontFamily: "'Space Mono', monospace",
                  textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8,
                }}>
                  Код подтверждения
                </div>
                <input
                  value={code}
                  onChange={e => {
                    const v = e.target.value.replace(/\D/g, "").slice(0, 6);
                    setCode(v);
                    setCodeError("");
                  }}
                  placeholder="• • • • • •"
                  maxLength={6}
                  inputMode="numeric"
                  autoFocus
                  style={{
                    width: "100%",
                    padding: "14px 16px",
                    borderRadius: 10,
                    background: COLORS.bg,
                    border: `1px solid ${codeError ? COLORS.red : code.length === 6 ? COLORS.green : COLORS.border}`,
                    color: COLORS.textPrimary,
                    fontSize: 28,
                    fontFamily: "'Space Mono', monospace",
                    fontWeight: 700,
                    textAlign: "center",
                    letterSpacing: "0.4em",
                    outline: "none",
                    transition: "border-color 0.15s",
                  }}
                />
                {/* Индикатор прогресса */}
                <div style={{ display: "flex", gap: 4, marginTop: 8, justifyContent: "center" }}>
                  {[0,1,2,3,4,5].map(i => (
                    <div key={i} style={{
                      width: 28, height: 3, borderRadius: 2,
                      background: i < code.length ? COLORS.accent : COLORS.border,
                      transition: "background 0.15s",
                    }} />
                  ))}
                </div>
              </div>

              {/* Ошибка */}
              {codeError && <Alert type="error">{codeError}</Alert>}

              {/* Кнопка верификации */}
              <Button
                type="submit" primary
                disabled={codeLoading || code.length < 6}
                style={{ width: "100%" }}
              >
                {codeLoading ? "Проверяем..." : "Подтвердить →"}
              </Button>

              {/* Повторная отправка */}
              <div style={{ textAlign: "center" }}>
                {resendCooldown > 0 ? (
                  <span style={{ fontSize: 12, color: COLORS.textMuted }}>
                    Отправить повторно через{" "}
                    <span style={{ color: COLORS.accent, fontFamily: "'Space Mono', monospace" }}>
                      {resendCooldown}s
                    </span>
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={resendCode}
                    style={{
                      background: "none", border: "none",
                      color: COLORS.accent, fontSize: 12,
                      cursor: "pointer", textDecoration: "underline",
                      fontFamily: "'DM Sans', sans-serif",
                    }}
                  >
                    Не получили код? Отправить повторно
                  </button>
                )}
              </div>

              {/* Вернуться назад */}
              <button
                type="button"
                onClick={() => { setStep("form"); setCode(""); setCodeError(""); }}
                style={{
                  background: "none", border: "none",
                  color: COLORS.textMuted, fontSize: 12,
                  cursor: "pointer", textAlign: "center",
                  fontFamily: "'DM Sans', sans-serif",
                }}
              >
                ← Назад
              </button>
            </form>
          )}

          {/* ═══ ШАГ: ФОРМА (login / register) ═══ */}
          {!isVerifyStep && (
            <>
              {/* Tab switcher */}
              <div style={{
                display: "flex", background: COLORS.bg,
                borderRadius: 9, padding: 4, marginBottom: 24,
                border: `1px solid ${COLORS.border}`,
              }}>
                {[["login", "Войти"], ["register", "Регистрация"]].map(([t, label]) => (
                  <button
                    key={t}
                    onClick={() => switchTab(t)}
                    style={{
                      flex: 1, padding: "8px 0", borderRadius: 7,
                      border: "none", cursor: "pointer",
                      fontFamily: "'Space Mono', monospace",
                      fontSize: 11, fontWeight: 700,
                      letterSpacing: "0.08em", textTransform: "uppercase",
                      transition: "all 0.15s",
                      background: tab === t ? COLORS.surface : "transparent",
                      color: tab === t ? COLORS.textPrimary : COLORS.textMuted,
                      boxShadow: tab === t ? "0 1px 8px rgba(0,0,0,0.4)" : "none",
                    }}
                  >{label}</button>
                ))}
              </div>

              <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 13 }}>

                {/* Поля только для регистрации */}
                {tab === "register" && (
                  <>
                    <Input
                      name="full_name" label="Полное имя"
                      placeholder="Иван Иванов"
                      value={form.full_name} onChange={handle}
                    />
                    <Input
                      name="username" label="Имя пользователя"
                      placeholder="ivan"
                      value={form.username} onChange={handle}
                    />
                    <Input
                      name="phone" label="Телефон (для SMS кода)"
                      placeholder="+998901234567"
                      value={form.phone} onChange={handle}
                    />
                    <div style={{
                      fontSize: 11, color: COLORS.textMuted,
                      background: COLORS.bg,
                      border: `1px solid ${COLORS.border}`,
                      borderRadius: 7, padding: "8px 12px",
                      lineHeight: 1.5,
                    }}>
                      💡 Если указать email — код придёт на почту.<br />
                      Если указать только телефон — код придёт по SMS.
                    </div>
                  </>
                )}

                {/* Email */}
                <Input
                  name="email" type="email"
                  label={tab === "login" ? "Email или телефон" : "Email"}
                  placeholder={tab === "login" ? "email или +998..." : "you@company.com"}
                  value={form.email} onChange={handle}
                  required={tab === "login"}
                />

                {/* Пароль */}
                <Input
                  name="password" type="password"
                  label="Пароль" placeholder="••••••••"
                  value={form.password} onChange={handle}
                  required
                />

                {/* Ошибка */}
                {error && <Alert type="error">{error}</Alert>}

                {/* Кнопка */}
                <Button
                  type="submit" primary
                  disabled={loading}
                  style={{ width: "100%", marginTop: 4 }}
                >
                  {loading
                    ? "Загрузка..."
                    : tab === "login"
                      ? "Войти →"
                      : "Создать аккаунт →"
                  }
                </Button>

                {/* Google (опционально) */}
                <div style={{ textAlign: "center", marginTop: 4 }}>
                  <span style={{ fontSize: 12, color: COLORS.textMuted }}>или </span>
                  <button
                    type="button"
                    style={{
                      background: "none", border: "none",
                      color: COLORS.accent, fontSize: 12,
                      cursor: "pointer", fontFamily: "'DM Sans', sans-serif",
                    }}
                  >
                    продолжить через Google
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}