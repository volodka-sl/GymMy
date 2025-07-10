from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple

from storage.promo_repository import PromoRepository
from storage.subscription_repository import SubscriptionRepository
from sqlalchemy.exc import NoResultFound

class PromoResult(NamedTuple):
    type: str                # 'free_days' | 'discount_percent' | 'discount_fixed'
    value: str | Decimal     # для free_days — строка с датой окончания, для скидок — новая цена
    description: str         # описание промокода

class PromoService:
    def __init__(self, telegram_id: int):
        self._promo_repo = PromoRepository()
        self._sub_repo   = SubscriptionRepository()
        self._user       = self._sub_repo.get_user(telegram_id)
        if not self._user:
            raise ValueError("Сначала пройдите регистрацию (/start).")

    def apply_code(
        self,
        code_str: str,
        original_amount: Decimal | None = None
    ) -> PromoResult:
        promo = self._promo_repo.get_promo(code_str)
        if not promo:
            raise ValueError("Промокод не найден.")

        today = datetime.now(timezone.utc).date()
        if promo.valid_from and today < promo.valid_from:
            raise ValueError("Промокод ещё не активен.")
        if promo.valid_to   and today > promo.valid_to:
            raise ValueError("Срок действия промокода истёк.")

        if promo.usage_limit is not None and \
           self._promo_repo.total_redemptions(promo.id) >= promo.usage_limit:
            raise ValueError("Промокод больше не доступен.")

        if self._promo_repo.user_redeemed(self._user.user_id, promo.id):
            raise ValueError("Вы уже использовали этот промокод.")

        # --- free_days ---
        if promo.type == 'free_days':
            if not promo.free_days or promo.free_days <= 0:
                raise ValueError("Неверное значение бесплатных дней в промокоде.")
            tz = timezone(timedelta(hours=self._user.tz_offset))
            now_local = datetime.now(tz)
            end_local = now_local + timedelta(days=promo.free_days)

            # создаём подписку
            self._sub_repo.create_subscription(
                user_id  = self._user.user_id,
                start_ts = now_local,
                end_ts   = end_local
            )

            # фиксируем использование
            self._promo_repo.record_redemption(self._user.user_id, promo.id)

            end_str = end_local.strftime("%d.%m.%Y %H:%M")
            return PromoResult('free_days', end_str, promo.description or "")

        # --- скидки ---
        if original_amount is None:
            raise ValueError("Для этого промокода нужно указывать сумму покупки.")

        # процентная скидка
        if promo.type == 'discount_percent':
            if promo.discount_pct is None:
                raise ValueError("Неверное значение процента в промокоде.")
            factor    = (Decimal(100) - promo.discount_pct) / Decimal(100)
            new_price = (original_amount * factor) \
                        .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # фиксированная скидка
        elif promo.type == 'discount_fixed':
            if promo.discount_amt is None:
                raise ValueError("Неверное значение суммы скидки в промокоде.")
            new_price = (original_amount - promo.discount_amt) \
                        .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if new_price < 0:
                new_price = Decimal('0.00')

        else:
            raise ValueError("Этот тип промокода пока не поддерживается.")

        # фиксируем использование скидочного кода
        self._promo_repo.record_redemption(self._user.user_id, promo.id)

        return PromoResult(promo.type, new_price, promo.description or "")

    def close(self):
        self._promo_repo.close()
        self._sub_repo.close()
