# services/plan_chat_service.py

import os
import json
import httpx

from services.gpt_workout_prompt import system_message
from services.gpt_plan_prompt import system_message as plan_system_message

class PlanChatService:
    """
    Сервис для генерации тренировок через ChatGPT (одна тренировка или план на неделю).
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_plan(self, user_payload: dict, exercises_payload: list[dict]) -> dict:
        """
        Запрос к OpenAI для создания одной тренировки (dict с name и plan).
        """
        user_content = json.dumps(user_payload, ensure_ascii=False)
        exercises_content = json.dumps(exercises_payload, ensure_ascii=False)

        messages = [
            system_message,
            {
                "role": "user",
                "content": (
                    f"Профиль пользователя: {user_content}\n"
                    f"Список упражнений (используй только эти названия!): {exercises_content}"
                )
            }
        ]

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.2,
            "max_tokens": 512,
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
            content = data["choices"][0]["message"]["content"].strip()

        try:
            plan_obj = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Некорректный формат плана: {content}")

        if not isinstance(plan_obj, dict) or "name" not in plan_obj or "plan" not in plan_obj:
            raise ValueError(f"Ответ от ChatGPT не содержит нужные поля: {content}")

        return plan_obj

    async def generate_full_plan(self, user_payload: dict, exercises_payload: list[dict]) -> list[dict]:
        """
        Запрос к OpenAI для создания плана на неделю (list из дней с упражнениями).
        """
        user_content = json.dumps(user_payload, ensure_ascii=False)
        exercises_content = json.dumps(exercises_payload, ensure_ascii=False)

        messages = [
            plan_system_message,
            {
                "role": "user",
                "content": (
                    f"Профиль пользователя: {user_content}\n"
                    f"Список упражнений (используй только эти названия!): {exercises_content}\n"
                    f"Пожелания: {user_payload.get('wish', '')}\n"
                    f"Дни недели (свободный ввод): {user_payload.get('days_text', '')}\n"
                    "Верни массив дней недели с упражнениями в строгом JSON-формате!"
                )
            }
        ]

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.2,
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                json=payload,
                headers=self.headers,
                timeout=40.0
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()

        # Иногда GPT возвращает ```json ... ```
        if content.startswith("```json"):
            content = content.removeprefix("```json").removesuffix("```").strip()

        try:
            plan = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Некорректный формат плана: {content}")

        if not isinstance(plan, list) or not plan:
            raise ValueError(f"Ответ от ChatGPT не содержит массив дней: {content}")

        # Лёгкая валидация структуры каждого дня
        for day in plan:
            if "day" not in day or "exercises" not in day or not isinstance(day["exercises"], list):
                raise ValueError(f"Некорректный формат дня: {json.dumps(day, ensure_ascii=False)}")

        return plan
