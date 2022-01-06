import logging

from telegram.ext import CommandHandler, MessageHandler, CallbackContext, Filters, Updater
from telegram import Update

from tabulate import tabulate

from pymongo import MongoClient

from googletrans import Translator

import requests

import json
import os
import random
import datetime
import pytz
import re

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TOKEN = os.environ['TOKEN']
DB = os.environ['DB']

mongo = MongoClient(DB)
db = mongo['CityU_Bot']
ranking = db['ranking']

translator = Translator()

updater = Updater(token=TOKEN, use_context=True)

logger = logging.getLogger()

dispatcher = updater.dispatcher

cooldown_gpa_god = {}

restaurant = ["AC1 Canteen", "AC1 Canteen", "AC1 Canteen",
              "AC2 Canteen", "AC2 Canteen", "AC2 Canteen",
              "AC3 Canteen", "AC3 Canteen",
              "Kebab 4/F AC1",
              "Subway 3/F AC3", "Subway 3/F AC3",
              "Yum Cha 8/F BOC", "Yum Cha 8/F BOC",
              "Lodge Bistro G/F Academic Exchange Building",
              "White Zone"]

capoos = [
    "BlueBearBrownBear",
    "Capoo_Dynamic3",
    "Capoo_Dynamic2",
    "Capoo_Dynamic1",
    "CapooEmojiAnimated1",
    "CrazyCapoo",
    "HappyCapoo",
    "HyperCapoo",
    "Animated_White_Rabbit",
    "YourCapoo",
    "AnimatedCapoo",
    "More_Capoo",
    "Capoo60FPS",
    "capoo_sp_animated",
    "AnimatedBlackCapoo",
    "Orange_Capoo",
    "Animated_Capoo",

    "line_11d10a_by_Sean_Bot",
    "catbugcapoo_kenny",
    "capoo_no_nichijou",
    "BugCat_Capoo",
    "capoo_5_1_by_StickersCloudBot",
    "line350755774_by_RekcitsEnilbot",
    "line339685862_by_RekcitsEnilbot",
    "CapooLoveRabbit",
    "line11894_by_Sean_Bot",
    "Capoo5447",
    "greencapoo",
    "BugCatCapoo2",
    "LINE9600",
    "line7007511_by_Sean_Bot",
    "line13545_by_Sean_Bot",
    "line293948094_by_RekcitsEnilbot",
    "BugCat_Capoo_The_Cutie_Pie",
    "Happyutu",
    "Capoo2978",
    "capoomixmixmixmix",
    "line24868_by_RekcitsEnilbot"
]

cityu_infos = {
    "助一城 Festival Jog - Schedule Planner": "https://festivaljog.com/",
    "CityU GE 指南": "http://cityuge.swiftzer.net/",
    "城大人資訊專頁": "https://www.instagram.com/hkcityu.info/",
    "學生會": "https://www.instagram.com/cityusu/",
    "學生會福利部": "https://www.instagram.com/cityusu_welfare/",
    "城市廣播": "https://www.instagram.com/cityusu.cbc/",
}


def delete_message(context: CallbackContext) -> None:
    context.bot.delete_message(context.job.context["chat"], context.job.context["message_id"])


def cron_delete_message(update: Update = None, context: CallbackContext = None, msg=None, second=3600):
    c = {
        "chat": update.message.chat.id,
        "message_id": update.message.message_id,
    }
    context.job_queue.run_once(delete_message, second, context=c)
    c = {
        "chat": update.message.chat.id,
        "message_id": msg.message_id,
    }
    context.job_queue.run_once(delete_message, second, context=c)


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

    ranking.update_one({"_id": {"type": "froze", "group": update.effective_chat.id}}, {"$inc": {f"{str(uid)}": 1}},
                       upsert=True)
    cron_delete_message(update=update, context=context, second=3600, msg=msg)


def what_to_eat(update: Update, context: CallbackContext):
    msg = context.bot.send_message(chat_id=update.effective_chat.id, text=random.choice(restaurant) + "!",
                                   reply_to_message_id=update.message.message_id)
    # cron_delete_message(update=update, context=context, second=3600, msg=msg)


def gpa_god(update: Update, context: CallbackContext):
    if update.message.chat.id not in cooldown_gpa_god:
        cooldown_gpa_god[update.message.chat.id] = []
    if update.effective_user.id not in cooldown_gpa_god[update.message.chat.id]:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"GPA God 保佑{update.effective_user.first_name}")
        cooldown_gpa_god[update.message.chat.id].append(update.effective_user.id)

        uid = update.effective_user.id
        ranking.update_one({"_id": {"type": "gpa_god", "group": update.effective_chat.id}},
                           {"$inc": {f"{str(uid)}": 1}}, upsert=True)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="你今日咪喺度求過囉，求得多GPA會0.00！")


def capoo(update: Update, context: CallbackContext):
    capoo_set = random.choice(capoos)
    sticker_set = context.bot.get_sticker_set(capoo_set).stickers
    msg = context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=random.choice(sticker_set),
                                   reply_to_message_id=update.message.message_id)
    cron_delete_message(update=update, context=context, second=1200, msg=msg)


def cityu_info(update: Update, context: CallbackContext):
    strs = ""
    for k, v in cityu_infos.items():
        strs += k + " " + v
        strs += "\n"
    msg = context.bot.send_message(chat_id=update.effective_chat.id, text=strs,
                                   reply_to_message_id=update.message.message_id)


def translate(update: Update, context: CallbackContext):
    if update.message.reply_to_message is not None:
        message = update.message.reply_to_message.text.replace('/t', '')
    else:
        message = update.message.text.replace('/t', '')
    if any(s in message for s in ['林鄭', '林鄭月娥']):
        message = message.replace('林鄭月娥', 'Mother Fucker')
        message = message.replace('林鄭', 'Mother Fucker')
    elif any(s in message.lower() for s in ['carrie lam', 'mother fucker']):
        message = message.lower().replace('carrie lam', '林鄭月娥')
        message = message.lower().replace('mother fucker', '林鄭月娥')
    if len(re.findall(r'[\u4e00-\u9fff]+', message)) > 0:
        result = translator.translate(message, dest='en').text
    else:
        result = translator.translate(message, dest='zh-TW').text
    msg = context.bot.send_message(chat_id=update.effective_chat.id, text=result,
                                   reply_to_message_id=update.message.message_id)


start_handler = CommandHandler('start', start)
froze_handler = CommandHandler('froze', froze)
gpa_god_handler = CommandHandler('gpagod', gpa_god)
what_to_eat_handler = CommandHandler('whattoeat', what_to_eat)
capoo_handler = CommandHandler('capoo', capoo)
cityu_info_handler = CommandHandler('cityuinfo', cityu_info)
translate_handler = CommandHandler('t', translate)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(froze_handler)
dispatcher.add_handler(gpa_god_handler)
dispatcher.add_handler(what_to_eat_handler)
dispatcher.add_handler(capoo_handler)
dispatcher.add_handler(cityu_info_handler)
dispatcher.add_handler(translate_handler)

updater.start_polling()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
