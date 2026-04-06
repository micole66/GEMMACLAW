import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai

# 1. --- CONFIGURATION ---
# These are pulled from your Railway "Variables" tab
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMMA_API_KEY = os.getenv('GEMMA_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME', 'gemma-4-27b-it') 

# Configure Google AI
genai.configure(api_key=GEMMA_API_KEY)
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction="You are the OpenClaw Assistant, a high-intelligence AI powered by Gemma 4. You provide deep, reasoned, and logical answers."
)

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

# 2. --- FUNCTION DEFINITIONS (Must come BEFORE the main block) ---

# This is the 'start' function that was missing or misplaced
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦀 Hello! I am the OpenClaw Assistant, powered by the largest Gemma 4 Thinking Model. How can I help you today?"
    )

# This handles the actual AI chatting
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Show "typing..." action in Telegram
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Generate response from Gemma 4
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("I encountered an error. Please try again.")

# 3. --- THE MAIN EXECUTION BLOCK (Must come LAST) ---
if __name__ == '__main__':
    # Build the application
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Connect the functions to the commands
    # Now 'start' and 'handle_message' are already defined above, so this will work!
    start_handler = CommandHandler('start', start)
    msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    
    print("OpenClaw Assistant is starting up...")
    application.run_polling()
