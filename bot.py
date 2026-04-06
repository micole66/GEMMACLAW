import os  # Import os to read environment variables
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai

# --- CONFIGURATION (Now loading from Environment Variables) ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMMA_API_KEY = os.getenv('GEMMA_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME', 'gemma-4-27b-it') 

# Configure Google AI
genai.configure(api_key=GEMMA_API_KEY)
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction="You are the OpenClaw Assistant, a high-intelligence AI powered by Gemma 4."
)

# ... (The rest of your start and handle_message functions remain the same) ...

if __name__ == '__main__':
    # Use the environment variable for the token
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    
    print("OpenClaw Assistant is running on Railway!")
    application.run_polling()