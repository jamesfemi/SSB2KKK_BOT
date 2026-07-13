import os
import re
import logging
import asyncio  # Make sure asyncio is imported at the top!
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Retrieve the token from Render Environment Variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Define the /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hi {user_first_name}! 👋\n\n"
        "I am a Word Counter Bot running on a background worker. "
        "Send me any text, and I will count the words and characters for you!"
    )

# Define the text analyzer handler
async def count_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    total_chars_with_spaces = len(text)
    total_chars_no_spaces = len(text.replace(" ", ""))

    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)

    response = (
        f"📊 **Text Statistics:**\n\n"
        f"🔹 **Words:** {word_count}\n"
        f"🔹 **Characters (with spaces):** {total_chars_with_spaces}\n"
        f"🔹 **Characters (no spaces):** {total_chars_no_spaces}"
    )
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def start_bot():
    """Async function to initialize and run the polling loop."""
    if not TOKEN:
        logger.error("No TELEGRAM_TOKEN found in environment variables!")
        return

    # Initialize python-telegram-bot Application
    ptb_app = Application.builder().token(TOKEN).build()

    # Register Handlers
    ptb_app.add_handler(CommandHandler("start", start))
    ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_words))

    logger.info("Bot initialized. Starting polling loop...")
    
    # We initialize and run polling within the active async context
    await ptb_app.initialize()
    await ptb_app.updater.start_polling(drop_pending_updates=True)
    await ptb_app.start()
    
    logger.info("Bot is running and listening via polling.")
    
    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping bot...")
    finally:
        await ptb_app.updater.stop()
        await ptb_app.stop()
        await ptb_app.shutdown()

def main():
    # Force creation and management of the event loop for Python 3.14+
    try:
        asyncio.run(start_bot())
    except Exception as e:
        logger.critical(f"Unhandled exception in main loop: {e}", exc_info=True)

if __name__ == "__main__":
    main()
