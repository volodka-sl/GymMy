from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from services.exercise_service import ExerciseService
from services.subscription_service import SubscriptionService  # ←— Импорт
from keyboards.exercise_keyboards import muscles_kb, levels_kb, exercises_kb
from states import ExerciseStates
from storage.models import DifficultyLevel

router = Router(name="exercise")


@router.message(F.text == "📚 База упражнений")
async def ask_muscle(message: Message, state: FSMContext):
    svc = ExerciseService()
    muscles = svc.list_muscles()
    svc.close()

    await state.clear()
    await state.set_state(ExerciseStates.waiting_for_muscle)
    await message.answer(
        "💪 Отлично! Доступна база упражнений.\n"
        "Выбери мышечную группу, которая тебя интересует:",
        reply_markup=muscles_kb(muscles),
    )


@router.callback_query(
    ExerciseStates.waiting_for_muscle, F.data == "exercise_cancel"
)
async def cancel_exercises(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    await state.clear()


@router.callback_query(
    ExerciseStates.waiting_for_muscle, F.data.startswith("muscle_choice:")
)
async def choose_level(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()

    muscle = callback.data.split(":", 1)[1]
    await state.update_data(muscle=muscle)

    svc = ExerciseService()
    levels = svc.list_levels(muscle)
    svc.close()

    # ←— ФИЛЬТРУЕМ УРОВНИ ДЛЯ НЕПОДПИСАННЫХ
    sub_svc = SubscriptionService(callback.from_user.id)
    has_sub = False
    try:
        has_sub = sub_svc.has_active()
    finally:
        sub_svc.close()

    if not has_sub:
        # оставляем только лёгкий, даже если в базе есть другие
        levels = [DifficultyLevel.easy]

    await state.set_state(ExerciseStates.waiting_for_level)
    await callback.message.answer(
        f"🧐 Выбрана *{muscle}*.\nТеперь укажи уровень подготовки:",
        parse_mode="Markdown",
        reply_markup=levels_kb(levels),
    )


@router.callback_query(
    ExerciseStates.waiting_for_level, F.data == "back_to_muscle"
)
async def back_to_muscle(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()

    svc = ExerciseService()
    muscles = svc.list_muscles()
    svc.close()

    await state.set_state(ExerciseStates.waiting_for_muscle)
    await callback.message.answer(
        "💪 Давай сначала выберем мышечную группу:",
        reply_markup=muscles_kb(muscles),
    )


@router.callback_query(
    ExerciseStates.waiting_for_level, F.data.startswith("level_")
)
async def list_exs(callback: CallbackQuery, state: FSMContext):
    # удаляем предыдущее сообщение и отвечаем
    await callback.message.delete()
    await callback.answer()

    data = await state.get_data()
    muscle = data["muscle"]
    lvl_value = callback.data.split("_", 1)[1]
    chosen_level = DifficultyLevel(lvl_value)

    # ←— проверяем подписку пользователя
    sub_svc = SubscriptionService(callback.from_user.id)
    has_sub = False
    try:
        has_sub = sub_svc.has_active()
    finally:
        sub_svc.close()

    # если нет подписки — принудительно используем лёгкий уровень
    level = chosen_level if has_sub else DifficultyLevel.easy  # ←— Изменено

    svc = ExerciseService()
    exs = svc.list_exercises(muscle, level)
    svc.close()

    # сохраняем в контекст: какой уровень реально используется и список id
    await state.update_data(
        level=level.value,
        exercise_ids=[ex.exercise_id for ex in exs]
    )
    await state.set_state(ExerciseStates.waiting_for_exercise)

    # формируем подпись уровня: если мы «понизили» уровень, предупреждаем
    level_name = level.name.title()
    suffix = ""
    if not has_sub and chosen_level != level:
        suffix = "\n\n⚠️ Доступен только лёгкий уровень для бесплатных пользователей."
    await callback.message.answer(
        f"📋 Упражнения для *{muscle}* ({level_name}):{suffix}",
        parse_mode="Markdown",
        reply_markup=exercises_kb(exs),
    )


@router.callback_query(
    ExerciseStates.waiting_for_exercise, F.data == "back_to_level"
)
async def back_to_level(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()

    data = await state.get_data()
    muscle = data["muscle"]

    svc = ExerciseService()
    levels = svc.list_levels(muscle)
    svc.close()

    await state.set_state(ExerciseStates.waiting_for_level)
    await callback.message.answer(
        f"🧐 Выбрана *{muscle}*.\nВыбери уровень подготовки снова:",
        parse_mode="Markdown",
        reply_markup=levels_kb(levels),
    )


@router.callback_query(
    ExerciseStates.waiting_for_exercise, F.data.startswith("exercise:")
)
async def show_detail(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()

    ex_id = int(callback.data.split(":", 1)[1])

    svc = ExerciseService()
    ex = svc.get_detail_by_id(ex_id)
    svc.close()

    if not ex:
        await callback.message.answer("⚠️ Упражнение не найдено.")
        return

    detail_text = (
        f"🏋️ *{ex.name}*\n\n"
        f"{ex.description}\n\n"
        f"*Техника выполнения:*\n{ex.technique}\n\n"
        f"*Оборудование:* {ex.equipment or '—'}"
    )
    await callback.message.answer(detail_text, parse_mode="Markdown")

    # повторно показываем список упражнений
    data = await state.get_data()
    muscle = data["muscle"]
    level = DifficultyLevel(data["level"])

    svc = ExerciseService()
    exs = svc.list_exercises(muscle, level)
    svc.close()

    await callback.message.answer(
        f"📋 Упражнения для *{muscle}* ({level.name.title()}):",
        parse_mode="Markdown",
        reply_markup=exercises_kb(exs),
    )
