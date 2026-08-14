import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

logging.TOKEN = "8865477160:AAHxLidy6fkQKYK3bzcz_aMKVVYVworiJWQ"

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("A TOKEN környezeti változó hiányzik!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_balances = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        user_id = message.from_user.id
        if user_id not in user_balances:
            user_balances[user_id] = 0
        
        await message.answer(
            f"Üdvözöllek a Tito Token Tesztnet botban!\n\nJelenlegi egyenleged: {user_balances[user_id]} token."
        )
    except Exception as e:
        logging.error(f"Hiba a start parancsnál: {e}")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    try:
        total_users = len(user_balances)
        total_tokens = sum(user_balances.values())
        await message.answer(
            f"📊 **Statisztika:**\n"
            f"• Összes regisztrált felhasználó: {total_users} fő\n"
            f"• Felhasználók egyenlege összesen: {total_tokens} token"
        )
    except Exception as e:
        logging.error(f"Hiba a stats parancsnál: {e}")

@dp.message()
async def handle_all_messages(message: types.Message):
    try:
        await message.answer("Szia! A kezdéshez kérlek küldd el a /start parancsot!")
    except Exception as e:
        logging.error(f"Hiba az üzenet kezelésekor: {e}")

if __name__ == "__main__":
    import asyncio
    async def main():
        logging.info("A Telegram bot indítása...")
        await dp.start_polling(bot)

    asyncio.run(main())
