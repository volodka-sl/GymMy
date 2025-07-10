from datetime import datetime, date, timedelta
from storage.models import ReminderGender
from storage.user_repository import UserRepository
from storage.user_program_repository import UserProgramRepository
from services.reminder_text_service import ReminderTextService
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from states import ChatStates
from keyboards.chat_keyboards import chat_back_kb

TARGET_HOUR = 6       # Время рассылки (по локальному времени пользователя)
TARGET_MINUTE = 0

class TrainingReminderService:
    def __init__(self, bot, reminder_text_service: ReminderTextService, storage):
        self._bot = bot
        self._reminder_text_service = reminder_text_service
        self._user_repo = UserRepository()
        self._program_repo = UserProgramRepository()
        self._storage = storage  # storage теперь явная зависимость

    def _get_today_program_users(self):
        users = self._user_repo.list_with_programs()
        today = datetime.utcnow().date()
        result = []
        now_utc = datetime.utcnow()
        for user in users:
            user_offset = user.tz_offset or 0
            local_time = now_utc + timedelta(hours=user_offset)
            if local_time.hour == TARGET_HOUR and local_time.minute == TARGET_MINUTE:
                # для этого пользователя сейчас время рассылки
                for program in user.programs:
                    for schedule in program.template.schedules:
                        if (local_time.weekday() + 1) == schedule.day_of_week:
                            result.append((user, program, program.template, user.tz_offset))
        return result

    async def send_today_reminders(self):
        """
        Отправляет мотивационные напоминания и переводит пользователей в воронку Gymmy.
        В каждом напоминании уже есть призыв к диалогу, дополнительное сообщение не отправляется.
        """
        users = self._get_today_program_users()
        today = date.today()
        sent_users = set()
        for user, program, template, tz_offset in users:
            if user.telegram_id in sent_users:
                continue
            gender = ReminderGender.female if user.sex == "женщина" else ReminderGender.male
            text = await self._reminder_text_service.get_or_generate_reminder(today, gender)
            msg_text = (
                f"{text}\n\n"
                f"Твоя тренировка: <b>{template.name}</b>"
            )
            await self._bot.send_message(
                chat_id=user.telegram_id,
                text=msg_text,
                parse_mode="HTML",
                reply_markup=chat_back_kb()
            )
            await self.start_reminder_dialog(user.telegram_id)
            sent_users.add(user.telegram_id)

    async def start_reminder_dialog(self, telegram_id: int):
        key = StorageKey(
            chat_id=telegram_id,
            user_id=telegram_id,
            bot_id=self._bot.id
        )
        state = FSMContext(self._storage, key)
        # Проверяем текущее состояние и историю
        cur_state = await state.get_state()
        data = await state.get_data()
        if cur_state != ChatStates.chatting:
            await state.set_state(ChatStates.chatting)
            await state.update_data(history=[])
