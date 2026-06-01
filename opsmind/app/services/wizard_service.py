import asyncio
import json
from google import genai
from google.genai.errors import ServerError

from app.core.config import settings


class SetupWizardService:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        ) 

    async def ask(
        self,
        category: str,
        message: str,
    ):
        print('STEP 1')

        prompt = f"""
        Ты OpsMind AI Setup Assistant.

        Отвечай ТОЛЬКО JSON.

        Формат:

        {{
        "answer": "текст ответа",
        "suggested_values": {{}}
        }}

        Правила:

        1. Если пользователь пишет:
        "docker на том же сервере"

        Ответ:

        {{
        "answer": "TLS не нужен. Используйте unix socket.",
        "suggested_values": {{
            "docker_engine_url": "unix:///var/run/docker.sock",
            "docker_tls_enabled": false
        }}
        }}

        2. Если пользователь пишет:
        "docker на отдельном VPS"

        Ответ:

        {{
        "answer": "Используйте TLS для безопасного подключения.",
        "suggested_values": {{
            "docker_engine_url": "tcp://YOUR_SERVER_IP:2376",
            "docker_tls_enabled": true
        }}
        }}

        3. Если пользователь спрашивает про GitLab:

        {{
        "answer": "Создайте Personal Access Token в GitLab.",
        "suggested_values": {{
            "gitlab_url": "https://gitlab.com"
        }}
        }}

        4. Если данных недостаточно —
        задай уточняющий вопрос.

        Никакого markdown.
        Никаких пояснений вне JSON.
        """

        print('STEP 2')

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{prompt}\n\nПользователь: {message}"
        )

        print('STEP 3')

        return response.text
    

    async def analyze(
    self,
    form_data: dict,
):
        prompt = f"""
    Проверь конфигурацию OpsMind.

    Конфигурация:

    {json.dumps(form_data, indent=2)}

    Найди:

    - проблемы безопасности
    - отсутствующие настройки
    - ошибки Docker
    - ошибки GitLab
    - проблемы уведомлений

    Верни ТОЛЬКО JSON.
    НЕ используй markdown.
    НЕ используй ```json.
    Верни только чистый JSON объект.

    Формат:

    {{
    "score": 0,
    "status": "critical",
    "summary": "",
    "issues": [],
    "recommendations": []
    }}
    """

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )

                return response.text

            except ServerError:
                if attempt < 2:
                    await asyncio.sleep(2)
                    continue

                return json.dumps({
                    "score": 0,
                    "status": "warning",
                    "summary": "Gemini временно перегружен",
                    "issues": [
                        "Не удалось получить ответ от Gemini"
                    ],
                    "recommendations": [
                        "Повторите анализ через несколько секунд"
                    ]
                })