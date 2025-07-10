# services/reminder_text_service.py

from datetime import date
from storage.reminder_text_repository import ReminderTextRepository
from storage.models import ReminderGender
import asyncio

# Можно задать параметры генерации здесь:
MALE_PROMPT = (
    "Сгенерируй мотивирующее, дружелюбное и неформальное напоминание о тренировке для мужчины. "
    "В конце обязательно задай интересный, неформальный вопрос о его сегодняшнем настроении, целях или тренировке, чтобы он захотел ответить Gymmy. "
    "Вопрос может быть простым или с юмором: например, 'Как настрой на сегодняшнюю тренировку?' или 'Какую мышцу хочешь прокачать больше всего сегодня?' "
    "Пример: 'Вперёд за бицепсом! Кстати, как настрой — есть боевой дух?' "
    "Ответ только в виде мотивационного текста и вопроса, 1-2 предложения, не пиши лишних пояснений. Не используй кавычки в начале и конце напоминания."
)

FEMALE_PROMPT = (
    "Сгенерируй позитивное, вдохновляющее напоминание о тренировке для женщины. "
    "В конце обязательно задай приятный, тёплый вопрос о настроении или планах на тренировку, чтобы ей захотелось ответить Gymmy. "
    "Вопрос может быть о мотивации, самочувствии или любимых упражнениях: например, 'Что тебе хочется сегодня проработать больше всего?' или 'Какое настроение на тренировку?' "
    "Пример: 'Сегодня твой день блистать! А на какую мышцу сегодня хочешь сделать акцент?' "
    "Ответ только в виде мотивационного текста и вопроса, 1-2 предложения, не пиши лишних пояснений. Не используй кавычки в начале и конце напоминания."
)

class ReminderTextService:
    """
    Сервис генерации и хранения мотивационных напоминалок по полу и дате.
    """
    def __init__(self, gpt_service):
        self._gpt = gpt_service  # любой сервис обращения к ChatGPT (инъекция зависимости)
        self._repo = ReminderTextRepository()

    async def get_or_generate_reminder(self, day: date, gender: ReminderGender) -> str:
        # 1. Проверяем, есть ли напоминание в БД
        reminder = self._repo.get_by_date_and_gender(day, gender)
        if reminder:
            return reminder.text

        # 2. Генерируем новое через GPT
        prompt = MALE_PROMPT if gender == ReminderGender.male else FEMALE_PROMPT
        text = await self._gpt.generate_reminder_text(prompt)
        text = text.strip().replace('\n', ' ')

        # 3. Сохраняем результат
        self._repo.save(day, gender, text)
        return text

    async def generate_for_both(self, day: date):
        from storage.models import ReminderGender
        result = {}
        for gender in (ReminderGender.male, ReminderGender.female):
            exist = self._repo.get_by_date_and_gender(day, gender)
            if exist:
                result[gender.value] = exist.text
            else:
                result[gender.value] = await self.get_or_generate_reminder(day, gender)
        return result
