import os
import re
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Initialize Flask
app = Flask(__name__)

# Retrieve environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render automatically provides this

# Initialize python-telegram-bot Application
# We disable the updater loop since we are using Webhooks instead of Polling
ptb_app = Application.builder().token(TOKEN).updater(None).build()

# Define the /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hi {user_first_name}! 👋\n\n"
        "I am a Word Counter Bot. Send me any text, and I will count the words and characters for you!"
    )

# Define the text analyzer handler
async def count_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    # Count of raw characters (with and without spaces)
    total_chars_with_spaces = len(text)
    total_chars_no_spaces = len(text.replace(" ", ""))

    # Word counting logic: Using non-word alphanumeric dividers
    # This matches the "CountOfWords" style (treating symbols like :, _, @, etc., as word separators)
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)

    response = (
        f"📊 **Text Statistics:**\n\n"
        f"🔹 **Words:** {word_count}\n"
        f"🔹 **Characters (with spaces):** {total_chars_with_spaces}\n"
        f"🔹 **Characters (no spaces):** {total_chars_no_spaces}"
    )
    
    await update.message.reply_text(response, parse_mode="Markdown")

# Register Handlers
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_words))

# Flask Route to receive updates from Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    if request.method == "POST":
        # Convert the JSON payload to a Telegram Update object
        update = Update.de_json(request.get_json(force=True), ptb_app.bot)
        # Handle the update asynchronously
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(ptb_app.process_update(update))
        loop.close()
    return "OK", 200

# Setup Webhook when the app starts
@app.before_all_requests
def setup_webhook():
    import asyncio
    # Only register webhook if we aren't already set up
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Check current webhook status and set it
    current_info = loop.run_until_complete(ptb_app.bot.get_webhook_info())
    if current_info.url != webhook_url:
        loop.run_until_complete(ptb_app.bot.set_webhook(url=webhook_url))
        
    loop.close()

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
