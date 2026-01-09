#!/usr/bin/env python3
import logging
import re

import httpx
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ContextTypes,
    filters,
)

import config

# ------------------ Logging ------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ------------------ Helpers ------------------
def validate_bin(bin_number: str) -> bool:
    """Validate BIN format (6 digits)"""
    return bool(re.fullmatch(r"\d{6}", bin_number or ""))


async def fetch_bin_info(bin_number: str):
    """Fetch BIN information from API (async)"""
    url = f"{config.BIN_API_URL}{bin_number}"
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=config.HEADERS) as client:
            r = await client.get(url)

        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None

        logger.error("API Error: %s %s", r.status_code, r.text[:200])
        return None
    except Exception as e:
        logger.error("Request failed: %s", e)
        return None


def format_bin_info(bin_data: dict | None, bin_number: str) -> str:
    """Format BIN information for display"""
    if not bin_data:
        return config.MESSAGES["no_data"]

    lines = []
    lines.append(f"🔢 *BIN:* `{bin_number}`")
    lines.append("")

    if bin_data.get("scheme"):
        lines.append(f"🏦 *Brand:* {str(bin_data['scheme']).upper()}")

    if bin_data.get("type"):
        lines.append(f"💳 *Type:* {str(bin_data['type']).capitalize()}")

    if bin_data.get("bank"):
        bank = bin_data["bank"] or {}
        if bank.get("name"):
            lines.append(f"🏛️ *Bank:* {bank['name']}")
        if bank.get("url"):
            lines.append(f"🌐 *Website:* {bank['url']}")
        if bank.get("phone"):
            lines.append(f"📞 *Phone:* {bank['phone']}")

    if bin_data.get("country"):
        country = bin_data["country"] or {}
        country_info = []
        if country.get("name"):
            country_info.append(country["name"])
        if country.get("emoji"):
            country_info.append(country["emoji"])
        if country.get("currency"):
            country_info.append(f"({country['currency']})")
        if country_info:
            lines.append(f"🌍 *Country:* {' '.join(country_info)}")

    if bin_data.get("brand"):
        lines.append(f"⭐ *Level:* {str(bin_data['brand']).capitalize()}")

    if "prepaid" in bin_data and bin_data["prepaid"] is not None:
        lines.append(f"💳 *Prepaid:* {'Yes' if bin_data['prepaid'] else 'No'}")

    lines.append("")
    lines.append("📝 *Note:* This shows card type only, not card validity.")
    lines.append("ℹ️ Use `/help` for more information.")

    return "\n".join(lines)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 Lookup a BIN", switch_inline_query_current_chat="")],
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
                InlineKeyboardButton("🔒 Privacy", callback_data="privacy"),
            ],
        ]
    )


# ------------------ Handlers ------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        config.MESSAGES["welcome"],
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(config.MESSAGES["help"], parse_mode="Markdown")


async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(config.MESSAGES["privacy"], parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if not validate_bin(text):
        await update.message.reply_text(config.MESSAGES["invalid_bin"], parse_mode="Markdown")
        return

    await update.message.chat.send_action(ChatAction.TYPING)

    bin_data = await fetch_bin_info(text)

    if bin_data is None:
        # 404 বা no data
        await update.message.reply_text(config.MESSAGES["no_data"], parse_mode="Markdown")
        return

    response_text = format_bin_info(bin_data, text)

    await update.message.reply_text(
        response_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("🔄 Lookup Another", switch_inline_query_current_chat=""),
                InlineKeyboardButton("❓ Help", callback_data="help"),
            ]]
        ),
    )


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = (update.inline_query.query or "").strip()

    if not validate_bin(q):
        return

    bin_data = await fetch_bin_info(q)
    if not bin_data:
        return

    response_text = format_bin_info(bin_data, q)

    scheme = str(bin_data.get("scheme") or "").upper()
    ctype = str(bin_data.get("type") or "").capitalize()

    result = InlineQueryResultArticle(
        id=q,
        title=f"BIN: {q}",
        description=f"{scheme} - {ctype}".strip(" -"),
        input_message_content=InputTextMessageContent(
            response_text,
            parse_mode="Markdown",
        ),
    )

    await update.inline_query.answer([result], cache_time=5)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    if cq.data == "help":
        await cq.edit_message_text(text=config.MESSAGES["help"], parse_mode="Markdown")
    elif cq.data == "privacy":
        await cq.edit_message_text(text=config.MESSAGES["privacy"], parse_mode="Markdown")


# ------------------ Main ------------------
def main():
    application = Application.builder().token(config.BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("privacy", privacy_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(CallbackQueryHandler(callback_handler))

    logger.info("Starting BIN Lookup Bot...")
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()