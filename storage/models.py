import enum
from sqlalchemy import (
    Column, Integer, BigInteger, SmallInteger, String, Text,
    Date, DateTime, Boolean, DECIMAL, ForeignKey, Enum,
    UniqueConstraint, Index, func,
    Text, Numeric, TIMESTAMP
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class DifficultyLevel(enum.Enum):
    easy = "easy"
    medium = "medium"
    advanced = "advanced"


class ProgramTemplate(Base):
    __tablename__ = "program_template"

    template_id = Column(Integer, primary_key=True)
    name        = Column(Text,    nullable=False)
    description = Column(Text)
    difficulty  = Column(
        Enum(DifficultyLevel, name="difficulty_levels"),
        nullable=False,
        comment="Лёгкий / средний / продвинутый"
    )
    created_by  = Column(Text)   # 'chatgpt' или админ
    created_at  = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # связи
    exercises = relationship("TemplateExercise", back_populates="template")
    schedules = relationship("UserProgramSchedule", back_populates="template")


class Exercise(Base):
    __tablename__ = "exercise"

    exercise_id    = Column(Integer, primary_key=True)
    name           = Column(Text,    nullable=False)
    description    = Column(Text)
    technique      = Column(Text,    comment="Техника выполнения")
    primary_muscle = Column(Text)
    equipment      = Column(Text)
    video_url      = Column(Text)
    difficulty     = Column(
        Enum(DifficultyLevel, name="difficulty_levels"),
        nullable=False,
        comment="Лёгкий / средний / продвинутый"
    )
    created_at     = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # связь ManyToMany через TemplateExercise
    templates = relationship("TemplateExercise", back_populates="exercise")


class TemplateExercise(Base):
    __tablename__ = "template_exercise"
    # Эта таблица — связка шаблона и упражнения с доп. полями
    template_id = Column(
        Integer,
        ForeignKey("program_template.template_id", ondelete="CASCADE"),
        primary_key=True
    )
    exercise_id = Column(
        Integer,
        ForeignKey("exercise.exercise_id", ondelete="CASCADE"),
        primary_key=True
    )
    sort_order  = Column(SmallInteger, nullable=False)
    sets        = Column(SmallInteger, nullable=False)
    reps        = Column(Text,        nullable=False)  # например '8–12'

    template = relationship("ProgramTemplate", back_populates="exercises")
    exercise = relationship("Exercise",        back_populates="templates")


class User(Base):
    __tablename__ = "user"

    user_id       = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id   = Column(BigInteger, nullable=False, unique=True, index=True)
    sex           = Column(String(1), comment="M/F/O")
    birth_date    = Column(Date,       nullable=False)
    height_cm     = Column(SmallInteger, nullable=False)
    weight_kg     = Column(DECIMAL(5,2), nullable=False)
    body_fat_pct  = Column(Text)
    health_issues = Column(Text)
    tz_offset     = Column(SmallInteger, nullable=False, comment="Смещение от UTC, часы")
    created_at    = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    promo_redemptions = relationship(
        "UserPromoCode", back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions = relationship("UserSubscription", back_populates="user")
    payment_orders = relationship(
        "PaymentOrder", back_populates="user", cascade="all, delete-orphan"
    )
    programs = relationship("UserProgram", back_populates="user")


class UserProgram(Base):
    __tablename__ = "user_program"

    user_program_id = Column(Integer, primary_key=True)
    user_id         = Column(
        BigInteger,
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False
    )
    template_id     = Column(
        Integer,
        ForeignKey("program_template.template_id"),
        nullable=False
    )
    start_date      = Column(Date, nullable=False)
    end_date        = Column(Date, nullable=True)   # NULL = бессрочный
    is_active       = Column(Boolean, nullable=False, server_default="true")
    created_at      = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # связи
    template = relationship("ProgramTemplate")
    user = relationship("User", back_populates="programs")


class UserProgramSchedule(Base):
    __tablename__ = "user_program_schedule"

    schedule_id  = Column(Integer, primary_key=True)
    template_id  = Column(
        Integer,
        ForeignKey("program_template.template_id", ondelete="CASCADE"),
        nullable=False
    )
    day_of_week  = Column(SmallInteger, nullable=False)  # 1=пн … 7=вс

    __table_args__ = (
        UniqueConstraint(
            "template_id",
            "day_of_week",
            name="uq_schedule_template_day"
        ),
    )

    template = relationship("ProgramTemplate", back_populates="schedules")


class UserSubscription(Base):
    __tablename__ = "user_subscription"

    subscription_id = Column(Integer, primary_key=True)
    user_id         = Column(
        BigInteger,
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False
    )
    start_ts      = Column(DateTime(timezone=True), nullable=False)
    end_ts        = Column(DateTime(timezone=True), nullable=False)
    created_at    = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    user      = relationship("User",             back_populates="subscriptions")
    reminders = relationship(
        "SubscriptionReminder",
        back_populates="subscription",
        cascade="all, delete"
    )


class SubscriptionReminder(Base):
    __tablename__ = "subscription_reminder"

    reminder_id          = Column(Integer, primary_key=True)
    user_subscription_id = Column(
        Integer,
        ForeignKey(
            "user_subscription.subscription_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    remind_at = Column(DateTime(timezone=True), nullable=False)
    type      = Column(String, nullable=False)   # 'before_3d' или 'on_end'
    sent      = Column(Boolean, nullable=False, server_default="false")
    sent_ts   = Column(DateTime(timezone=True), nullable=True)

    subscription = relationship(
        "UserSubscription",
        back_populates="reminders"
    )


class PromoCode(Base):
    __tablename__ = "promo_code"

    id           = Column(Integer, primary_key=True)
    code         = Column(Text, nullable=False, unique=True)
    type         = Column(Enum(
                       'discount_percent', 'discount_fixed', 'free_days',
                       name='promo_code_type'
                   ), nullable=False)
    discount_pct = Column(Numeric(5,2), comment="Скидка в %")
    discount_amt = Column(Numeric(10,2), comment="Фиксированная скидка в ₽")
    free_days    = Column(Integer, comment="Бесплатные дни")
    valid_from   = Column(Date,    nullable=False, server_default=func.current_date())
    valid_to     = Column(Date,    comment="Дата истечения")
    usage_limit  = Column(Integer, comment="Лимит использований, NULL = нет")
    created_at   = Column(TIMESTAMP(timezone=True),
                          nullable=False,
                          server_default=func.now())
    description  = Column(Text)

    redemptions  = relationship("UserPromoCode", back_populates="promo_code")

class UserPromoCode(Base):
    __tablename__ = "user_promo_code"

    id            = Column(Integer, primary_key=True)
    user_id       = Column(ForeignKey('user.user_id', ondelete='CASCADE'),
                           nullable=False)
    promo_code_id = Column(ForeignKey('promo_code.id', ondelete='CASCADE'),
                           nullable=False)
    redeemed_at   = Column(TIMESTAMP(timezone=True),
                           nullable=False,
                           server_default=func.now())

    promo_code    = relationship("PromoCode", back_populates="redemptions")
    user          = relationship("User", back_populates="promo_redemptions")


class PaymentOrder(Base):
    __tablename__ = "payment_order"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    amount      = Column(Numeric(10,2),      nullable=False)
    description = Column(Text,                nullable=False)
    status      = Column(Text,   nullable=False, server_default="pending")
    created_at  = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user        = relationship("User", back_populates="payment_orders")


class ReminderGender(enum.Enum):
    male = "male"
    female = "female"


class ReminderText(Base):
    __tablename__ = "reminder_text"

    reminder_text_id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)  # Дата, на которую сгенерировано напоминание (день)
    gender = Column(Enum(ReminderGender), nullable=False)
    text = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("date", "gender", name="uq_reminder_date_gender"),
    )


# индексы
Index("ix_subscription_remind_at", SubscriptionReminder.remind_at)
