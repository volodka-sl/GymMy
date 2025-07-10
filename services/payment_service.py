from decimal import Decimal
from urllib import parse
import hashlib

import asyncio

from handlers.configs.robokassa_config import RobokassaConfig
from storage.payment_repository import PaymentRepository
from storage.user_repository import UserRepository

class PaymentService:
    def __init__(self, telegram_id: int):
        # 1) Инициализируем оба репозитория
        self._repo       = PaymentRepository()
        self._user_repo  = UserRepository()

        # 2) Ищем в БД пользователя по telegram_id
        user = self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("Сначала заполните профиль через /start.")
        self._user = user

    def _calc_signature(self, out_sum: str, inv_id: str) -> str:
        raw = f"{RobokassaConfig.MERCHANT_LOGIN}:{out_sum}:{inv_id}:{RobokassaConfig.PASSWORD1}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    async def generate_payment_link(self, amount: Decimal) -> str:
        """
        Создаёт запись заказа (user_id берётся из self._user.user_id)
        и возвращает URL для оплаты в Robokassa.
        """
        # используем именно внутренний user_id
        order = await asyncio.to_thread(
            self._repo.create_order,
            self._user.user_id,
            amount,
            "Подписка GymMy Premium"
        )

        out_sum   = f"{amount:.2f}"
        inv_id    = str(order.id)
        signature = self._calc_signature(out_sum, inv_id)

        params = {
            "MerchantLogin":  RobokassaConfig.MERCHANT_LOGIN,
            "OutSum":         out_sum,
            "InvId":          inv_id,
            "Description":    order.description,
            "SignatureValue": signature,
            "IsTest":         0
        }
        query = parse.urlencode(params)
        return f"{RobokassaConfig.PAYMENT_URL}?{query}"

    def close(self):
        self._repo.close()
        self._user_repo.close()
