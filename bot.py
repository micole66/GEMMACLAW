import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from duckduckgo_search import DDGS 

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
    system_instruction="You are the OpenClaw Assistant. You are helpful, concise, and intelligent."
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. --- SEARCH FUNCTION ---
def search_web(query):
    """Searches DuckDuckGo and returns a string of results."""
    try:
        with DDGS() as ddgs:
            # Use a clean search query
            results = list(ddgs.text(keywords=query, region='wt-wt', safesearch='off', max_results=5))
            
            if not results:
                return None
            
            formatted_results = []
            for r in results:
                formatted_results.append(f"Source: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}")
            
            return "\n\n---\n\n".join(formatted_results)
    except Exception as e:
        logging.error(f"Search error: {e}")
        return None

# 3. --- LOGIC HELPERS ---

async def decide_search_needed(user_text):
    """Uses the LLM to decide if the query needs real-time web data."""
    decision_prompt = f"""
    Analyze the user message: "{user_text}"
    Does this message require real-time information, current events, news, or specific facts that might change (like weather, stocks, or recent product releases)?
    Respond with ONLY the word 'YES' or 'NO'.
    """
    response = model.generate_content(decision_prompt)
    return "YES" in response.text.upper()

async def generate_search_query(user_text):
    """Uses the LLM to turn a conversational sentence into a clean search keyword."""
    query_prompt = f"Extract the core search keywords from this sentence: '{user_text}'. Respond ONLY with the keywords."
    response = model.generate_content(query_prompt)
    return response.text.strip()

# 4. --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦀 OpenClaw Assistant is online! I can search the web for current events if needed.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # STEP 1: Decide if we actually need to search
        needs_search = await decide_search_needed(user_text)
        
        search_context = ""
        if needs_search:
            # STEP 2: Generate a CLEAN search query (not the whole sentence)
            clean_query = await generate_search_query(user_text)
            logging.info(f"Searching for: {clean_query}")
            
            # Show user we are searching (Optional but good UX)
            # await update.message.reply_text("🔍 Searching the web...") 
            
            results = search_web(clean_query)
            if results:
                search_context = f"\n\nWEB SEARCH RESULTS:\n{results}"
            else:
                search_context = "\n\n(Note: No recent web results found for this specific topic.)"

        # STEP 3: Final Prompt Construction
        final_prompt = f"""
        You are the OpenClaw Assistant. 
        Use the search context below if it's relevant to answer the user. 
        If the context is empty or irrelevant, use your own knowledge.

        {search_context}

        USER QUESTION: {user_text}
        """

        response = model.generate_content(final_prompt)
        
        if response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("I'm sorry, I couldn't generate a response.")

    except Exception as e:
        logging.error(f"Main Error: {e}")
        await update.message.reply_text("❌ An error occurred while processing your request.")

# 5. --- MAIN ---
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("OpenClaw Assistant with Smart Search is running...")
    application.run_polling()
