# storage/add_data/promo_codes/add_free10_promo_code.py

import sys
from pathlib import Path

# добавляем корень проекта в sys.path
# путь до этого файла: <проект>/storage/add_data/promo_codes/...
# родитель на 3 уровня вверх — это корень проекта
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from storage.db import SessionLocal
from storage.models import PromoCode
from datetime import date

def main():
    session = SessionLocal()

    code = "FREE100"  # промокод
    existing = session.query(PromoCode).filter_by(code=code).first()
    if existing:
        print(f"Промокод «{code}» уже существует в базе.")
    else:
        promo = PromoCode(
            code=code,
            type='free_days',        # тип «бесплатные дни»
            free_days=10000,            # даёт 10 бесплатных суток
            valid_from=date.today(), # с сегодняшнего дня
            valid_to=None,           # без ограничения по дате
            usage_limit=100,        # без лимита на количество пользователей
            description="Premium-подписка на всю жизнь"
        )
        session.add(promo)
        session.commit()
        print(f"Промокод «{code}» успешно создан.")

    session.close()

if __name__ == "__main__":
    main()
