# storage/promo_repository.py
from storage.db import SessionLocal
from storage.models import PromoCode, UserPromoCode
from datetime import date

class PromoRepository:
    def __init__(self):
        self._session = SessionLocal()

    def get_promo(self, code: str) -> PromoCode | None:
        return (
            self._session
            .query(PromoCode)
            .filter(PromoCode.code == code)
            .one_or_none()
        )

    def user_redeemed(self, user_id: int, promo_id: int) -> bool:
        return (
            self._session
            .query(UserPromoCode)
            .filter_by(user_id=user_id, promo_code_id=promo_id)
            .first()
            is not None
        )

    def total_redemptions(self, promo_id: int) -> int:
        return (
            self._session
            .query(UserPromoCode)
            .filter_by(promo_code_id=promo_id)
            .count()
        )

    def record_redemption(self, user_id: int, promo_id: int) -> None:
        upc = UserPromoCode(user_id=user_id, promo_code_id=promo_id)
        self._session.add(upc)
        self._session.commit()

    def close(self):
        self._session.close()
