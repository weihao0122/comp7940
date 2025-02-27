## 此文件基于版本 13.7 的 Python Telegram 聊天机器人
## 和 urllib3 版本 1.26.18
## chatbot.py

import telegram
from telegram.ext import Updater, MessageHandler, Filters
# MessageHandler 用于所有消息更新
import configparser
import logging

def main():
    # 加载你的令牌并为你的机器人创建一个 Updater
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8-sig')
    print(repr(config['TELEGRAM']['ACCESS_TOKEN']))
    updater = Updater(token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    
    dispatcher = updater.dispatcher

    # 可以设置这个日志模块，
    # 这样你就会知道为什么和什么时候事情没有按预期工作
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    # 注册处理消息的调度器：
    # 这里我们注册一个回显调度器
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    # 启动机器人：
    updater.start_polling()
    updater.idle()

def echo(update, context):
    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("Context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)

if __name__ == '__main__':
    main()
