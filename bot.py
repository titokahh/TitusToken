import os
import logging
import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

TOKEN = "8602710874:AAHYjciw889hoT_Th6rM7HuIFb_35jPXiDU"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Memória a felhasználók adataihoz
user_data = {}
all_users = set()

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0.0,
            "ads_watched": 0,
            "autobot_active": False,
            "autobot_end_time": None,
            "start_time": datetime.datetime.now()
        }
    return user_data[user_id]

# Főmenü gombok generálása
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="💰 Egyenleg", callback_data="balance"),
        types.InlineKeyboardButton(text="⛏️ Bányászat", callback_data="mining")
    )
    builder.row(
        types.InlineKeyboardButton(text="🤖 Autobot (24 óra)", callback_data="autobot"),
        types.InlineKeyboardButton(text="🔒 Staking", callback_data="staking")
    )
    builder.row(
        types.InlineKeyboardButton(text="👥 Meghívás", callback_data="invite"),
        types.InlineKeyboardButton(text="⏱️ Időzítő", callback_data="timer")
    )
    builder.row(
        types.InlineKeyboardButton(text="💸 Utalás", callback_data="transfer"),
        types.InlineKeyboardButton(text="💳 Tárca Csatolása", callback_data="wallet")
    )
    builder.row(
        types.InlineKeyboardButton(text="ℹ️ Infó & Tokenomika", callback_data="info")
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    all_users.add(user_id)
    get_user(user_id)
    
    text = f"Szia **{message.from_user.first_name}**!\nÜdvözöllek a **Sajt Token Tesztnet** botban! 🧀\nVálassz az alábbi lehetőségek közül:"
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    total_count = len(all_users)
    total_mined = sum(data["balance"] for data in user_data.values())
    remaining_pool = 3000000 - total_mined

    stats_text = (
        f"📊 **Rendszer Statisztika:**\n\n"
        f"• Összes regisztrált felhasználó: **{total_count}** fő\n"
        f"• Eddig összesen kitermelve: **{total_mined:.4f}** SAJT\n"
        f"• A 3 milliós bányászható alapból hátra van: **{remaining_pool:.4f}** SAJT"
    )
    await message.answer(stats_text, parse_mode="Markdown")

# Gombkezelő (Callback handler)
@dp.callback_query()
async def callback_listener(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    all_users.add(user_id)
    user_info = get_user(user_id)
    data = callback.data

    if data == "balance":
        await callback.answer()
        bal = user_info["balance"]
        await callback.message.answer(f"🔥 **Egyenleged részletezése:**\n\n• Elérhető egyenleg: **{bal:.4f}** Sajt Token", parse_mode="Markdown")

    elif data == "mining":
        await callback.answer()
        await callback.message.answer("⛏️ **Bányászat menü:** Nézz meg 5 hirdetést a Mini Appban, indítsd el az Autobotot, és az 24 órán át termeli neked a tokeneket!")

    elif data == "autobot":
        await callback.answer()
        watched = user_info["ads_watched"]
        now = datetime.datetime.now()

        if user_info["autobot_active"] and user_info["autobot_end_time"] and now < user_info["autobot_end_time"]:
            remaining = user_info["autobot_end_time"] - now
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            auto_desc = (
                f"🤖 **Auto-Bot Státusz: 🟢 AKTÍV**\n\n"
                f"Az Autobot éppen dolgozik a háttérben!\n"
                f"• Hátralévő idő: **{hours} óra {minutes} perc**\n"
                f"• Jelenlegi egyenleg: **{user_info['balance']:.4f} SAJT**"
            )
            await callback.message.answer(auto_desc, parse_mode="Markdown")
        else:
            if user_info["autobot_active"] and user_info["autobot_end_time"] and now >= user_info["autobot_end_time"]:
                user_info["autobot_active"] = False

            web_app_url = "https://sajt-token-bot-production.up.railway.app"
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="📺 Hirdetés megtekintése (Mini App)", web_app=types.WebAppInfo(url=web_app_url)))
            builder.row(types.InlineKeyboardButton(text="✅ Hirdetés teljesítve (Jóváírás)", callback_data="watch_one_ad"))
            
            if watched >= 5:
                builder.row(types.InlineKeyboardButton(text="🚀 24 Órás Autobot Indítása", callback_data="start_autobot_24h"))

            auto_desc = (
                f"🤖 **Auto-Bot Vezérlőpult**\n\n"
                f"• **Státusz:** 🔴 INAKTÍV\n"
                f"• **Teljesített hirdetések:** **{watched} / 5**\n\n"
                f"Nézz végig 5 hirdetést a Mini Appban, majd indítsd el az Autobotot!"
            )
            await callback.message.answer(auto_desc, reply_markup=builder.as_markup(), parse_mode="Markdown")

    elif data == "watch_one_ad":
        if user_info["ads_watched"] < 5:
            user_info["ads_watched"] += 1
            await callback.answer(f"Hirdetés rögzítve! ({user_info['ads_watched']}/5)")
            await callback.message.answer(f"✅ Hirdetés sikeresen igazolva!\nJelenlegi állás: **{user_info['ads_watched']} / 5**", parse_mode="Markdown")
        else:
            await callback.answer("Már megvan az 5 hirdetés!", show_alert=True)

    elif data == "start_autobot_24h":
        if user_info["ads_watched"] >= 5:
            user_info["autobot_active"] = True
            user_info["autobot_end_time"] = datetime.datetime.now() + datetime.timedelta(hours=24)
            user_info["ads_watched"] = 0
            user_info["balance"] += 0.50
            await callback.answer("Sikeresen elindult a 24 órás Autobot!")
            await callback.message.answer("🚀 **Gratulálunk!** Az Autobot elindult a következő 24 órára, és jóváírtuk az induló jutalmat!", parse_mode="Markdown")
        else:
            await callback.answer("Még nincs meg az 5 hirdetés!", show_alert=True)

    elif data == "staking":
        await callback.answer()
        await callback.message.answer("🔒 **Staking Rendszer:** Itt tudod majd lekötni a tokenjeidet extra hozamért.", parse_mode="Markdown")

    elif data == "invite":
        await callback.answer()
        bot_info = await bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        await callback.message.answer(f"👥 **Barátok Meghívása:**\nOszd meg az alábbi linket:\n`{invite_link}`", parse_mode="Markdown")

    elif data == "timer":
        await callback.answer()
        start_t = user_info["start_time"]
        expiry_t = start_t + datetime.timedelta(days=365)
        remaining = expiry_t - datetime.datetime.now()

        if remaining.total_seconds() > 0:
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            timer_text = f"⏱️ **Visszaszámlálás a tőzsdére kerülésig:**\n• **{days}** nap\n• **{hours}** óra\n• **{minutes}** perc"
        else:
            timer_text = "⏱️ Letelt az idő, a tőzsdére kerülés ideje elért!"
        await callback.message.answer(timer_text, parse_mode="Markdown")

    elif data == "transfer":
        await callback.answer()
        await callback.message.answer("💸 **Token Utalás:** Itt tudsz majd tokeneket küldeni más felhasználóknak.", parse_mode="Markdown")

    elif data == "wallet":
        await callback.answer()
        await callback.message.answer("💳 **Tárca Csatolása:** A TON / Web3 tárca összekötése hamarosan érkezik.", parse_mode="Markdown")

    elif data == "info":
        await callback.answer()
        info_text = (
            "ℹ️ **Sajt Token Hivatalos Tokenomika:**\n\n"
            "• **Maximális készlet:** 5,000,000 SAJT\n"
            "• **Utángyártás:** Nincs (Szigorúan korlátozott)\n"
            "• **Tito részesedése:** 2,000,000 SAJT\n\n"
            "📊 **Reklám Bevételek Elosztása:**\n"
            "• 💧 **40%** -> Likviditás\n"
            "• 🔥 **30%** -> Egetés (Burn)\n"
            "• 🛠️ **30%** -> Fejlesztés"
        )
        await callback.message.answer(info_text, parse_mode="Markdown")

# Adsgram jutalom végpont (/reward?user_id=...)
async def handle_reward(request: web.Request):
    user_id_str = request.query.get("user_id")
    if not user_id_str:
        return web.json_response({"error": "Hiányzó user_id"}, status=400)
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        return web.json_response({"error": "Érvénytelen user_id formátum"}, status=400)
    
    user_info = get_user(user_id)
    user_info["balance"] += 0.02  # Hirdetés utáni jóváírás
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 **Adsgram Hirdetés Teljesítve!**\nJóváírtunk neked +0.02 SAJT tokent.\nJelenlegi egyenleged: **{user_info['balance']:.4f} SAJT**",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Hiba az értesítés küldésekor: {e}")
    
    return web.json_response({"status": "success", "reward": 0.02})

async def web_server():
    app = web.Application()
    app.router.add_get("/reward", handle_reward)
    
    async def index(request):
        return web.Response(text="Sajt Token Bot Backend Fut (Adsgram Aktív).")
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
