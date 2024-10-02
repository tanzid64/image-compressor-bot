import os
import io
from PIL import Image
import logging
from telegram import Update, Bot
from telegram.ext import (
    Application,
    # ApplicationBuilder, for local development
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv

print("Starting bot server...")

# Load environment variables
load_dotenv()

TG_BOT_ACCESS_TOKEN = os.environ.get("TG_BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = Bot(TG_BOT_ACCESS_TOKEN)

# Function for /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    reply_msg = f"""
    Welcome to the image compression bot!
    Hi, {update.effective_user.first_name}! I'm a bot, please talk to me!
    Type /help to get a list of available commands.
    """
    await context.bot.send_message(chat_id=chat_id, text=reply_msg)


# Function for unknown command
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


# Function to handle /help command
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
        Here are the available commands:
        /start - Start interacting with the bot
        /help - Get a list of all available commands
        To compress a photo just send a photo.
        """
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


# Function to compress the image using Pillow
def compress_image_data(image_bytes, quality=30) -> io.BytesIO:
    img = Image.open(io.BytesIO(image_bytes))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return buffer


# Function to handle image compression
async def handle_compress_image(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.message.reply_text("Photo compressing...")
    try:
        img = await update.message.photo[-1].get_file(
            timeout=20
        )  # Get highest resolution photo
        photo_data = await img.download_as_bytearray()  # Download photo as bytearray

        compressed_image = compress_image_data(photo_data)  # Compress the image

        await update.message.reply_photo(
            compressed_image, caption="Here is your compressed photo!"
        )
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        await update.message.reply_text("Sorry, I couldn't compress the image.")

# For local development
# if __name__ == "__main__":
#     # Build Application
#     application = ApplicationBuilder().token(TG_BOT_ACCESS_TOKEN).build()

#     # Handlers
#     start_handler = CommandHandler("start", start)
#     help_handler = CommandHandler("help", help)
#     unknown_handler = MessageHandler(filters.COMMAND, unknown)
#     compress_handler = MessageHandler(
#         filters.PHOTO, handle_compress_image
#     )  # Renamed handler

#     # Add Handlers
#     application.add_handler(start_handler)
#     application.add_handler(help_handler)
#     application.add_handler(unknown_handler)
#     application.add_handler(compress_handler)

#     # Run Bot
#     application.run_polling()


# Google Cloud Functions entry point
def telegram_bot_function(request):
    if request.method == "POST":
        # Process Telegram update
        update = Update.de_json(request.get_json(force=True), bot)
        application = Application.builder().token(TG_BOT_ACCESS_TOKEN).build()

        # Add Handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help))
        application.add_handler(MessageHandler(filters.COMMAND, unknown))
        application.add_handler(MessageHandler(filters.PHOTO, handle_compress_image))

        application.process_update(update)

        return "OK", 200
    return "Bad Request", 400
