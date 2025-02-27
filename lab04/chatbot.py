from telegram import Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          CallbackContext)
from ChatGPT_HKBU import HKBU_ChatGPT
import configparser
import logging
import redis

global redis1
global chatgpt  # Declare the global variable for chatgpt

def main():
    # Load your token and create an Updater for your Bot
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8-sig')
    updater = Updater(token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher
    
    global redis1
    redis1 = redis.Redis(host=(config['REDIS']['HOST']),
                         password=(config['REDIS']['PASSWORD']),
                         port=int((config['REDIS']['REDISPORT'])),
                         decode_responses=config['REDIS'].getboolean('DECODE_RESPONSE'),
                         username=(config['REDIS']['USER_NAME']))
    
    # Initialize ChatGPT instance
    global chatgpt
    chatgpt = HKBU_ChatGPT(config)  # Use config to initialize the ChatGPT instance
    
    # Set logging configuration
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    
    # Register a dispatcher for ChatGPT (ensure this is registered first)
    chatgpt_handler = MessageHandler(Filters.text, equiped_chatgpt)  # Capture all text messages
    dispatcher.add_handler(chatgpt_handler)

    # Register other command handlers
    dispatcher.add_handler(CommandHandler("add", add))
    # dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("set", set_key))       # /set <key> <value>
    dispatcher.add_handler(CommandHandler("get", get_key))       # /get <key>
    dispatcher.add_handler(CommandHandler("delete", delete_key)) # /delete <key>
    dispatcher.add_handler(CommandHandler("hello", hello))       # /hello <name> -> Greeting handler
    
    # Start the bot
    updater.start_polling()
    updater.idle()

#Handle the ChatGPT interaction
def equiped_chatgpt(update, context):
    global chatgpt
    logging.info("Received message: %s", update.message.text)  # Debug log for received message
    try:
        reply_message = chatgpt.submit(update.message.text)  # Send the user's message to ChatGPT
        logging.info("ChatGPT reply: %s", reply_message)  # Debug log for ChatGPT's response
        context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)
    except Exception as e:
        logging.error("Error in ChatGPT processing: %s", str(e))
        context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, there was an error.")

def echo(update, context):
    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("Context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)

# # Define command handlers
# def help_command(update: Update, context: CallbackContext) -> None:
#     """Send a message when the command /help is issued."""
#     update.message.reply_text('Helping you helping you.')
# Define the /hello command handler
def hello(update: Update, context: CallbackContext) -> None:
    """Send a personalized greeting when the command /hello is issued."""
    try:
        if len(context.args) == 1:
            name = context.args[0]  # Extract the name from the command
            greeting = f"Good day, {name}!"
            update.message.reply_text(greeting)
        else:
            update.message.reply_text('Usage: /hello <name>')
    except Exception as e:
        update.message.reply_text(f'Error: {str(e)}')

def add(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /add is issued."""
    try:
        global redis1
        logging.info(context.args[0])
        msg = context.args[0]  # /add keyword <-- this should store the keyword
        redis1.incr(msg)
        update.message.reply_text('You have said ' + msg + ' for ' +
                                  redis1.get(msg) + ' times.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')

# Handle the set command
def set_key(update: Update, context: CallbackContext) -> None:
    """Set a key-value pair in Redis when the command /set is issued."""
    try:
        global redis1
        if len(context.args) != 2:
            update.message.reply_text('Usage: /set <key> <value>')
            return
        key, value = context.args
        redis1.set(key, value)
        update.message.reply_text(f'Successfully set {key} to {value}.')
    except Exception as e:
        update.message.reply_text(f'Error: {str(e)}')

# Handle the get command
def get_key(update: Update, context: CallbackContext) -> None:
    """Get the value of a key from Redis when the command /get is issued."""
    try:
        global redis1
        if len(context.args) != 1:
            update.message.reply_text('Usage: /get <key>')
            return
        key = context.args[0]
        value = redis1.get(key)
        if value:
            update.message.reply_text(f'The value of {key} is {value}.')
        else:
            update.message.reply_text(f'{key} does not exist.')
    except Exception as e:
        update.message.reply_text(f'Error: {str(e)}')

# Handle the delete command
def delete_key(update: Update, context: CallbackContext) -> None:
    """Delete a key from Redis when the command /delete is issued."""
    try:
        global redis1
        if len(context.args) != 1:
            update.message.reply_text('Usage: /delete <key>')
            return
        key = context.args[0]
        if redis1.exists(key):
            redis1.delete(key)
            update.message.reply_text(f'Successfully deleted {key}.')
        else:
            update.message.reply_text(f'{key} does not exist.')
    except Exception as e:
        update.message.reply_text(f'Error: {str(e)}')

if __name__ == '__main__':
    main()
