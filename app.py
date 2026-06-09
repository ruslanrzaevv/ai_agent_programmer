from google import genai

client = genai.Client(
    api_key="AIzaSyA8mS4vSSVUzxl9RNlOWwW3dNdAqmhUBPc"
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=""" Что такое питон
        
    """
)

print(response.text)