import os
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = "8797502641:AAFLNc-S9Lmeo3jGvnN0Up-Ff7FdJZdd7DE"
bot = telebot.TeleBot(TOKEN)

# Rendszer adatok
user_count = 1
countdown_active = False
max_supply = 5_000_000
tito_share = 2_000_000
total_mined_tokens = 0.0

# Felhasználói adatok tárolása
user_data = {}


def get_user_info(chat_id):
  if chat_id not in user_data:
    user_data[chat_id] = {
        "ads_watched": 0,
        "auto_claim": False,
        "referrals": 0,
        "balance": 0.0,
    }
  return user_data[chat_id]


def get_info_text():
  phase_status = (
      "⏳ **Visszaszámlálás folyamatban (1 év)**"
      if countdown_active
      else "🧪 **Teszt fázis** (Várakozás a 2,000 felhasználóra)"
  )
  remaining_pool = max_supply - tito_share - total_mined_tokens

  return (
      "📊 **TitusToken - Élő Rendszer Státusz & Keret**\n\n"
      f"👥 **Felhasználók:** {user_count} / 2,000\n"
      f"📌 **Jelenlegi státusz:** {phase_status}\n\n"
      "💎 **Élő Token Keret & Készlet:**\n"
      f"• **Teljes készlet:** {max_supply:,} token\n"
      f"• **Tito részesedése:** {tito_share:,} token\n"
      f"• **Eddig kitermelt/kiosztott:** {total_mined_tokens:.2f} token\n"
      f"• **Élő bányászható keret:** {remaining_pool:.2f} token\n\n"
      "⚙️ **Főbb Paraméterek:**\n"
      "• **Utángyártás:** Nincs\n"
      "• **Bányászati ciklus:** 6 óránként (0.02 token)\n"
      "• **Auto-claim:** 5 valódi reklám megtekintéséért 24 órás auto-claim\n"
      "• **Ajánlói rendszer:** 0.5 token az első bányászat után\n\n"
      "💰 **Nyitáskori reklámbevétel elosztás:**\n"
      "• **60%** -> Likviditás\n"
      "• **20%** -> Égetés (Burn)\n"
      "• **20%** -> Fejlesztés és fenntartás"
  )


@bot.message_handler(commands=["start"])
def send_welcome(message):
  markup = InlineKeyboardMarkup()
  markup.row(InlineKeyboardButton("ℹ️ Infó & Státusz", callback_data="info_menu"))
  markup.row(
      InlineKeyboardButton(
          "📺 Szorgalmi feladat & Verseny", callback_data="ads_menu"
      )
  )
  bot.send_message(
      message.chat.id,
      "Szia Tito! Üdvözöllek a TitusToken botban. Válassz az alábbi"
      " lehetőségek közül:",
      reply_markup=markup,
  )


@bot.message_handler(commands=["info"])
def send_info_command(message):
  bot.send_message(message.chat.id, get_info_text(), parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
  chat_id = call.message.chat.id
  u_info = get_user_info(chat_id)

  if call.data == "info_menu":
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⬅️ Vissza", callback_data="main_menu"))
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=get_info_text(),
        parse_mode="Markdown",
        reply_markup=markup,
    )

  elif call.data == "ads_menu":
    bot.answer_callback_query(call.id)
    ads_count = u_info["ads_watched"]
    refs_count = u_info["referrals"]
    status_text = (
        "✅ **Aktív (24 órás auto-claim)**"
        if u_info["auto_claim"]
        else f"⏳ Még {5 - ads_count} VALÓDI reklám szükséges a 24 órás"
        " auto-claimhez."
    )

    text = (
        "📺 **Szorgalmi Feladat & Nyitási Verseny**\n\n"
        "⚠️ *Fontos: Csak a VALÓDI hirdetések megtekintése érvényes!*\n\n"
        f"• Megtekintett valós reklámjaid: **{ads_count} / 5**\n"
        f"• Auto-claim státusz: {status_text}\n"
        f"• Meghívott felhasználóid: **{refs_count} db**\n\n"
        "🏆 **Verseny szabályok (Nyitásig):**\n"
        "1️⃣ Aki a legtöbb VALÓDI reklámot nézi meg -> **500 token** jutalom!\n"
        "2️⃣ Aki a legtöbb felhasználót hozza -> **500 token** jutalom!\n\n"
        "💰 **Bevétel elosztás nyitáskor:**\n"
        "• 60% Likviditás | 20% Égetés | 20% Fejlesztés & Fenntartás"
    )
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(
            "▶️ Valódi reklám megtekintése",
            url="https://example.com/valodi-reklam",
        )
    )
    markup.row(
        InlineKeyboardButton(
            "🔄 Ellenőrzés / Frissítés", callback_data="check_ads"
        )
    )
    markup.row(
        InlineKeyboardButton(
            "👥 Barát meghívása (Ajánlás szimuláció)", callback_data="simulate_ref"
        )
    )
    markup.row(InlineKeyboardButton("⬅️ Vissza", callback_data="main_menu"))
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=markup,
    )

  elif call.data == "check_ads":
    bot.answer_callback_query(
        call.id,
        "Ellenőrzés: Csak a hitelesített valós megtekintések adódnak hozzá!",
        show_alert=True,
    )

  elif call.data == "simulate_ref":
    u_info["referrals"] += 1
    bot.answer_callback_query(
        call.id, "Sikeres ajánlás regisztrálva (+1 barát)!"
    )

    ads_count = u_info["ads_watched"]
    refs_count = u_info["referrals"]
    status_text = (
        "✅ **Aktív (24 órás auto-claim)**"
        if u_info["auto_claim"]
        else f"⏳ Még {5 - ads_count} VALÓDI reklám szükséges a 24 órás"
        " auto-claimhez."
    )

    text = (
        "📺 **Szorgalmi Feladat & Nyitási Verseny**\n\n"
        "⚠️ *Fontos: Csak a VALÓDI hirdetések megtekintése érvényes!*\n\n"
        f"• Megtekintett valós reklámjaid: **{ads_count} / 5**\n"
        f"• Auto-claim státusz: {status_text}\n"
        f"• Meghívott felhasználóid: **{refs_count} db**\n\n"
        "🏆 **Verseny szabályok (Nyitásig):**\n"
        "1️⃣ Aki a legtöbb VALÓDI reklámot nézi meg -> **500 token** jutalom!\n"
        "2️⃣ Aki a legtöbb felhasználót hozza -> **500 token** jutalom!"
    )
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(
            "▶️ Valódi reklám megtekintése",
            url="https://example.com/valodi-reklam",
        )
    )
    markup.row(
        InlineKeyboardButton(
            "🔄 Ellenőrzés / Frissítés", callback_data="check_ads"
        )
    )
    markup.row(
        InlineKeyboardButton(
            "👥 Barát meghívása (Ajánlás szimuláció)", callback_data="simulate_ref"
        )
    )
    markup.row(InlineKeyboardButton("⬅️ Vissza", callback_data="main_menu"))
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=markup,
    )

  elif call.data == "main_menu":
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("ℹ️ Infó & Státusz", callback_data="info_menu"))
    markup.row(
        InlineKeyboardButton(
            "📺 Szorgalmi feladat & Verseny", callback_data="ads_menu"
        )
    )
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"Szia Tito! Üdvözöllek a TitusToken botban. Válassz az alábbi"
        " lehetőségek közül:",
        reply_markup=markup,
    )


if __name__ == "__main__":
  bot.infinity_polling()
