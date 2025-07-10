import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from storage.models import Exercise

from storage.add_data.chest_exercises import chest_exercises_data
from storage.add_data.back_exercises import back_exercises_data
from storage.add_data.legs_exercises import legs_exercises_data
from storage.add_data.shoulders_exercises import shoulders_exercises_data
from storage.add_data.biceps_exercises import biceps_exercises_data
from storage.add_data.triceps_exercises import triceps_exercises_data

# Подключаемся к БД через переменную окружения
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

def seed_back_exercises():
    exercises_data = [
        chest_exercises_data,
        back_exercises_data,
        legs_exercises_data,
        shoulders_exercises_data,
        biceps_exercises_data,
        triceps_exercises_data,
    ]

    session = Session()
    for data in exercises_data:
        for exercise in data:
            session.add(Exercise(**exercise))
        session.commit()
        session.close()
    print("✅ Упражнения успешно добавлены в таблицу exercise.")

if __name__ == "__main__":
    seed_back_exercises()
