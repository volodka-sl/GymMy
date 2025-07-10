import os
import httpx

class GptReminderService:
    """
    Сервис генерации текстов через OpenAI GPT (gpt-3.5-turbo).
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_reminder_text(self, prompt: str) -> str:
        messages = [
            {"role": "system", "content": "Ты — дружелюбный, мотивирующий фитнес-ассистент Gymmy."},
            {"role": "user", "content": prompt}
        ]
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.85,        # Чуть выше креативность для напоминалок
            "top_p": 0.95,
            "max_tokens": 128,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                json=payload,
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
