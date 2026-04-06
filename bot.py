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
    system_instruction="You are the OpenClaw Assistant, a high-intelligence AI. You have access to real-time web search results. Always use the provided search context to give accurate, up-to-date answers. If the search results don't contain the answer, use your own knowledge but mention that you couldn't find recent web data."
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. --- SEARCH FUNCTION ---
def search_web(query):
    """Searches DuckDuckGo and returns a string of results."""
    try:
        # The 'with' statement is correct, but we add a timeout and specific parameters
        with DDGS() as ddgs:
            # We use ddgs.text instead of ddgs.search for better snippet extraction
            # Added region and safesearch to improve result hit-rate
            results = ddgs.text(
                keywords=query, 
                region='wt-wt', 
                safesearch='off', 
                max_results=5
            )
            
            if not results:
                return "No specific web results found for this query."
            
            # Combine Title and Body for better LLM context
            formatted_results = []
            for r in results:
                formatted_results.append(f"Source: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}")
            
            return "\n\n---\n\n".join(formatted_results)
            
    except Exception as e:
        logging.error(f"Search error: {e}")
        return "Search service currently unavailable. Please check your internet connection or library version."

# 3. --- FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦀 OpenClaw Assistant with Web Search is online! Ask me anything about current events.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # IMPROVEMENT: Create a search-optimized query
        # Instead of searching "Hey bot, can you tell me what the weather is in Tokyo?",
        # we search "weather in Tokyo"
        search_query = user_text
        if len(user_text.split()) > 10:
            # Simple heuristic: if the prompt is long, it's a conversation, not a query.
            # In a production app, you'd use the LLM to generate a search query here.
            search_query = " ".join(user_text.split()[:8]) 

        search_results = search_web(search_query)
        
        augmented_prompt = f"""
        WEB SEARCH RESULTS:
        {search_results}
        
        USER QUESTION: 
        {user_text}
        
        Please answer the user question using the web search results provided above. 
        If the results are 'No specific web results found', rely on your internal knowledge but inform the user.
        """

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
