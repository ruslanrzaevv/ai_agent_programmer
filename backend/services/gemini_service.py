import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-3.1-pro')

def analyze_incident(logs: str, commits: str):
    prompt = f"""
    You are an elite AI DevOps Incident Response Agent.

    Analyze the production incident.

    LOGS:
    {logs}

    RECENT COMMITS:
    {commits}

    Tasks:
    1. Find root cause
    2. Explain issue
    3. Suggest fix
    4. Generate corrected code
    5. Generate commit message
    6. Give confidence score

    Respond in this JSON format:

    {{
      "root_cause": "...",
      "explanation": "...",
      "fix": "...",
      "corrected_code": "...",
      "commit_message": "...",
      "confidence": "..."
    }}
    """

    response = model.generate_content(prompt)
    return response.text