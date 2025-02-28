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

    # Initialize Redis connection with logging
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
    chatgpt_handler = MessageHandler(Filters.text & ~Filters.command, equiped_chatgpt)  # Exclude commands
    dispatcher.add_handler(chatgpt_handler)

    # Register other command handlers
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("set", set_key))       # /set <key> <value>
    dispatcher.add_handler(CommandHandler("get", get_key))       # /get <key>
    dispatcher.add_handler(CommandHandler("delete", delete_key)) # /delete <key>
    dispatcher.add_handler(CommandHandler("hello", hello))       # /hello <name> -> Greeting handler
    dispatcher.add_handler(CommandHandler("help", help_command))
    # Start the bot
    updater.start_polling()
    updater.idle()

# Handle the ChatGPT interaction
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

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Available commands:\n'
                              '/add <keyword> - Add a keyword\n'
                              '/set <key> <value> - Set a key-value pair\n'
                              '/get <key> - Get the value of a key\n'
                              '/delete <key> - Delete a key\n'
                              '/hello <name> - Send a greeting')

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
        if len(context.args) == 0:
            update.message.reply_text('Usage: /add <keyword>')
            return

        msg = context.args[0]  # /add keyword <-- this should store the keyword
        logging.info("Incrementing keyword '%s' in Redis", msg)  # Log the action

        # Increment the counter for the keyword in Redis
        redis1.incr(msg)
        
        # Log the current count
        count = redis1.get(msg)
        logging.info("Keyword '%s' count after increment: %s", msg, count)

        update.message.reply_text(f'You have said "{msg}" for {count} times.')
    except (IndexError, ValueError) as e:
        logging.error("Error in /add command: %s", str(e))
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
        logging.info("Setting Redis key '%s' to value '%s'", key, value)  # Log the action

        # Set the key-value pair in Redis
        redis1.set(key, value)

        # Log the set action
        logging.info("Successfully set key '%s' to value '%s'", key, value)

        update.message.reply_text(f'Successfully set {key} to {value}.')
    except Exception as e:
        logging.error("Error in /set command: %s", str(e))
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
        logging.info("Getting Redis key '%s'", key)  # Log the action

        # Retrieve the value from Redis
        value = redis1.get(key)
        
        # Log the retrieved value
        if value:
            logging.info("Found value for key '%s': %s", key, value)
            update.message.reply_text(f'The value of {key} is {value}.')
        else:
            logging.info("Key '%s' does not exist in Redis", key)
            update.message.reply_text(f'{key} does not exist.')
    except Exception as e:
        logging.error("Error in /get command: %s", str(e))
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
        logging.info("Deleting Redis key '%s'", key)  # Log the action

        # Check if the key exists in Redis
        if redis1.exists(key):
            # Delete the key from Redis
            redis1.delete(key)
            logging.info("Successfully deleted key '%s' from Redis", key)
            update.message.reply_text(f'Successfully deleted {key}.')
        else:
            logging.info("Key '%s' does not exist in Redis", key)
            update.message.reply_text(f'{key} does not exist.')
    except Exception as e:
        logging.error("Error in /delete command: %s", str(e))
        update.message.reply_text(f'Error: {str(e)}')

if __name__ == '__main__':
    main()
