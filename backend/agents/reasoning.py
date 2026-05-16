import json 

def parse_ai_response(response_text: str):
    try:
        cleaned = response_text.replace("```json", "").replace("```", "")
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "root_cause": "Parsing failed",
            "explanation": response_text,
            "fix": "",
            "corrected_code": "",
            "commit_message": "",
            "confidence": "0%"
        }