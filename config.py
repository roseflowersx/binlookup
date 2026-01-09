import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration - Your token is added here
BOT_TOKEN = "BOT_TOKEN"

# API configuration
BIN_API_URL = "https://lookup.binlist.net/"
HEADERS = {
    'Accept-Version': '3',
    'User-Agent': 'BinLookupBot/1.0'
}

# Bot messages
MESSAGES = {
    'welcome': "🔍 Welcome to BIN Lookup Bot!\n\n"
               "Send me a BIN (first 6 digits of a card) to get information about it.\n\n"
               "Example: `464235` or `514945`",
    'invalid_bin': "❌ Invalid BIN format. Please send 6 digits.\n\n"
                   "Example: `464235`",
    'error': "⚠️ Error fetching BIN information. Please try again later.",
    'no_data': "No information found for this BIN.",
    'help': "🤖 *BIN Lookup Bot Help*\n\n"
            "• Send any 6-digit BIN to get card information\n"
            "• Example: `464235`\n"
            "• BIN = Bank Identification Number (first 6 digits of a card)\n\n"
            "📊 *Information Provided:*\n"
            "• Card Brand\n• Card Type\n• Bank Name\n• Country\n• Card Level\n• Currency",
    'privacy': "🔒 *Privacy Notice:*\n\n"
               "• I only process the first 6 digits (BIN)\n"
               "• I don't store any BIN data\n"
               "• I don't have access to full card numbers\n"
               "• BIN data is from public databases"
}