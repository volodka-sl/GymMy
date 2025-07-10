from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    sex = State()
    height = State()
    weight = State()
    body_fat = State()
    health = State()
    birth_date = State()
    confirmation = State()

class PromoStates(StatesGroup):
    enter_code = State()

class ExerciseStates(StatesGroup):
    waiting_for_muscle = State()
    waiting_for_level  = State()
    waiting_for_exercise = State()

class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()
    in_feedback_chat    = State()

class ChatStates(StatesGroup):
    chatting = State()

class WorkoutCreation(StatesGroup):
    choosing_level = State()
    waiting_comment = State()
    choosing_day = State()
    generating_plan = State()

    plan_choosing_level = State()
    plan_waiting_comment = State()
    plan_waiting_days = State()
    plan_generating = State()
