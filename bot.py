import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)

TOKEN = "8865477160:AAHxLidy6fkQKYK3bzcz_aMKVVYVworiJWQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_balances = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        user_id = message.from_user.id
        if user_id not in user_balances:
            user_balances[user_id] = 0
        
        web_app_url = "https://sajt-token-bot-production.up.railway.app"
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="🎮 Játék & Reklámok", 
                        web_app=types.WebAppInfo(url=web_app_url)
                    )
                ]
            ]
        )
        await message.answer(
            f"Üdvözöllek a Tito Token Tesztnet botban!\n\nJelenlegi egyenleged: {user_balances[user_id]} token.",
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Hiba a start parancsnál: {e}")

@dp.message()
async def handle_all_messages(message: types.Message):
    try:
        await message.answer("Szia! A gomb elindításához kérlek küldd el a /start parancsot!")
    except Exception as e:
        logging.error(f"Hiba az üzenet kezelésekor: {e}")

async def handle_reward(request: web.Request):
    user_id_str = request.query.get("user_id")
    
    if not user_id_str:
        return web.json_response({"error": "Hiányzó user_id"}, status0=400)
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        return web.json_response({"error": "Érvénytelen user_id formátum"}, status=400)
    
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] += 10
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 Gratulálok! Megnézted a hirdetést, és jóváírtunk neked 10 tokent!\nÖsszes egyenleged: {user_balances[user_id]} token."
        )
    except Exception as e:
        logging.error(f"Hiba az értesítés küldésekor: {e}")
    
    return web.json_response({"status": "success", "reward": 10})

async def web_server():
    app = web.Application()
    app.router.add_get("/reward", handle_reward)
    
    async def index(request):
        return web.Response(text="Tito Token Bot Backend Fut.")
    app.router.add_get("/", index)
    
    return app

if __name__ == "__main__":
    import asyncio
    
    async def main():
        port = int(os.environ.get("PORT", 8080))
        runner = web.AppRunner(await web_server())
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logging.info(f"Web szerver elindult a {port} porton.")
        
        await dp.start_polling(bot)

    asyncio.run(main())
