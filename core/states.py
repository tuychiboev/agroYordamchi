from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    choose_language = State()
    main_menu = State()
    ask_question = State()
    ask_plant_name = State()
    send_photo = State()
