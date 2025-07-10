from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta

from storage.subscription_repository import SubscriptionRepository

class SubscriptionService:
    def __init__(self, telegram_id: int):
        self._repo         = SubscriptionRepository()
        self._telegram_id = telegram_id

    def trial(self) -> datetime:
        """
        Открыть пробную подписку на 7 суток в часовом поясе пользователя.
        Пробная неделя доступна только единожды.
        Возвращает дату и время окончания в его локальном UTC-офсете.
        """
        user = self._repo.get_user(self._telegram_id)
        if not user:
            raise ValueError("Пользователь не найден. Сначала пройдите регистрацию.")

        # Если у пользователя уже есть любая подписка — проба недоступна
        if user.subscriptions:
            raise ValueError("У вас уже была / есть активная подписка.")

        # Таймзона пользователя
        tz_offset = timedelta(hours=user.tz_offset)
        user_tz   = timezone(tz_offset)

        # Локальное текущее время
        now_local = datetime.now(user_tz)
        end_local = now_local + timedelta(days=7)

        # Сохраняем пробную подписку; по вашему триггеру создадутся напоминания
        self._repo.create_subscription(
            user_id  = user.user_id,
            start_ts = now_local,
            end_ts   = end_local
        )
        return end_local

    def subscribe_month(self, months: int = 1) -> datetime:
        """
        Открыть платную подписку на `months` месяцев
        в часовом поясе пользователя.
        Возвращает datetime конца подписки (локальный).
        """
        user = self._repo.get_user(self._telegram_id)
        if not user:
            raise ValueError("Пользователь не найден. Сначала пройдите регистрацию.")

        # Таймзона пользователя
        tz_off = timedelta(hours=user.tz_offset)
        user_tz = timezone(tz_off)

        now_local = datetime.now(user_tz)
        end_local = now_local + relativedelta(months=months)

        # создаём подписку и сразу триггером сформируются напоминания
        self._repo.create_subscription(
            user_id=user.user_id,
            start_ts=now_local,
            end_ts=end_local
        )
        return end_local

    def has_active(self) -> bool:
        """
        Возвращает True, если у пользователя уже есть активная подписка в текущий момент UTC.
        """
        user = self._repo.get_user(self._telegram_id)
        if not user:
            return False
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        for sub in user.subscriptions:
            # sub.start_ts и sub.end_ts уже хранятся с таймзоной
            if sub.start_ts <= now_utc <= sub.end_ts:
                return True
        return False

    def current_end(self) -> datetime | None:
        """
        Если есть активная подписка — возвращает её время окончания (UTC-aware), иначе None.
        """
        user = self._repo.get_user(self._telegram_id)
        if not user:
            return None
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        for sub in user.subscriptions:
            if sub.start_ts <= now_utc <= sub.end_ts:
                return sub.end_ts
        return None

    def close(self):
        self._repo.close()
