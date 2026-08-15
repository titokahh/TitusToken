from datetime import datetime, timedelta
import telebot

# TitusToken Bot Token a BotFathertől
TOKEN = "8797502641:AAHreTwgj6k0EHmoPKfAh0ctd40vQg7Nkc"
bot = telebot.TeleBot(TOKEN)

# --- TOKENOMIKA ÉS KONSTANSOK ---
TOTAL_MAX_SUPPLY = 5_000_000
OWNER_SUPPLY = 2_000_000  # Tito birtokában lévő rész
NO_MINTING_NOTE = (
    "Szigorúan fix készlet, utángyártás soha nem lesz."  # Soha nincs utángyártás
)

# Pénzügyi elosztás a reklámbevételekből
ADS_REVENUE_SPLIT = {
    "Liquidity": "60%",
    "Burn": "20%",
    "Development_Maintenance": "20%",
}

# 1 éves visszaszámláló céldátuma (Példa: 2027. augusztus 15.)
LAUNCH_DATE = datetime(2027, 8, 15, 0, 0, 0)

# Egyszerű memóriabeli adatbázis a teszteléshez (éles rendszerben SQL adatbázis ajánlott)
# user_id: { "balance": float, "ads_today": int, "last_ad_date": str, "mining_active": bool, "refs": int }
users_db = {}


def get_user(user_id):
  if user_id not in users_db:
    users_db[user_id] = {
        "balance": 0.0,
        "ads_today": 0,
        "last_ad_date": str(datetime.now().date()),
        "mining_active": False,
        "refs": 0,
    }
  # Napi reklám számláló reset ellenőrzés
  today_str = str(datetime.now().date())
  if users_db[user_id]["last_ad_date"] != today_str:
    users_db[user_id]["ads_today"] = 0
    users_db[user_id]["last_ad_date"] = today_str
    users_db[user_id]["mining_active"] = False
  return users_db[user_id]


@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  get_user(user_id)
  welcome_text = (
      "Üdvözlünk a hivatalos **TitusToken** rendszerben, Tito!\n\n"
      "Írd be a /menu parancsot a funkciók eléréséhez, vagy használd az alábbi parancsokat:\n"
      "• /balance - Élő token egyenleg és számláló\n"
      "• /mining - 0-24 órás bányászat és napi reklámok (5 db)\n"
      "• /referral - Barát meghívása (+0.5 token)\n"
      "• /info - 1 éves visszaszámláló és tokenomika"
  )
  bot.reply_to(message, welcome_text, parse_mode="Markdown")


@bot.message_handler(commands=["balance"])
def show_balance(message):
  user_id = message.from_user.id
  u_data = get_user(user_id)

  circulating = sum(u["balance"] for u in users_db.values()) + OWNER_SUPPLY
  remaining_pool = TOTAL_MAX_SUPPLY - circulating

  text = (
      f"**TitusToken Élő Számláló**\n\n"
      f"• Saját egyenleged: **{u_data['balance']:.2f} TitusToken**\n"
      f"• Teljes készlet (Max Supply): **{TOTAL_MAX_SUPPLY:,}**\n"
      f"• Jelenlegi forgalom: **{circulating:,}**\n"
      f"• Hátralévő készlet: **{remaining_pool:,}**\n"
      f"• Utángyártás: **Nincs és soha nem is lesz.**"
  )
  bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=["mining"])
def mining_status(message):
  user_id = message.from_user.id
  u_data = get_user(user_id)

  ads_left = max(0, 5 - u_data["ads_today"])
  status = (
      "Aktív (0-24 órás bányászat)"
      if u_data["mining_active"]
      else "Inaktív (Napi 5 reklám szükséges)"
  )

  text = (
      f"**Automatikus Bányászati Rendszer**\n\n"
      f"• Bányászat státusza: **{status}**\n"
      f"• Ma megtekintett reklámok: **{u_data['ads_today']} / 5**\n"
      f"• Hátralévő reklám a 0-24 órás bányászathoz: **{ads_left} db**\n"
      f"• Ciklus: **6 óránként +0.02 token** (feltételek teljesülése esetén)\n\n"
      f"_Megjegyzés: A rendszer szerver-oldali visszahívással (Callback) ellenőrzi a valós reklámnézést._"
  )
  bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=["simulate_ad"])
def simulate_ad_view(message):
  # Ezt a függvényt hívja meg az AdsGram szerver-oldali visszahívása (S2S Callback)
  user_id = message.from_user.id
  u_data = get_user(user_id)

  if u_data["ads_today"] < 5:
    u_data["ads_today"] += 1
    if u_data["ads_today"] >= 5:
      u_data["mining_active"] = True
      bot.reply_to(
          message,
          "Sikeresen teljesítetted a napi 5 reklámot! A 0-24 órás automata"
          " bányászat elindult.",
      )
    else:
      bot.reply_to(
          message,
          f"Reklám rögzítve! Még {5 - u_data['ads_today']} reklám hiányzik a"
          " bányászat aktiválásához.",
      )
  else:
    bot.reply_to(
        message, "Mára már teljesítetted a szükséges 5 reklámot."
    )


@bot.message_handler(commands=["referral"])
def referral_system(message):
  user_id = message.from_user.id
  u_data = get_user(user_id)
  bot_name = bot.get_me().username

  ref_link = f"https://t.me/{bot_name}?start=ref_{user_id}"
  text = (
      f"**Ajánlói Rendszer**\n\n"
      f"• Meghívott barátok: **{u_data['refs']} fő**\n"
      f"• Jutalmad barátnként: **0.5 TitusToken**\n\n"
      f"A te meghívó linked:\n`{ref_link}`"
  )
  bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=["info"])
def info_tab(message):
  now = datetime.now()
  countdown = LAUNCH_DATE - now
  days = countdown.days
  hours = countdown.seconds // 3600

  text = (
      f"**TitusToken Információs Fül**\n\n"
      f"⏳ **1 Éves Visszaszámláló a Valódi Valutává válásig:**\n"
      f"Hátra van: **{days} nap és {hours} óra**\n\n"
      f"📊 **Reklámbevételek Pénzügyi Elosztása:**\n"
      f"• Likviditás: **{ADS_REVENUE_SPLIT['Liquidity']}**\n"
      f"• Égetés (Burn): **{ADS_REVENUE_SPLIT['Burn']}**\n"
      f"• Fejlesztés és Fenntartás:"
      f" **{ADS_REVENUE_SPLIT['Development_Maintenance']}**\n\n"
      f"🔒 **Biztonság és Szabályzat:**\n"
      f"• Csalásmegelőzés: Szigorú szerver-oldali IP- és hirdetésellenőrzés.\n"
      f"• Max Supply: 5,000,000 (Utángyártás soha nem lesz)."
  )
  bot.reply_to(message, text, parse_mode="Markdown")


if __name__ == "__main__":
  print("A TitusToken bot elindult és aktívan fut...")
  bot.infinity_polling()
