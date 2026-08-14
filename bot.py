import os
import logging
import datetime
import secrets
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ============================================================
# BEÁLLÍTÁSOK
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Railway Variables alatt kell megadni:
# BOT_TOKEN = az ÚJ BotFather token
# REWARD_SECRET = egy hosszú titkos kulcs
#
# Példa:
# BOT_TOKEN=123456:ABC...
# REWARD_SECRET=valami-hosszu-titkos-kulcs

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Hiányzik a BOT_TOKEN Railway Environment Variable!")

REWARD_SECRET = os.environ.get("REWARD_SECRET")

if not REWARD_SECRET:
    raise RuntimeError("Hiányzik a REWARD_SECRET Railway Environment Variable!")


# Saját Railway cím
BASE_URL = "https://sajt-token-bot-production.up.railway.app"

# AdsGram Block ID
ADSGRAM_BLOCK_ID = "42894"

# Egy hirdetés jutalma
AD_REWARD = 0.02

# Minimum idő két szerveroldali jutalom között ugyanannak a usernek.
# Ez plusz védelmet ad a véletlen dupla callbackek ellen.
REWARD_COOLDOWN_SECONDS = 15


bot = Bot(token=TOKEN)
dp = Dispatcher()


# ============================================================
# FELHASZNÁLÓI ADATOK
# ============================================================

user_data = {}
all_users = set()

# Utolsó AdsGram jutalom időpontja
last_reward_time = {}


def get_user(user_id: int):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0.0,
            "ads_watched": 0,
            "autobot_active": False,
            "autobot_end_time": None,
            "start_time": datetime.datetime.now()
        }

    return user_data[user_id]


# ============================================================
# FŐMENÜ
# ============================================================

def get_main_menu():
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="💰 Egyenleg",
            callback_data="balance"
        ),
        types.InlineKeyboardButton(
            text="⛏️ Bányászat",
            callback_data="mining"
        )
    )

    builder.row(
        types.InlineKeyboardButton(
            text="🤖 Autobot (24 óra)",
            callback_data="autobot"
        ),
        types.InlineKeyboardButton(
            text="🔒 Staking",
            callback_data="staking"
        )
    )

    builder.row(
        types.InlineKeyboardButton(
            text="👥 Meghívás",
            callback_data="invite"
        ),
        types.InlineKeyboardButton(
            text="⏱️ Időzítő",
            callback_data="timer"
        )
    )

    builder.row(
        types.InlineKeyboardButton(
            text="💸 Utalás",
            callback_data="transfer"
        ),
        types.InlineKeyboardButton(
            text="💳 Tárca Csatolása",
            callback_data="wallet"
        )
    )

    builder.row(
        types.InlineKeyboardButton(
            text="ℹ️ Infó & Tokenomika",
            callback_data="info"
        )
    )

    return builder.as_markup()


# ============================================================
# /START
# ============================================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    all_users.add(user_id)
    get_user(user_id)

    text = (
        f"Szia **{message.from_user.first_name}**!\n\n"
        f"Üdvözöllek a **Sajt Token Tesztnet** botban! 🧀\n\n"
        f"Válassz az alábbi lehetőségek közül:"
    )

    await message.answer(
        text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


# ============================================================
# /STATS
# ============================================================

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    total_count = len(all_users)

    total_mined = sum(
        data["balance"]
        for data in user_data.values()
    )

    remaining_pool = max(
        0,
        3_000_000 - total_mined
    )

    stats_text = (
        f"📊 **Rendszer Statisztika:**\n\n"
        f"• Összes regisztrált felhasználó: **{total_count}** fő\n"
        f"• Eddig összesen kitermelve: **{total_mined:.4f}** SAJT\n"
        f"• A 3 milliós bányászható alapból hátra van: "
        f"**{remaining_pool:.4f}** SAJT"
    )

    await message.answer(
        stats_text,
        parse_mode="Markdown"
    )


# ============================================================
# CALLBACKOK
# ============================================================

@dp.callback_query()
async def callback_listener(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    all_users.add(user_id)

    user_info = get_user(user_id)

    data = callback.data

    # --------------------------------------------------------
    # EGYENLEG
    # --------------------------------------------------------

    if data == "balance":

        await callback.answer()

        bal = user_info["balance"]

        await callback.message.answer(
            f"🔥 **Egyenleged:**\n\n"
            f"• Elérhető egyenleg: **{bal:.4f} SAJT**",
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # BÁNYÁSZAT
    # --------------------------------------------------------

    elif data == "mining":

        await callback.answer()

        web_app_url = (
            f"{BASE_URL}/?user_id={user_id}"
        )

        builder = InlineKeyboardBuilder()

        builder.row(
            types.InlineKeyboardButton(
                text="📺 Hirdetés megtekintése",
                web_app=types.WebAppInfo(
                    url=web_app_url
                )
            )
        )

        await callback.message.answer(
            "⛏️ **SAJT Token Bányászat**\n\n"
            "Nézz meg egy AdsGram hirdetést, "
            "és a sikeres megtekintés után megkapod a jutalmat.",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # AUTOBOT
    # --------------------------------------------------------

    elif data == "autobot":

        await callback.answer()

        watched = user_info["ads_watched"]
        now = datetime.datetime.now()

        if (
            user_info["autobot_active"]
            and user_info["autobot_end_time"]
            and now < user_info["autobot_end_time"]
        ):

            remaining = (
                user_info["autobot_end_time"] - now
            )

            hours = int(
                remaining.total_seconds() // 3600
            )

            minutes = int(
                (remaining.total_seconds() % 3600) // 60
            )

            auto_desc = (
                f"🤖 **Auto-Bot Státusz: 🟢 AKTÍV**\n\n"
                f"Az Autobot éppen dolgozik a háttérben!\n\n"
                f"• Hátralévő idő: **{hours} óra {minutes} perc**\n"
                f"• Jelenlegi egyenleg: "
                f"**{user_info['balance']:.4f} SAJT**"
            )

            await callback.message.answer(
                auto_desc,
                parse_mode="Markdown"
            )

        else:

            if (
                user_info["autobot_active"]
                and user_info["autobot_end_time"]
                and now >= user_info["autobot_end_time"]
            ):
                user_info["autobot_active"] = False

            web_app_url = (
                f"{BASE_URL}/?user_id={user_id}"
            )

            builder = InlineKeyboardBuilder()

            builder.row(
                types.InlineKeyboardButton(
                    text="📺 Hirdetés megtekintése",
                    web_app=types.WebAppInfo(
                        url=web_app_url
                    )
                )
            )

            if watched >= 5:

                builder.row(
                    types.InlineKeyboardButton(
                        text="🚀 24 Órás Autobot Indítása",
                        callback_data="start_autobot_24h"
                    )
                )

            auto_desc = (
                f"🤖 **Auto-Bot Vezérlőpult**\n\n"
                f"• **Státusz:** 🔴 INAKTÍV\n"
                f"• **Teljesített hirdetések:** "
                f"**{watched} / 5**\n\n"
                f"Nézz végig 5 hirdetést a Mini Appban, "
                f"majd indítsd el az Autobotot."
            )

            await callback.message.answer(
                auto_desc,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )

    # --------------------------------------------------------
    # AUTOBOT INDÍTÁS
    # --------------------------------------------------------

    elif data == "start_autobot_24h":

        if user_info["ads_watched"] >= 5:

            user_info["autobot_active"] = True

            user_info["autobot_end_time"] = (
                datetime.datetime.now()
                + datetime.timedelta(hours=24)
            )

            user_info["ads_watched"] = 0

            user_info["balance"] += 0.50

            await callback.answer(
                "Sikeresen elindult a 24 órás Autobot!"
            )

            await callback.message.answer(
                "🚀 **Gratulálunk!**\n\n"
                "Az Autobot elindult a következő 24 órára.\n\n"
                "🎁 Induló jutalom: **+0.50 SAJT**",
                parse_mode="Markdown"
            )

        else:

            await callback.answer(
                "Még nincs meg az 5 hirdetés!",
                show_alert=True
            )

    # --------------------------------------------------------
    # STAKING
    # --------------------------------------------------------

    elif data == "staking":

        await callback.answer()

        await callback.message.answer(
            "🔒 **Staking Rendszer**\n\n"
            "Itt tudod majd lekötni a tokenjeidet "
            "extra hozamért.",
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # MEGHÍVÁS
    # --------------------------------------------------------

    elif data == "invite":

        await callback.answer()

        bot_info = await bot.get_me()

        invite_link = (
            f"https://t.me/{bot_info.username}"
            f"?start=ref_{user_id}"
        )

        await callback.message.answer(
            f"👥 **Barátok Meghívása**\n\n"
            f"Oszd meg az alábbi linket:\n\n"
            f"`{invite_link}`",
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # IDŐZÍTŐ
    # --------------------------------------------------------

    elif data == "timer":

        await callback.answer()

        start_t = user_info["start_time"]

        expiry_t = (
            start_t
            + datetime.timedelta(days=365)
        )

        remaining = (
            expiry_t
            - datetime.datetime.now()
        )

        if remaining.total_seconds() > 0:

            days = remaining.days

            hours = (
                remaining.seconds // 3600
            )

            minutes = (
                (remaining.seconds % 3600)
                // 60
            )

            timer_text = (
                "⏱️ **Visszaszámlálás a tőzsdére kerülésig:**\n\n"
                f"• **{days}** nap\n"
                f"• **{hours}** óra\n"
                f"• **{minutes}** perc"
            )

        else:

            timer_text = (
                "⏱️ Letelt az idő, "
                "a tőzsdére kerülés ideje elért!"
            )

        await callback.message.answer(
            timer_text,
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # UTALÁS
    # --------------------------------------------------------

    elif data == "transfer":

        await callback.answer()

        await callback.message.answer(
            "💸 **Token Utalás**\n\n"
            "Itt tudsz majd tokeneket küldeni "
            "más felhasználóknak.",
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # WALLET
    # --------------------------------------------------------

    elif data == "wallet":

        await callback.answer()

        await callback.message.answer(
            "💳 **Tárca Csatolása**\n\n"
            "A TON / Web3 tárca összekötése hamarosan érkezik.",
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # INFO
    # --------------------------------------------------------

    elif data == "info":

        await callback.answer()

        info_text = (
            "ℹ️ **Sajt Token Hivatalos Tokenomika:**\n\n"
            "• **Maximális készlet:** 5,000,000 SAJT\n"
            "• **Utángyártás:** Nincs\n"
            "• **Tito részesedése:** 2,000,000 SAJT\n\n"
            "📊 **Reklám Bevételek Elosztása:**\n"
            "• 💧 **40%** → Likviditás\n"
            "• 🔥 **30%** → Égetés (Burn)\n"
            "• 🛠️ **30%** → Fejlesztés"
        )

        await callback.message.answer(
            info_text,
            parse_mode="Markdown"
        )


# ============================================================
# ADSGRAM REWARD ENDPOINT
# ============================================================

async def handle_reward(request: web.Request):

    # --------------------------------------------------------
    # Titkos kulcs ellenőrzése
    # --------------------------------------------------------

    supplied_secret = request.query.get("key")

    if not supplied_secret:
        logging.warning(
            "Reward kérés titkos kulcs nélkül érkezett."
        )

        return web.json_response(
            {"error": "Unauthorized"},
            status=401
        )

    if not secrets.compare_digest(
        supplied_secret,
        REWARD_SECRET
    ):

        logging.warning(
            "Érvénytelen Reward Secret."
        )

        return web.json_response(
            {"error": "Unauthorized"},
            status=401
        )

    # --------------------------------------------------------
    # Telegram User ID
    # --------------------------------------------------------

    user_id_str = request.query.get("userid")

    if not user_id_str:

        return web.json_response(
            {"error": "Hiányzó userid"},
            status=400
        )

    try:

        user_id = int(user_id_str)

    except ValueError:

        return web.json_response(
            {"error": "Érvénytelen userid"},
            status=400
        )

    # --------------------------------------------------------
    # Dupla callback védelem
    # --------------------------------------------------------

    now = datetime.datetime.now()

    previous_reward = last_reward_time.get(user_id)

    if previous_reward:

        elapsed = (
            now - previous_reward
        ).total_seconds()

        if elapsed < REWARD_COOLDOWN_SECONDS:

            logging.warning(
                f"Dupla reward blokkolva: "
                f"user_id={user_id}"
            )

            return web.json_response({
                "status": "already_processed"
            })

    # --------------------------------------------------------
    # Jutalom
    # --------------------------------------------------------

    user_info = get_user(user_id)

    user_info["balance"] += AD_REWARD

    user_info["ads_watched"] += 1

    last_reward_time[user_id] = now

    all_users.add(user_id)

    logging.info(
        f"AdsGram reward: "
        f"user={user_id}, "
        f"reward={AD_REWARD}, "
        f"balance={user_info['balance']}"
    )

    # --------------------------------------------------------
    # Telegram értesítés
    # --------------------------------------------------------

    try:

        await bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 **AdsGram Hirdetés Teljesítve!**\n\n"
                f"🧀 Jóváírás: **+{AD_REWARD:.2f} SAJT**\n"
                f"📺 Teljesített hirdetések: "
                f"**{user_info['ads_watched']} / 5**\n\n"
                f"💰 Jelenlegi egyenleg: "
                f"**{user_info['balance']:.4f} SAJT**"
            ),
            parse_mode="Markdown"
        )

    except Exception as e:

        logging.error(
            f"Telegram értesítés hiba: {e}"
        )

    return web.json_response({
        "status": "success",
        "user_id": user_id,
        "reward": AD_REWARD,
        "balance": user_info["balance"]
    })


# ============================================================
# MINI APP
# ============================================================

async def index(request: web.Request):

    user_id = request.query.get(
        "user_id",
        ""
    )

    html_content = f"""
<!DOCTYPE html>
<html lang="hu">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width,
        initial-scale=1.0,
        maximum-scale=1.0"
    >

    <title>Sajt Token - AdsGram</title>

    <script src="https://telegram.org/js/telegram-web-app.js"></script>

    <script src="https://sad.adsgram.ai/js/sad.min.js"></script>

    <style>

        body {{
            background:
                linear-gradient(
                    180deg,
                    #171717 0%,
                    #252525 100%
                );

            color: #ffffff;

            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                sans-serif;

            text-align: center;

            padding: 30px 20px;

            margin: 0;

            min-height: 100vh;

            box-sizing: border-box;
        }}

        .container {{
            max-width: 500px;
            margin: 0 auto;
        }}

        .logo {{
            font-size: 60px;
            margin-bottom: 10px;
        }}

        h1 {{
            color: #ffaa00;
            font-size: 25px;
            margin-bottom: 10px;
        }}

        p {{
            color: #cccccc;
            line-height: 1.5;
        }}

        button {{
            background:
                linear-gradient(
                    135deg,
                    #ffaa00,
                    #ffcc33
                );

            color: #171717;

            border: none;

            padding: 16px 28px;

            font-size: 17px;

            font-weight: bold;

            border-radius: 14px;

            cursor: pointer;

            margin-top: 25px;

            box-shadow:
                0 5px 20px
                rgba(255,170,0,0.25);
        }}

        button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}

        #status {{
            margin-top: 25px;
            color: #bbbbbb;
            min-height: 45px;
            line-height: 1.5;
        }}

        .reward {{
            margin-top: 20px;
            padding: 15px;
            border-radius: 12px;
            background: #222222;
            color: #ffcc33;
        }}

    </style>

</head>

<body>

<div class="container">

    <div class="logo">🧀</div>

    <h1>Sajt Token Bányászat</h1>

    <p>
        Nézd végig a hirdetést, és
        a sikeres megtekintés után
        megkapod a SAJT jutalmat.
    </p>

    <button
        id="adButton"
        onclick="triggerAd()"
    >
        📺 Hirdetés Indítása
    </button>

    <div id="status"></div>

    <div class="reward">
        🎁 Jutalom:
        <strong>+{AD_REWARD:.2f} SAJT</strong>
    </div>

</div>


<script>

    const userId = "{user_id}";

    const tg = window.Telegram?.WebApp;

    if (tg) {{
        tg.ready();
        tg.expand();
    }}

    let adController = null;

    try {{

        adController = window.Adsgram.init({{
            blockId: "{ADSGRAM_BLOCK_ID}"
        }});

    }} catch (error) {{

        console.error(
            "AdsGram inicializálási hiba:",
            error
        );

    }}


    async function triggerAd() {{

        const statusEl =
            document.getElementById("status");

        const button =
            document.getElementById("adButton");

        if (!userId) {{

            statusEl.innerText =
                "❌ Hiányzik a Telegram felhasználói azonosító.";

            return;
        }}

        if (!adController) {{

            statusEl.innerText =
                "❌ Az AdsGram nem töltődött be.";

            return;
        }}

        button.disabled = true;

        statusEl.innerText =
            "📺 Hirdetés betöltése...";

        try {{

            await adController.show();

            /*
             * FONTOS:
             *
             * Itt NEM hívjuk meg a /reward endpointot.
             *
             * A szerveroldali jutalmat az AdsGram
             * Reward URL callbackje intézi.
             */

            statusEl.innerText =
                "✅ A hirdetés teljesítve! " +
                "A SAJT jutalom hamarosan jóváírásra kerül.";

        }} catch (error) {{

            console.error(error);

            statusEl.innerText =
                "❌ A hirdetés nem teljesült, " +
                "ezért nincs jutalom.";

            button.disabled = false;

        }}

    }}

</script>

</body>

</html>
"""

    return web.Response(
        text=html_content,
        content_type="text/html"
    )


# ============================================================
# WEB SERVER
# ============================================================

async def web_server():

    app = web.Application()

    app.router.add_get(
        "/",
        index
    )

    app.router.add_get(
        "/reward",
        handle_reward
    )

    return app


# ============================================================
# INDÍTÁS
# ============================================================

if __name__ == "__main__":

    import asyncio

    async def main():

        port = int(
            os.environ.get(
                "PORT",
                8080
            )
        )

        app = await web_server()

        runner = web.AppRunner(app)

        await runner.setup()

        site = web.TCPSite(
            runner,
            "0.0.0.0",
            port
        )

        await site.start()

        logging.info(
            f"Web szerver elindult: port={port}"
        )

        logging.info(
            f"AdsGram Block ID: {ADSGRAM_BLOCK_ID}"
        )

        logging.info(
            "Bot polling elindul..."
        )

        await dp.start_polling(bot)


    asyncio.run(main())
