import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from duckduckgo_search import DDGS  # <--- New Search Library

# 1. --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMMA_API_KEY = os.getenv('GEMMA_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME', 'gemma-4-31b-it')

genai.configure(api_key=GEMMA_API_KEY)

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    safety_settings=safety_settings,
    system_instruction="You are the OpenClaw Assistant, a high-intelligence AI. You have access to real-time web search results. Always use the provided search context to give accurate, up-to-date answers. If the search results don't contain the answer, use your own knowledge but mention that you couldn't find recent web data."
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. --- SEARCH FUNCTION ---
def search_web(query):
    """Searches DuckDuckGo and returns a string of results."""
    try:
        with DDGS() as ddgs:
            # Get top 5 results
            results = [r['body'] for r in ddgs.text(query, max_results=5)]
            return "\n\n".join(results) if results else "No web results found."
    except Exception as e:
        logging.error(f"Search error: {e}")
        return "Search service currently unavailable."

# 3. --- FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦀 OpenClaw Assistant with Web Search is online! Ask me anything about current events.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # STEP 1: Search the web for the user's question
        # We tell the user we are searching so they don't think it's frozen
        search_results = search_web(user_text)
        
        # STEP 2: Create a "Prompt" that combines Search Results + User Question
        augmented_prompt = f"""
        WEB SEARCH RESULTS:
        {search_results}
        
        USER QUESTION: 
        {user_text}
        
        Please answer the user question using the web search results provided above.
        """

        # STEP 3: Generate response from Gemma 4
        response = model.generate_content(augmented_prompt)
        
        if response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("The AI generated an empty response. Try rephrasing.")

    except Exception as e:
        error_detail = f"❌ Error: {str(e)}"
        logging.error(error_detail)
        await update.message.reply_text(error_detail)

# 4. --- MAIN ---
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("OpenClaw Assistant with Search is running...")
    application.run_polling()
