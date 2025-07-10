from storage.db import SessionLocal
from storage.models import User, UserProgram, ProgramTemplate
from sqlalchemy.exc import NoResultFound

class UserRepository:
    def __init__(self):
        self._session = SessionLocal()

    def get_by_id(self, user_id):
        return self._session.query(User).filter_by(user_id=user_id).one_or_none()

    def list_with_programs(self):
        """
        Возвращает всех пользователей с их активными тренировочными программами и шаблонами.
        """
        return (
            self._session
            .query(User)
            .join(UserProgram, User.user_id == UserProgram.user_id)
            .join(ProgramTemplate, UserProgram.template_id == ProgramTemplate.template_id)
            .options(
            )
            .all()
        )

    def get_by_telegram_id(self, tg_id: int) -> User | None:
        try:
            return (
                self._session
                    .query(User)
                    .filter(User.telegram_id == tg_id)
                    .one()
            )
        except NoResultFound:
            return None

    def save(self, tg_id: int, **data) -> User:
        user = self.get_by_telegram_id(tg_id)
        if not user:
            user = User(telegram_id=tg_id, **data)
            self._session.add(user)
        else:
            for field, val in data.items():
                setattr(user, field, val)
        self._session.commit()
        return user

    def close(self):
        self._session.close()
