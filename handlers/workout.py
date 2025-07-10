from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from services.subscription_service import SubscriptionService
from states import WorkoutCreation
from services.program_service import ProgramService
from services.program_creator_service import ProgramCreatorService
from services.main_menu_service import MenuService
from services.user_program_view_service import UserProgramViewService
from services.exercise_service import ExerciseService
from keyboards.workout import main_workout_keyboard, level_keyboard

router = Router()

DAYS_RU = [
    "Понедельник", "Вторник", "Среда", "Четверг",
    "Пятница", "Суббота", "Воскресенье"
]

def days_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=DAYS_RU[0], callback_data="dow_0"),
         InlineKeyboardButton(text=DAYS_RU[1], callback_data="dow_1")],
        [InlineKeyboardButton(text=DAYS_RU[2], callback_data="dow_2"),
         InlineKeyboardButton(text=DAYS_RU[3], callback_data="dow_3")],
        [InlineKeyboardButton(text=DAYS_RU[4], callback_data="dow_4"),
         InlineKeyboardButton(text=DAYS_RU[5], callback_data="dow_5")],
        [InlineKeyboardButton(text=DAYS_RU[6], callback_data="dow_6")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_comment")]
    ])

@router.message(lambda message: message.text == "🏋️ Мои тренировки")
async def my_workouts_handler(message: Message, state: FSMContext):
    sub_service = SubscriptionService(message.from_user.id)
    if not sub_service.has_active():
        await message.answer("❗️ Этот раздел доступен только пользователям с Premium-подпиской.")
        return
    await state.clear()
    svc = ProgramService(message.from_user.id)
    programs = svc.list_user_programs()
    markup = main_workout_keyboard(programs)
    await message.answer("⚡️ Твои тренировки прикреплены к сообщению", reply_markup=markup)

@router.callback_query(lambda c: c.data == "cancel_creation")
async def cancel_creation_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer("Вы покинули раздел тренировок 🫡")
    await state.clear()
    markup = MenuService(callback.from_user.id).get_main_menu_markup()
    await callback.message.answer("Вы покинули раздел тренировок 🫡", reply_markup=markup)

@router.callback_query(lambda c: c.data == "create_workout")
async def create_workout_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    await state.set_state(WorkoutCreation.choosing_level)
    await callback.message.answer("Выберите уровень сложности:", reply_markup=level_keyboard())

@router.callback_query(lambda c: c.data == "plan_create")
async def plan_create_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    await state.set_state(WorkoutCreation.plan_choosing_level)
    await callback.message.answer("Выберите уровень сложности плана:", reply_markup=level_keyboard())

@router.callback_query(lambda c: c.data == "back_to_workouts", StateFilter(WorkoutCreation.choosing_level))
async def back_to_workouts_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    await state.clear()
    svc = ProgramService(callback.from_user.id)
    programs = svc.list_user_programs()
    markup = main_workout_keyboard(programs)
    await callback.message.answer("⚡️ Твои тренировки прикреплены к сообщению", reply_markup=markup)

@router.callback_query(
    lambda c: c.data.startswith("level_"),
    StateFilter(WorkoutCreation.choosing_level)
)
async def level_selected_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    level = callback.data.split("_", 1)[1]
    await state.set_state(WorkoutCreation.waiting_comment)
    await state.update_data(chosen_level=level)
    await callback.message.answer(
        "📝 Введите пожелания к тренировке (например, 'хочу проработать ноги и плечи, немного бицепс')",
        parse_mode="HTML"
    )

@router.message(StateFilter(WorkoutCreation.waiting_comment))
async def comment_received(message: Message, state: FSMContext):
    comment = message.text.strip()
    await state.update_data(comment=comment)
    await state.set_state(WorkoutCreation.choosing_day)
    await message.answer(
        "В какой день недели вам удобнее всего делать эту тренировку?",
        reply_markup=days_keyboard()
    )

@router.callback_query(lambda c: c.data == "back_to_comment", StateFilter(WorkoutCreation.choosing_day))
async def back_to_comment_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    await state.set_state(WorkoutCreation.waiting_comment)
    await callback.message.answer(
        "📝 Введите пожелания к тренировке (например, \"хочу проработать ноги и плечи, немного бицепс\")",
        parse_mode="HTML"
    )

@router.callback_query(lambda c: c.data == "back_to_workouts_list")
async def back_to_workouts_list_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    svc = ProgramService(callback.from_user.id)
    programs = svc.list_user_programs()
    markup = main_workout_keyboard(programs)
    await callback.message.answer("🏋️ Твои тренировки прикреплены к сообщению", reply_markup=markup)

@router.callback_query(lambda c: c.data.startswith("dow_"), StateFilter(WorkoutCreation.choosing_day))
async def day_chosen_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    day_idx = int(callback.data.split("_", 1)[1])
    day_ru = DAYS_RU[day_idx]
    await state.update_data(day_of_week=day_ru)
    data = await state.get_data()
    level = data.get("chosen_level")
    comment = data.get("comment", "")
    day_of_week = data.get("day_of_week")
    wait_msg = await callback.message.answer("⚡ Пару мгновений, создаю тренировку...")
    await state.set_state(WorkoutCreation.generating_plan)
    await state.update_data(wait_msg_id=wait_msg.message_id)
    user_id = callback.from_user.id
    creator = ProgramCreatorService(user_id)
    try:
        await creator.generate_and_save_plan(level, comment, day_of_week)
        await state.clear()
        markup = MenuService(user_id).get_main_menu_markup()
        await wait_msg.answer("Готово! Твоя тренировка создана.", reply_markup=markup)
    except Exception as e:
        await state.clear()
        await wait_msg.answer(
            f"❗️ Ошибка при создании тренировки:\nТренировка не была сохранена. Попробуйте ещё раз."
        )

@router.callback_query(lambda c: c.data == "back_to_day", StateFilter(WorkoutCreation.generating_plan))
async def back_to_day_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if "wait_msg_id" in data:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=data["wait_msg_id"])
        except Exception:
            pass
    await callback.message.delete()
    await callback.answer()
    await state.set_state(WorkoutCreation.choosing_day)
    await callback.message.answer(
        "В какой день недели вам удобнее всего делать эту тренировку?",
        reply_markup=days_keyboard()
    )

# ---- ВОРОНКА СОЗДАНИЯ ПЛАНА ----

@router.callback_query(lambda c: c.data.startswith("level_"), StateFilter(WorkoutCreation.plan_choosing_level))
async def plan_level_selected_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    level = callback.data.split("_", 1)[1]
    await state.set_state(WorkoutCreation.plan_waiting_comment)
    await state.update_data(plan_level=level)
    await callback.message.answer(
        "📝 Расскажи, что хочешь получить от плана (например, \"накачать ноги и пресс\")"
    )

@router.message(StateFilter(WorkoutCreation.plan_waiting_comment))
async def plan_comment_cb(message: Message, state: FSMContext):
    await state.update_data(plan_comment=message.text)
    await state.set_state(WorkoutCreation.plan_waiting_days)
    await message.answer(
        "🗓 В какие дни недели тебе было бы удобно тренироваться? "
        "Можешь написать в свободной форме — я всё пойму (например: \"понедельник, среда и пятница\" или \"хочу 4 раза в неделю, кроме выходных\")"
    )

@router.message(StateFilter(WorkoutCreation.plan_waiting_days))
async def plan_days_cb(message: Message, state: FSMContext):
    await state.update_data(plan_days=message.text)
    data = await state.get_data()
    level = data.get("plan_level")
    comment = data.get("plan_comment")
    days_text = data.get("plan_days")
    wait_msg = await message.answer("⚡ Пару мгновений, составляю план тренировок...")
    try:
        creator = ProgramCreatorService(message.from_user.id)
        await creator.generate_and_save_full_plan(level, comment, days_text)
        await state.clear()
        markup = MenuService(message.from_user.id).get_main_menu_markup()
        await wait_msg.answer("План успешно создан! Посмотри список тренировок.", reply_markup=markup)
    except Exception as e:
        print(e)
        await state.clear()
        await wait_msg.answer(
            f"❗️ Ошибка при создании плана:\nПлан не был сохранён. Попробуйте ещё раз."
        )

@router.callback_query(lambda c: c.data.startswith("workout_"))
async def workout_view_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    user_program_id = int(callback.data.split("_", 1)[1])
    service = UserProgramViewService(callback.from_user.id)
    details, markup = service.get_user_program_detail(user_program_id)
    msg = await callback.message.answer(details, reply_markup=markup, parse_mode="HTML")
    await state.update_data(last_workout_msg_id=msg.message_id)

@router.callback_query(lambda c: c.data.startswith("exercise_detail:"))
async def exercise_detail_cb(callback: CallbackQuery):
    await callback.answer()
    ex_id = int(callback.data.split(":", 1)[1])
    svc = ExerciseService()
    ex = svc.get_detail_by_id(ex_id)
    svc.close()
    if not ex:
        await callback.message.answer("⚠️ Упражнение не найдено.")
        return
    detail_text = (
        f"🏋️ <b>{ex.name}</b>\n\n"
        f"{ex.description}\n\n"
        f"<b>Техника выполнения:</b>\n{ex.technique}\n\n"
        f"<b>Оборудование:</b> {ex.equipment or '—'}"
    )
    await callback.message.answer(detail_text, parse_mode="HTML")

@router.callback_query(lambda c: c.data.startswith("delete_program:"))
async def delete_program_confirm_cb(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_program_id = int(callback.data.split(":", 1)[1])
    msg = await callback.message.answer(
        "❗️ Вы уверены, что хотите удалить эту тренировку?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_program_yes:{user_program_id}")],
                [InlineKeyboardButton(text="❌ Нет, оставить", callback_data=f"delete_program_no:{user_program_id}")]
            ]
        )
    )
    await state.update_data(delete_confirm_msg_id=msg.message_id)

@router.callback_query(lambda c: c.data.startswith("delete_program_yes:"))
async def delete_program_yes_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if "last_workout_msg_id" in data and data["last_workout_msg_id"]:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=data["last_workout_msg_id"])
        except Exception:
            pass
    await callback.message.delete()
    await callback.answer()
    user_program_id = int(callback.data.split(":", 1)[1])
    from storage.user_program_repository import UserProgramRepository
    repo = UserProgramRepository()
    try:
        program = repo.get(user_program_id)
        if program:
            repo._session.delete(program)
            repo._session.commit()
            await callback.message.answer("✅ Тренировка удалена.")
        else:
            await callback.message.answer("Тренировка не найдена.")
    finally:
        repo.close()
    await state.update_data(last_workout_msg_id=None)
    await state.update_data(delete_confirm_msg_id=None)

@router.callback_query(lambda c: c.data.startswith("delete_program_no:"))
async def delete_program_no_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()

@router.message(StateFilter(WorkoutCreation))
async def block_while_creating(message: Message):
    await message.reply(
        "Пожалуйста, закончите создание тренировки или плана, прежде чем выполнять другие команды 🤫"
    )
