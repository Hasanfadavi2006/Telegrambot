from openai import OpenAI
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext
import os
import certifi
import time
import logging

API_KEY = "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"
client = OpenAI(api_key=API_KEY)

def setup_logging(user_id):
    logger = logging.getLogger(f'user_{user_id}')
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    log_directory = os.path.abspath(os.path.dirname(__file__))
    log_filename = os.path.join(log_directory, f'{user_id}.log')
    try:
        fh = logging.FileHandler(log_filename, encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info("Logger setup complete.")
    except Exception as e:
        logging.error(f"Failed to set up logger for user {user_id}: {e}")
    return logger

def run_bot():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting the bot...")

    os.environ['SSL_CERT_FILE'] = certifi.where()
    bot_token = "6823019450:AAHdCIftRTrGnPoglIn58Vk48de5RIYvvq8"
    application = ApplicationBuilder().token(bot_token).build()
    user_chat_histories = {}

    def manage_chat_history(user_id):
        if user_id in user_chat_histories:
            total_tokens = sum([len(msg['content'].split()) for msg in user_chat_histories[user_id] if msg['content']])
            while total_tokens > 2000 and len(user_chat_histories[user_id]) > 1:
                removed_message = user_chat_histories[user_id].pop(0)
                total_tokens -= len(removed_message['content'].split())

    def ask_gpt4(user_id, question):
        if not question:
            return "لطفا تنها به شکل متنی با من ارتباط بگیرید"

        # SYSTEM PROMPT ثابت
        SYSTEM_PROMPT = "You are a smart assistant. Answer concisely and accurately."
        if user_id not in user_chat_histories:
            user_chat_histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
        manage_chat_history(user_id)
        try:
            user_chat_histories[user_id].append({"role": "user", "content": question})

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=user_chat_histories[user_id],
                temperature=0.1,
                max_tokens=1024,
                top_p=1,
            )
            answer = response.choices[0].message.content.strip()
            user_chat_histories[user_id].append({"role": "assistant", "content": answer})

            logger = setup_logging(user_id)
            logger.info(f"Question: {question}")
            logger.info(f"Answer: {answer}")

            return answer
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return "یک خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کنید."

    async def handle_message(update: Update, context: CallbackContext):
        user_id = update.message.from_user.id
        question = update.message.text
        answer = ask_gpt4(user_id, question)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

while True:
    try:
        run_bot()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        time.sleep(5)
