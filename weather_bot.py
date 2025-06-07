from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram import Router
from dotenv import load_dotenv
import os
import logging

from weather_scraper import get_weather_info, get_weather_forecast_14days
from create_pdf_from_csv import create_pdf_from_csv



# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="bot.log",
    filemode="a"
)

load_dotenv()
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
assert BOT_TOKEN, "TG_BOT_TOKEN is missing in .env file"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

class Form(StatesGroup):
    waiting_for_location = State()

# Головна клавіатура
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌤️ Get weather in Wroclaw")]
    ],
    resize_keyboard=True
)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Hello! I'm your Weather Bot \n"
        "I can provide you with the prediction of the weather in Wroclaw \n"
        "Choose an option:",
        reply_markup=keyboard
    )

@router.message(F.text == "🌤️ Get weather in Wroclaw")
async def weather_choice(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Please wait, I am fetching the weather information for Wroclaw...",
        reply_markup=ReplyKeyboardRemove()
    )
    try:
        weather = get_weather_info()
        logging.info(f"Weather fetched: {weather}")
        await message.answer(weather)
    except Exception as e:
        logging.error(f"Error fetching weather: {e}")
        await message.answer("❌ Failed to fetch weather data.")

    await message.answer(
        "If you want to get a 14-day weather forecast, please type '14 days':",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 14 days")],
                [KeyboardButton(text="🔙 Back to main menu")]
            ],
            resize_keyboard=True
        )
    )

@router.message(F.text == "🗕️ 14 days")
async def long_forecast(message: types.Message):
    await message.answer("Fetching 14-day forecast, please wait...", reply_markup=ReplyKeyboardRemove())
    try:
        forecast = get_weather_forecast_14days()
        await message.answer(forecast)
    except Exception as e:
        logging.error(f"Error fetching 14-day forecast: {e}")
        await message.answer("\u274c Failed to fetch 14-day forecast.")
        return

    await message.answer(
        "Do you want to receive the forecast in PDF format?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💾 Save forecast as PDF")],
                [KeyboardButton(text="🔙 Back to main menu")]
            ],
            resize_keyboard=True
        )
    )

@router.message(F.text == "💾 Save forecast as PDF")
async def send_pdf_forecast(message: types.Message):
    csv_path = "forecast_14days.csv"
    pdf_path = "forecast_14days.pdf"

    if not os.path.exists(csv_path):
        await message.answer("\u274c Forecast data not found. Please request it first.")
        return

    try:
        create_pdf_from_csv(csv_path, pdf_path)
        await message.answer_document(
            types.FSInputFile(pdf_path),
            caption="📄 Here's your 14-day forecast as a PDF file."
        )
    except Exception as e:
        logging.error(f"Error creating/sending PDF: {e}")
        await message.answer("\u274c Failed to create/send PDF.")

    await message.answer(
        "What would you like to do next?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Back to main menu")]],
            resize_keyboard=True
        )
    )

@router.message(F.text == "🔙 Back to main menu")
async def go_back_to_main(message: types.Message):
    await message.answer(
        "You're back at the main menu. Choose an option:",
        reply_markup=keyboard
    )

if __name__ == "__main__":
    import asyncio

    async def main():
        logging.info("Bot started")
        await dp.start_polling(bot)

    asyncio.run(main())
