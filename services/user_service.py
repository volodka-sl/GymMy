from datetime import datetime, timezone
from storage.user_repository import UserRepository
from storage.models import User

class UserService:
    def __init__(self, telegram_id: int):
        self.telegram_id = telegram_id
        self._repo = UserRepository()

    def exists(self) -> bool:
        return self._repo.get_by_telegram_id(self.telegram_id) is not None

    def get_profile(self) -> User | None:
        """
        Возвращает профиль пользователя по telegram_id.
        """
        return self._repo.get_by_telegram_id(self.telegram_id)

    def get_or_create_profile(self, **data) -> User:
        """
        Создаёт или обновляет профиль. Гарантирует,
        что при INSERT и UPDATE поле tz_offset никогда не NULL.
        """
        session = self._repo._session
        user = self._repo.get_by_telegram_id(self.telegram_id)

        # Вычисляем текущее смещение локального времени от UTC в часах
        now_local = datetime.now(timezone.utc).astimezone()
        offset_hours = int(now_local.utcoffset().total_seconds() // 3600)

        if not user:
            # При создании сразу передаём tz_offset
            user = User(
                telegram_id=self.telegram_id,
                tz_offset=offset_hours,
                **data
            )
            session.add(user)
        else:
            # При обновлении тоже обновляем tz_offset на текущее
            for field, val in data.items():
                setattr(user, field, val)
            user.tz_offset = offset_hours

        session.commit()
        session.refresh(user)
        return user

    def close(self):
        self._repo.close()
