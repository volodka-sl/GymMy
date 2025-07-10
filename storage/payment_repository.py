from storage.db import SessionLocal
from storage.models import PaymentOrder
from decimal import Decimal

class PaymentRepository:
    def __init__(self):
        self._session = SessionLocal()

    def create_order(self, user_id: int, amount: Decimal, description: str) -> PaymentOrder:
        order = PaymentOrder(
            user_id=user_id,
            amount=amount,
            description=description,
            status="pending"
        )
        self._session.add(order)
        self._session.commit()
        self._session.refresh(order)
        return order

    def update_status(self, order_id: int, status: str) -> None:
        order = self._session.get(PaymentOrder, order_id)
        if order:
            order.status = status
            self._session.commit()

    def close(self):
        self._session.close()
