

from google import genai

client = genai.Client(
    api_key="AIzaSyC0YmXgz_iP8zmfq07opJxVYAGhKgJYefo"
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=""" Что такое питон
        
    """
)

print(response.text)