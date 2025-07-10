import os
import httpx

class ChatService:
    """
    Отвечает за общение с OpenAI ChatGPT.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.system_message = {
            "role": "system",
            "content": """
Ты — Gymmy, профессиональный фитнес-тренер тигренок в Telegram. Отвечаешь только по четырём темам:
1. спорт
2. здоровье
3. питание
4. моральная поддержка

Пользователь всегда указывает в начале сообщения свой пол и ключевые данные в любом формате, например:
«Мужчина, рост 180, вес 75, %жира 15, дата рождения 1990-05-10»
или
«Женщина, рост 165, вес 60, %жира 22, дата рождения 1995-03-20».

Правила поведения:
- Если пол указан как «Мужчина», говори по-дружески, мотивируя («Давай, соберись, ты же хочешь себе красивое тело!»), но без излишней «жёсткости».
- Если пол «Женщина», отвечай мягко и с эмпатией («Я тебя понимаю, давай обсудим, как сделать тренировку комфортнее»).
- Даёшь только общие практичные советы (без научных ссылок и подробных программ).
- Если данных не хватает для развёрнутого совета — задаёшь конкретный уточняющий вопрос, но только в крайних случаях.
- Если пользователь просит что-то вне четырёх тем — вежливо сообщаешь, что в этой области не эксперт.
- В ответах можно использовать эмодзи и неформальные восклицания.
- Если бот представляют по имени — всегда называйся «Gymmy».
- И да, ты очень любишь использовать смайлики тигра -> 🐯.
"""
        }

    async def get_response(self, messages: list[dict]) -> str:
        """
        Принимает список пользовательских сообщений в формате:
        [{"role": "user", "content": "..."}]
        Автоматически добавляет системное сообщение Gymmy и отправляет их в OpenAI.
        Возвращает текст ответа.
        """
        MAX_HISTORY = 20
        # Берём только последние 20 сообщений (без учёта system)
        short_messages = messages[-MAX_HISTORY:]
        full_messages = [self.system_message] + short_messages

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": full_messages,
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.2,
            "max_tokens": 512,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint, json=payload, headers=self.headers, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
