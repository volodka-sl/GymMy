import os
import logging
import hashlib

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse

from storage.db import SessionLocal
from storage.models import PaymentOrder, User
from services.notifier import BotNotifier
from services.subscription_service import SubscriptionService

router = APIRouter()
logger = logging.getLogger("robokassa")

BOT_TOKEN       = os.getenv("BOT_TOKEN")
# Правильно: PASSWORD_2, а не PASSWORD2
ROBOKASSA_PASS2 = os.getenv("ROBOKASSA_PASSWORD_2")
notifier        = BotNotifier(BOT_TOKEN)


@router.api_route(
    "/result",
    methods=["GET", "POST"],
    response_class=PlainTextResponse,
    summary="Robokassa callback: успешная оплата"
)
async def robokassa_result(
    request: Request,
    OutSum: str         = Form(None),
    InvId: str          = Form(None),
    SignatureValue: str = Form(None),
):
    # 1) Игнорируем «чистые» GET-редиректы (без PaymentMethod)
    if request.method == "GET" and "PaymentMethod" not in request.query_params:
        return PlainTextResponse("OK")

    # 2) При GET-callback берём параметры из query_params
    if request.method == "GET":
        qp = request.query_params
        OutSum         = qp.get("OutSum")
        InvId          = qp.get("InvId")
        SignatureValue = qp.get("SignatureValue")

    logger.info(f"[/result] callback via {request.method}: OutSum={OutSum!r}, InvId={InvId!r}")

    session = SessionLocal()
    try:
        # 3) Ищем заказ
        order = session.get(PaymentOrder, int(InvId))
        if not order:
            logger.error(f"Order {InvId} not found")
            raise HTTPException(404, "Order not found")

        # 4) Ищем пользователя
        user = session.get(User, order.user_id)
        if not user:
            logger.error(f"Linked user {order.user_id} not found")
            raise HTTPException(500, "Linked user not found")
        chat_id = user.telegram_id

        # Сырой OutSum для подписи (Robokassa шлёт с шестью нулями)
        sum_for_sig = OutSum
        expected    = hashlib.md5(f"{sum_for_sig}:{InvId}:{ROBOKASSA_PASS2}".encode()).hexdigest()
        logger.info(f"Using raw OutSum for signature: {sum_for_sig!r}")
        logger.info(f"ProvidedSig={SignatureValue!r}, ExpectedSig={expected!r}")

        if expected.lower() != (SignatureValue or "").lower():
            logger.warning(f"Invalid signature for order {InvId}")
            try:
                await notifier.send(
                    chat_id,
                    "❗️ Подпись платежа не прошла проверку. Обратитесь в поддержку."
                )
            except Exception as e:
                logger.error(f"Failed to send invalid-signature notification: {e!r}")
            raise HTTPException(400, "Invalid signature")

        # 5) Если уже оплачено — тихо возвращаем OK
        if order.status == "paid":
            return PlainTextResponse("OK")

        # 6) Первый успешный callback: отмечаем оплаченным и шлём уведомления
        order_id = order.id

        # промежуточное уведомление
        try:
            await notifier.send(chat_id, "⚡️ Платёж получен, обрабатываю информацию…")
        except Exception as e:
            logger.error(f"Failed to send pre-notification: {e!r}")

        order.status = "paid"
        session.commit()
        logger.info(f"Order {InvId} marked as PAID")

        # итоговое уведомление
        try:
            await notifier.send(
                chat_id,
                f"✅ Оплата заказа #{order_id} ({float(sum_for_sig):.2f}₽) прошла успешно! Спасибо за покупку 💪"
            )
        except Exception as e:
            logger.error(f"Failed to send success notification: {e!r}")

        # ———— активируем месячную подписку ————
        try:
            sub_svc  = SubscriptionService(chat_id)
            end_dt   = sub_svc.subscribe_month(months=1)
            sub_svc.close()
            # форматируем без года, с часами и минутами
            await notifier.send(
                chat_id,
                f"🎉 Ваша подписка Premium активирована до {end_dt.strftime('%d.%m %H:%M')}."
            )
        except Exception as e:
            logger.error(f"Failed to create subscription: {e!r}")
            await notifier.send(
                chat_id,
                "⚠️ Подписка была оплачена, но не удалось её сохранить в базе. Обратитесь в поддержку."
            )

    finally:
        session.close()

    return PlainTextResponse("OK")


@router.get(
    "/fail",
    response_class=PlainTextResponse,
    summary="Robokassa fail URL: отмена или таймаут"
)
async def robokassa_fail(
    InvId: str,
    OutSum: str,
):
    logger.info(f"[/fail] called: InvId={InvId!r}, OutSum={OutSum!r}")
    session = SessionLocal()
    try:
        order = session.get(PaymentOrder, int(InvId))
        if not order:
            return PlainTextResponse("OK")
        user = session.get(User, order.user_id)
        if not user:
            return PlainTextResponse("OK")
        chat_id = user.telegram_id

        if order.status != "paid":
            try:
                await notifier.send(
                    chat_id,
                    "⚠️ Оплата не была завершена в отведённое время или была отменена."
                )
                logger.info(f"Sent failure notification for order {InvId}")
            except Exception as e:
                logger.error(f"Failed to send failure notification: {e!r}")
    finally:
        session.close()

    return PlainTextResponse("OK")
