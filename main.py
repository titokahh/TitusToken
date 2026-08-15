from datetime import datetime
import telebot

# Az új TitusToken bot API tokene
TOKEN = "8797502641:AAHreTwgj6k0EHmoPKfAh0ctd40vQg7Nkc"
bot = telebot.TeleBot(TOKEN)

TOTAL_MAX_SUPPLY = 5_000_000
OWNER_SUPPLY = 2_000_000

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
  return users_db[user_id]


@bot.message_handler(commands=["start", "balance", "mining", "info"])
def handle_commands(message):
  user_id = message.from_user.id
  u_data = get_user(user_id)
  cmd = message.text

  if "/start" in cmd:
    bot.reply_to(
        message,
        "Üdvözlünk a hivatalos TitusToken rendszerben!\nHasználd a /balance,"
        " /mining vagy /info parancsokat.",
    )
  elif "/balance" in cmd:
    circulating = sum(u["balance"] for u in users_db.values()) + OWNER_SUPPLY
    remaining = TOTAL_MAX_SUPPLY - circulating
    bot.reply_to(
        message,
        f"Egyenleg: {u_data['balance']:.2f} TitusToken\nHátralévő készlet:"
        f" {remaining:,}",
    )
  elif "/mining" in cmd:
    bot.reply_to(
        message,
        f"Bányászat státusz: {'Aktív' if u_data['mining_active'] else"
        f" Inaktív}\nMa megtekintett reklámok: {u_data['ads_today']} / 5",
    )
  elif "/info" in cmd:
    bot.reply_to(
        message,
        "TitusToken Info:\nMax Supply: 5,000,000 (Utángyártás soha nem"
        " lesz).",
    )


if __name__ == "__main__":
  print("A TitusToken bot fut...")
  bot.infinity_polling()
