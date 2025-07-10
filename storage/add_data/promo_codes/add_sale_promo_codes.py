#!/usr/bin/env python3
# storage/add_data/promo_codes/add_discount_promo_codes.py

import sys
from pathlib import Path
from datetime import date

# добавляем корень проекта в sys.path
# путь до этого файла: <project>/storage/add_data/promo_codes/...
# родитель на 3 уровня вверх — это корень проекта
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from storage.db import SessionLocal
from storage.models import PromoCode

def main():
    session = SessionLocal()
    today = date.today()

    promo_definitions = [
        {
            "code": "ZALUPA_ENOTA_PRC",
            "type": "discount_percent",
            "discount_pct": 99.0,
            "discount_amt": None,
            "free_days": None,
            "valid_from": today,
            "valid_to": None,
            "usage_limit": None,
            "description": "Тестовая скидка 99 % на подписку"
        },
        {
            "code": "ZALUPA_ENOTA_SUM",
            "type": "discount_fixed",
            "discount_pct": None,
            "discount_amt": 989.0,
            "free_days": None,
            "valid_from": today,
            "valid_to": None,
            "usage_limit": None,
            "description": "Тестовая скидка 989 ₽ на подписку"
        }
    ]

    for promo_data in promo_definitions:
        code = promo_data["code"]
        existing = session.query(PromoCode).filter_by(code=code).first()
        if existing:
            print(f"Промокод «{code}» уже существует — пропускаем.")
        else:
            promo = PromoCode(
                code=promo_data["code"],
                type=promo_data["type"],
                discount_pct=promo_data["discount_pct"],
                discount_amt=promo_data["discount_amt"],
                free_days=promo_data["free_days"],
                valid_from=promo_data["valid_from"],
                valid_to=promo_data["valid_to"],
                usage_limit=promo_data["usage_limit"],
                description=promo_data["description"]
            )
            session.add(promo)
            print(f"Добавляю промокод «{code}».")

    session.commit()
    print("Все промокоды обработаны.")
    session.close()

if __name__ == "__main__":
    main()
