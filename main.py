import logging

from telegram.ext import CommandHandler, MessageHandler, CallbackContext, Filters, Updater
from telegram import Update

from tabulate import tabulate

from pymongo import MongoClient

import schedule

import time
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

mongo = MongoClient('mongodb+srv://eugene:9Q9dBqcyiKuQdvfe@monpodb.lqom3.mongodb.net')
db = mongo['CityU_Bot']
ranking = db['ranking']

updater = Updater(token='1973202635:AAGdKCr2ljX7sUnfo-dzvAiQUttL2qQ1GAM', use_context=True)

logger = logging.getLogger()

dispatcher = updater.dispatcher

cooldown_gpa_god = {}


def delete_message(context: CallbackContext) -> None:
    context.bot.delete_message(context.job.context["chat"], context.job.context["message_id"])


def reset_cooldown():
    global cooldown_gpa_god
    for x in [*cooldown_gpa_god]:
        cooldown_gpa_god[x] = []


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def froze(update: Update, context: CallbackContext):
    try:
        who = update.message.reply_to_message.from_user.first_name
        uid = update.message.reply_to_message.from_user.id
    except AttributeError:
        who = "他"
        uid = update.effective_user.id
    msg = context.bot.send_message(chat_id=update.effective_chat.id, text=f"{update.effective_user.first_name}愣了，這才想起來"
                                                                          f"，{who}是城市大學畢業的，"
                                                                          "所以才有這麼高的素質。城市大學是一所歷史悠久、"
                                                                          "學科齊全、學術實力雄厚、辦學特色鮮明，在國際上"
                                                                          "具有重要影響力與競爭力的綜合性大學，在多個學術領"
                                                                          "域具有非常前瞻的科技實力，擁有世界一流的實驗室與"
                                                                          "師資力量，各種排名均位於全球前列。歡迎大家報考城市大學。")

    ranking.update_one({"_id": "froze"}, {"$inc": {f"{str(uid)}": 1}}, upsert=True)
    c = {
        "chat": update.message.chat.id,
        "message_id": update.message.message_id,
    }
    context.job_queue.run_once(delete_message, 3600, context=c)
    c = {
        "chat": update.message.chat.id,
        "message_id": msg.message_id,
    }
    context.job_queue.run_once(delete_message, 3600, context=c)


def get_froze_rank(update: Update, context: CallbackContext):
    return


def gpa_god(update: Update, context: CallbackContext):
    if update.message.chat.id not in cooldown_gpa_god:
        cooldown_gpa_god[update.message.chat.id] = []
    if update.effective_user.id not in cooldown_gpa_god[update.message.chat.id]:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"GPA God 保佑{update.effective_user.first_name}")
        cooldown_gpa_god[update.message.chat.id].append(update.effective_user.id)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="你今日咪喺度求過囉，求得多GPA會0.00！")


start_handler = CommandHandler('start', start)
froze_handler = CommandHandler('froze', froze)
gpa_god_handler = CommandHandler('gpagod', gpa_god)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(froze_handler)
dispatcher.add_handler(gpa_god_handler)

schedule.every().day.at("00:00").do(reset_cooldown)

print(time.time())

updater.start_polling()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
