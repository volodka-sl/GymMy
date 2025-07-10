from datetime import datetime
from storage.db import SessionLocal
from storage.models import UserSubscription, User
from sqlalchemy.exc import NoResultFound

class SubscriptionRepository:
    def __init__(self):
        self._session = SessionLocal()

    def get_user(self, telegram_id: int) -> User:
        try:
            return self._session.query(User).filter_by(telegram_id=telegram_id).one()
        except NoResultFound:
            return None

    def get_by_id(self, subscription_id):
        return self._session.query(UserSubscription).filter_by(subscription_id=subscription_id).one_or_none()

    def create_subscription(self, user_id: int, start_ts: datetime, end_ts: datetime) -> UserSubscription:
        sub = UserSubscription(user_id=user_id, start_ts=start_ts, end_ts=end_ts)
        self._session.add(sub)
        self._session.commit()
        # после коммита по нашему триггеру отпушкаются две строки в subscription_reminder
        return sub

    def close(self):
        self._session.close()
