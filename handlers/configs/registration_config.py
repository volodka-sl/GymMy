import re
from datetime import date
from states import RegistrationStates

def validate_weight(v: str):
    try:
        w = float(v.replace(',', '.'))
        if w > 0:
            return True, None
        return False, "Пожалуйста, введи число больше нуля для веса, например 68 ⚖️"
    except ValueError:
        return False, "Хмм… Не Совсем понял тебя 🧐\nВведи вес цифрами, например 68 ⚖️"

FIELD_CONFIG = [
    {
        'key': 'sex',
        'prefix': 'sex',
        'label': 'Пол',
        'state': RegistrationStates.sex,
        'ask': (
            "Для начала подскажи, пожалуйста, какой у тебя пол?\n"
            "Это поможет мне точнее подобрать упражнения и рассчитать калории 💡"
        ),
        'keyboard': 'sex_kb',
        'type': 'callback',
        'parse': lambda data: data.rsplit('_', 1)[1].upper(),
        'validate': lambda v: (True, None) if v in ('M', 'F') else (False, "Пожалуйста, выбери пол кнопкой 👍"),
        'manual_error': "Пожалуйста, выбери пол кнопкой 👍",
        'transform': lambda v: v,
        'next': 'height_cm',
    },
    {
        'key': 'height_cm',
        'label': 'Рост',
        'state': RegistrationStates.height,
        'ask': "Отлично 😊\nУкажи, пожалуйста, свой рост в сантиметрах",
        'keyboard': None,
        'type': 'message',
        'validate': lambda v: (
            (v.isdigit() and int(v) >= 100),
            "Извини, не понял 😅\nВведи рост, например 172"
        ) if not (v.isdigit() and int(v) >= 100) else (True, None),
        'transform': lambda v: int(v),
        'next': 'weight_kg',
    },
    {
        'key': 'weight_kg',
        'label': 'Вес',
        'state': RegistrationStates.weight,
        'ask': "Теперь расскажи, какой у тебя текущий вес в килограммах ⚖️",
        'keyboard': None,
        'type': 'message',
        'validate': validate_weight,
        'transform': lambda v: float(v.replace(',', '.')),
        'next': 'body_fat_pct',
    },
    {
        'key': 'body_fat_pct',
        'prefix': 'body_fat',
        'label': '% жира',
        'state': RegistrationStates.body_fat,
        'ask': "Укажи, пожалуйста, свой процент жира в теле — выбери одну из кнопок ниже 📊",
        'keyboard': 'body_fat_kb',
        'type': 'callback',
        'photo_path': lambda data: f"assets/body_fat_pictures/body_fat_picture_{data['sex']}.png",
        'parse': lambda data: data.rsplit('_', 1)[1],
        'validate': lambda v: (True, None),
        'manual_error': "Пожалуйста, выбери процент жира кнопкой 📊",
        'transform': lambda v: v,
        'next': 'health_issues',
    },
    {
        'key': 'health_issues',
        'prefix': 'health',
        'label': 'Проблемы со здоровьем',
        'state': RegistrationStates.health,
        'ask': (
            "Спасибо, план почти готов! 😌\n"
            "Чтобы сделать тренировки безопасными и эффективными, "
            "напиши, укажи свои физиологические особенности и медицинские противопоказания\n,"
            "например: "
            "— опиши их или нажми «Нет»"
        ),
        'keyboard': 'health_kb',
        'type': 'both',
        'parse': lambda data: data.rsplit('_', 1)[1],
        'validate': lambda v: (True, None),
        'transform': lambda v: 'Нет' if v.lower() == 'no' else v.strip(),
        'next': 'birth_date',
    },
    {
        'key': 'birth_date',
        'label': 'Дата рождения',
        'state': RegistrationStates.birth_date,
        'ask': (
            "И последний, но не менее важный вопрос 🎂\n\n"
            "Когда у тебя день рождения? Укажи дату в формате ДД.MM.ГГГГ\n"
            "Это также повлияет на план тренировок 💪"
        ),
        'keyboard': None,
        'type': 'message',
        'validate': lambda v: (
            bool(re.match(r'^\d{2}\.\d{2}\.\d{4}$', v)),
            "Извини, не понял формат 😅\nВведи дату как ДД.MM.ГГГГ"
        ),
        'transform': lambda v: date(*map(int, v.split('.')[::-1])).isoformat(),
        'next': None,
    },
]

CONFIG_BY_KEY = {cfg['key']: cfg for cfg in FIELD_CONFIG}
STATE_TO_KEY   = {cfg['state']: cfg['key'] for cfg in FIELD_CONFIG}
