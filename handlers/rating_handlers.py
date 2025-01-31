import keyboards.menu_kb as kb
from keyboards.pagination_kb import create_pagination_keyboard

from database import users_data

from filters import DisciplineFilter

from student_account import StudentAccount

from lexicon import LEXICON, LEXICON_COMMANDS

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery


router: Router = Router()
disciplines: list = []
pages: list = []
rating: list = []


@router.message(F.text == LEXICON_COMMANDS["rating"])
async def rating_menu(message: Message):
    await message.answer(
        text=LEXICON["rating"],
        reply_markup=kb.RatingMenu
        )


@router.message(F.text == LEXICON_COMMANDS["discipline_rating"])
async def discipline_rating_menu(message: Message):
    global disciplines

    await message.answer(text=LEXICON["processing"])

    rating = users_data[message.chat.id]["rating"]
    rating = await rating.full_disciplines_rating

    disciplines.extend([i.split(":")[0] for i in rating])

    await message.answer(
        text=LEXICON["discipline_rating"],
        reply_markup=kb.discipline_rating(disciplines=disciplines)
        )


@router.message(DisciplineFilter(disciplines=disciplines))
async def send_discipline_rating(message: Message):
    msg = await message.answer(text=LEXICON["processing"])

    discipline_rating = users_data[message.chat.id]["rating"]
    discipline_rating = await discipline_rating.discipline_rating(message.text)

    await msg.edit_text(text=discipline_rating)


@router.message(F.text == LEXICON_COMMANDS["short_rating"])
async def send_short_rating(message: Message):
    msg = await message.answer(text=LEXICON["processing"])

    rating = users_data[message.chat.id]["rating"]
    rating = await rating.short_disciplines_rating

    await msg.edit_text(text=rating)


@router.message(F.text == LEXICON_COMMANDS["full_rating"])
async def send_full_rating(message: Message):
    global rating
    global pages

    await message.answer(LEXICON["processing"])

    rating = users_data[message.chat.id]["rating"]
    rating = await rating.full_pages_rating

    pages = [str(i) for i in range(1, len(rating) + 1)]
    page = users_data[message.chat.id]["rating_page"]

    if page != len(pages) - 1 and page != 0:

        await message.answer(
            text=rating[page],
            reply_markup=create_pagination_keyboard(
                "backward_rating", pages[page], "forward_rating"
                )
            )

    elif page == 0:

        await message.answer(
            text=rating[page],
            reply_markup=create_pagination_keyboard(
                pages[page], "forward_rating"
                )
            )
    else:

        await message.answer(
            text=rating[page],
            reply_markup=create_pagination_keyboard(
                "backward_rating", pages[page]
                )
            )


@router.callback_query(F.data == "forward_rating")
async def press_forward_rating(callback: CallbackQuery):
    global rating
    global pages

    page = users_data[callback.from_user.id]["rating_page"]

    if page + 1 < len(pages) - 1:

        await callback.message.edit_text(
            text=rating[page + 1],
            reply_markup=create_pagination_keyboard(
                "backward_rating", pages[page + 1], "forward_rating"
                )
            )
    else:

        await callback.message.edit_text(
            text=rating[page + 1],
            reply_markup=create_pagination_keyboard(
                "backward_rating", pages[page + 1]
                )
            )

    users_data[callback.from_user.id]["rating_page"] += 1

    await callback.answer()


@router.callback_query(F.data == "backward_rating")
async def press_backward_rating(callback: CallbackQuery):
    global rating
    global pages

    page = users_data[callback.from_user.id]["rating_page"]

    if page - 1 > 0:

        await callback.message.edit_text(
            text=rating[page - 1],
            reply_markup=create_pagination_keyboard(
                "backward_rating", pages[page - 1], "forward_rating"
                )
            )

    else:

        await callback.message.edit_text(
            text=rating[page - 1],
            reply_markup=create_pagination_keyboard(
                pages[page - 1], "forward_rating"
                )
            )

    users_data[callback.from_user.id]["rating_page"] -= 1

    await callback.answer()


@router.message(F.text == LEXICON_COMMANDS["update_rating"])
async def update_student_rating(message: Message):
    msg = await message.answer(text=LEXICON["processing"])

    login = users_data[message.chat.id]["account"].user_login
    password = users_data[message.chat.id]["account"].user_pass

    account = await StudentAccount(
        user_login=login,
        user_pass=password).driver

    users_data[message.chat.id] = {
        "account": account,
        "schedule": account.schedule,
        "rating": account.rating,
        "schedule_page": 0,
        "rating_page": 0
    }

    users_data[message.chat.id]["account"].update_student_data(key="rating")

    await msg.edit_text(text=LEXICON["successful_updating"])
