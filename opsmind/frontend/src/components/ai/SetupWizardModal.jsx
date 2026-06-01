import { useState } from "react";
import { aiAPI } from "../../services/api";
import { Button, Card, Spinner } from "../ui";
import { COLORS } from "../../utils/constants";

export default function SetupWizardModal({
  category,
  onClose,
  onApply,
}) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Привет! Я помогу настроить Docker, GitLab и TLS.",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    if (!input.trim()) return;

    const userMessage = {
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const { data } = await aiAPI.setupWizard(
        category,
        input
      );

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
        },
      ]);

      if (
        data.suggested_values &&
        Object.keys(data.suggested_values).length
      ) {
        onApply(data.suggested_values);
      }

      setInput("");
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Ошибка Gemini",
        },
      ]);
    }

    setLoading(false);
  }

  return (
    <Card
      style={{
        position: "fixed",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        width: 700,
        height: 600,
        zIndex: 9999,
        padding: 24,
      }}
    >
      <h2>🤖 OpsMind Setup Assistant</h2>

      <div
        style={{
          height: 420,
          overflowY: "auto",
          marginTop: 20,
          marginBottom: 20,
          border: `1px solid ${COLORS.border}`,
          borderRadius: 8,
          padding: 12,
        }}
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: 12,
            }}
          >
            <b>
              {msg.role === "user"
                ? "Вы"
                : "OpsMind AI"}
              :
            </b>{" "}
            {msg.content}
          </div>
        ))}
      </div>

      <div
        style={{
          display: "flex",
          gap: 10,
        }}
      >
        <input
          value={input}
          onChange={(e) =>
            setInput(e.target.value)
          }
          placeholder="Например: Docker стоит на том же VPS..."
          style={{
            flex: 1,
            padding: 12,
          }}
        />

        <Button
          primary
          onClick={sendMessage}
          disabled={loading}
        >
          {loading ? (
            <Spinner size={16} />
          ) : (
            "Отправить"
          )}
        </Button>
      </div>

      <div
        style={{
          marginTop: 10,
          display: "flex",
          justifyContent: "flex-end",
        }}
      >
        <Button onClick={onClose}>
          Закрыть
        </Button>
      </div>
    </Card>
  );
}