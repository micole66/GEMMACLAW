import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMMA_API_KEY = os.getenv('GEMMA_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME', 'gemma-2-27b-it') # Ensure this is a valid model name

# Configure Google AI
genai.configure(api_key=GEMMA_API_KEY)

# SAFETY SETTINGS: This stops the bot from "encountering an error" when the AI is too shy
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    safety_settings=safety_settings,
    system_instruction="You are the OpenClaw Assistant, a high-intelligence AI powered by Gemma 4."
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

# 2. --- FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦀 OpenClaw Assistant is online! Send me a message.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Generate response
        response = model.generate_content(user_text)
        
        # Check if the response actually has text
        if response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("The AI generated an empty response. Try asking differently.")

    except Exception as e:
        # DEBUG MODE: This sends the ACTUAL error to your Telegram chat
        # Once you fix the error, you can change this back to a generic message
        error_detail = f"❌ Error: {str(e)}"
        logging.error(error_detail)
        await update.message.reply_text(error_detail)

# 3. --- MAIN ---
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("OpenClaw Assistant is running...")
    application.run_polling()
