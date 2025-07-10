from aiogram.utils.keyboard import InlineKeyboardBuilder
from handlers.configs.registration_config import FIELD_CONFIG


def sex_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='👨 Мужской', callback_data='sex_m')
    kb.button(text='👩 Женский', callback_data='sex_f')
    kb.adjust(2)
    return kb.as_markup()


def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='👍 Да, всё правильно', callback_data='confirm_yes')
    kb.button(text='✏️ Хочу исправить', callback_data='confirm_no')
    kb.adjust(2)
    return kb.as_markup()


def edit_field_kb():
    kb = InlineKeyboardBuilder()
    for cfg in FIELD_CONFIG:
        kb.button(text=cfg['label'], callback_data=f"edit_{cfg['key']}")
    kb.adjust(2)
    return kb.as_markup()


def body_fat_kb(data: dict):
    """
    Варианты % жира для выбора по полу.
    """
    options_f = ['13-15%', '15-25%', '26-35%', '36-40%', '41-45%', '45-55%']
    options_m = ['5-10%', '11-17%', '18-25%', '26-30%', '31-35%', '35-50%']
    opts = options_f if data.get('sex') == 'F' else options_m

    kb = InlineKeyboardBuilder()
    for opt in opts:
        val = opt.replace('%', '')
        kb.button(text=opt, callback_data=f"body_fat_{val}")
    kb.adjust(2)
    return kb.as_markup()


def health_kb():
    """
    Кнопка «Нет» для отсутствия проблем со здоровьем.
    """
    kb = InlineKeyboardBuilder()
    kb.button(text='Нет', callback_data='health_no')
    kb.adjust(1)
    return kb.as_markup()


def tariffs_kb():
    """
    Клавиатура с тарифами: оплата, промокод, пробная неделя и остаться на бесплатном тарифе.
    """
    kb = InlineKeyboardBuilder()
    kb.button(text='Перейти к оплате',                           callback_data='tariff_pay')
    kb.button(text='Ввести промокод',                            callback_data='tariff_promo')
    kb.button(text='Попробовать бесплатную неделю',              callback_data='tariff_trial')
    kb.adjust(2)  # две кнопки в ряду
    return kb.as_markup()
