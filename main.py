import io
import logging
import os
import pprint
import random
import re
import tempfile
import time
from typing import List, Any

import openai
import pandas as pd
import pickle5 as pickle
# from googletrans import Translator
from pandas import DataFrame
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Message, Sticker
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler
from telegram.ext import MessageHandler, CallbackContext, CallbackQueryHandler, filters

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
openai.api_key = str(os.environ['OPENAI'])

char_df: DataFrame = pd.read_csv("char.csv")
phrase_fragment_df: DataFrame = pd.read_csv("phrase_fragment.csv")
trending_df: DataFrame = pd.read_csv("trending.csv")
word_df: DataFrame = pd.read_csv("word.csv")

倉頡碼表 = {
    'q': '手',
    'w': '田',
    'e': '水',
    'r': '口',
    't': '廿',
    'y': '卜',
    'u': '山',
    'i': '戈',
    'o': '人',
    'p': '心',
    'a': '日',
    's': '尸',
    'd': '木',
    'f': '火',
    'g': '土',
    'h': '竹',
    'j': '十',
    'k': '大',
    'l': '中',
    'z': '重',
    'x': '難',
    'c': '金',
    'v': '女',
    'b': '月',
    'n': '弓',
    'm': '一',
}

with open('quick5.pickle', 'rb') as handle:
    quick5: Any = pickle.load(handle)

TOKEN: str = os.environ['TOKEN']
DB: str = os.environ['DB']

mongo: MongoClient = MongoClient(DB)
db: Database = mongo['CityU_Bot']
ranking: Collection = db['ranking']
gpt: Collection = db['chatgpt']
chat_ids: Collection = db['chat_id']

# translator: Translator = Translator()

# updater = Updater(token=TOKEN, use_context=True)
application = Application.builder().token(TOKEN).build()

logger: logging.Logger = logging.getLogger()

# dispatcher = updater.dispatcher

cooldown_gpa_god: dict = {}

cooldown_chat_gpt: dict = {}

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


async def delete_message(context: CallbackContext) -> None:
    await context.bot.delete_message(context.job.context["chat"], context.job.context["message_id"])
    logger.info(f"Message {context.job.context['message_id']} in {context.job.context['chat'],} deleted")


async def cron_delete_message(update: Update = None, context: CallbackContext = None, msg=None, second=3600) -> None:
    c: dict[str, int] = {
        "chat": update.message.chat.id,
        "message_id": update.message.message_id,
    }
    await context.job_queue.run_once(delete_message, second, context=c)
    c: dict[str, int] = {
        "chat": update.message.chat.id,
        "message_id": msg.message_id,
    }
    await context.job_queue.run_once(delete_message, second, context=c)


async def reset_cooldown() -> None:
    global cooldown_gpa_god
    for x in [*cooldown_gpa_god]:
        cooldown_gpa_god[x] = []


async def start(update: Update, context: CallbackContext) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a shitty bot, please talk to me!")


async def froze(update: Update, context: CallbackContext) -> None:
    try:
        who: str = update.message.reply_to_message.from_user.first_name
        uid: int = update.message.reply_to_message.from_user.id
        status: str = "畢業的"
    except AttributeError:
        who: str = "他"
        status: str = "的學生"
        uid: int = update.effective_user.id
    msg: Message = await context.bot.send_message(chat_id=update.effective_chat.id,
                                                  text=f"{update.effective_user.first_name}愣了，這才想起來"
                                                       f"，{who}是城市大學{status}，"
                                                       "所以才有這麼高的素質。城市大學是一所歷史悠久、"
                                                       "學科齊全、學術實力雄厚、辦學特色鮮明，在國際上"
                                                       "具有重要影響力與競爭力的綜合性大學，在多個學術領"
                                                       "域具有非常前瞻的科技實力，擁有世界一流的實驗室與"
                                                       "師資力量，各種排名均位於全球前列。歡迎大家報考城市大學。")

    ranking.update_one({"_id": {"type": "froze", "group": update.effective_chat.id}}, {"$inc": {f"{str(uid)}": 1}},
                       upsert=True)
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used froze")
    await cron_delete_message(update=update, context=context, second=300, msg=msg)


async def what_to_eat(update: Update, context: CallbackContext):
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=random.choice(restaurant) + "!",
                                         reply_to_message_id=update.message.message_id)
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used what to eat")
    cron_delete_message(update=update, context=context, second=300, msg=msg)


async def gpa_god(update: Update, context: CallbackContext) -> None:
    if update.message.chat.id not in cooldown_gpa_god:
        cooldown_gpa_god[update.message.chat.id] = []
    if update.effective_user.id not in cooldown_gpa_god[update.message.chat.id]:
        msg: Message = await context.bot.send_message(chat_id=update.effective_chat.id,
                                                      text=f"GPA God 保佑{update.effective_user.first_name}")
        cooldown_gpa_god[update.message.chat.id].append(update.effective_user.id)

        uid: int = update.effective_user.id
        ranking.update_one({"_id": {"type": "gpa_god", "group": update.effective_chat.id}},
                           {"$inc": {f"{str(uid)}": 1}}, upsert=True)
    else:
        msg: Message = await context.bot.send_message(chat_id=update.effective_chat.id,
                                                      text="你今日咪喺度求過囉，求得多GPA會0.00！")
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used gpa god")
    cron_delete_message(update=update, context=context, second=120, msg=msg)


async def capoo(update: Update, context: CallbackContext) -> None:
    capoo_set: str = random.choice(capoos)
    sticker_set: List[Sticker] = await context.bot.get_sticker_set(capoo_set).stickers
    msg: Message = await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=random.choice(sticker_set),
                                                  reply_to_message_id=update.message.message_id)
    logger.info(
        f"{update.effective_user.first_name}({update.effective_user.id}) 在 {update.effective_chat.title} 發送了一個 Capoo")
    cron_delete_message(update=update, context=context, second=120, msg=msg)


async def cityu_info(update: Update, context: CallbackContext) -> None:
    strs: str = ""
    for k, v in cityu_infos.items():
        strs += k + " " + v
        strs += "\n"
    msg: Message = await context.bot.send_message(chat_id=update.effective_chat.id, text=strs,
                                                  reply_to_message_id=update.message.message_id)
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) send cityu info")


async def translate(update: Update, context: CallbackContext) -> None:
    if update.message.reply_to_message is not None:
        prompt: str = update.message.reply_to_message.text.replace('/t', '')
    else:
        prompt: str = update.message.text.replace('/t', '')
    if len(re.findall(r'[\u4e00-\u9fff]+', prompt)) > 0:
        msg = [
            {"role": "system", "content": "You are a helpful assistant that translates any language to English."},
            {"role": "user", "content": f"Translate the following text to English: {prompt}"},

        ]
    else:
        msg = [
            {"role": "system", "content": "You are a helpful assistant that translates any language to "
                                          "Traditional Chinese."},
            {"role": "user", "content": f"Translate the following text to Traditional Chinese: {prompt}"},
        ]
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text="翻譯中...")
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=msg,
        user=str(update.effective_user.id),
    )
    content: str = result['choices'][0]['message']['content']
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=message.message_id, text=content)
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) translate {prompt} to {result}")


async def delete_gpa_bot(update: Update, context: CallbackContext) -> None:
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used get gpa bot")
    cron_delete_message(update=update, context=context, second=60)


async def rich(update: Update, context: CallbackContext) -> None:
    # if update.message.chat.id != -1001780288890: return
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used rich")
    sticker_set: List[Sticker] = await context.bot.get_sticker_set("line_276090076_by_moe_sticker_bot").stickers
    print(sticker_set)
    msg: Message = await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_set[14],
                                                  reply_to_message_id=update.message.message_id)


async def edit_university_msg(context: CallbackContext):
    await context.bot.edit_message_text(chat_id=context.job.context["chat"],
                                        message_id=context.job.context["message_id"],
                                        text=context.job.context["text"])


async def cron_edit_message(update: Update = None, context: CallbackContext = None, msg=None, second=3600,
                            text: str = None) -> None:
    c: dict[str, Any] = {
        "chat": update.effective_chat.id,
        "message_id": msg.message_id,
        "text": text,
    }
    await context.job_queue.run_once(edit_university_msg, second, context=c)


async def check_university(update: Update, context: CallbackContext):
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used check university")
    if update.message.reply_to_message is not None:
        message: Message = update.message.reply_to_message
        first_name: str = update.message.reply_to_message.from_user.first_name
    else:
        message: Message = update.message
        first_name: str = update.effective_user.first_name
    universities: List[str] = ["HKU", "CUHK", "CityU", "PolyU", "HKUST", "HKBU", "EDU", "Lingnan", "HKU SPACE", "HKCC",
                               "IVE",
                               "MIT", "Harvard", "Cambridge", "Imperial College", "Oxford", "University of Edinburgh",
                               "University of Bath"]
    random_university: str = random.choice(universities)
    second: int = random.randint(1, 5)
    msg: Message = await context.bot.send_message(chat_id=update.effective_chat.id, text="正在檢查.",
                                                  reply_to_message_id=message.message_id)
    await cron_edit_message(update=update, context=context, msg=msg, second=second, text="正在檢查...")
    await cron_edit_message(update=update, context=context, msg=msg, second=second * 2,
                            text=f"正在檢查 {first_name} 的Instagram")
    await cron_edit_message(update=update, context=context, msg=msg, second=second * 4,
                            text=f"正在檢查 {first_name} 的Twitter")
    await cron_edit_message(update=update, context=context, msg=msg, second=second * 5,
                            text=f"正在檢查 {first_name} 的Linkedin")
    await cron_edit_message(update=update, context=context, msg=msg, second=second * 6,
                            text=f"正在向 {random_university} 確認 {first_name} 的學歷")
    await cron_edit_message(update=update, context=context, msg=msg, second=second * 7,
                            text=f"正在向 {random_university} 確認 {first_name} 的學歷...")
    await cron_edit_message(update=update, context=context, msg=msg, second=second * 8,
                            text=f"確認 {first_name} 就讀於 {random_university}")


async def check_quick5(update: Update, context: CallbackContext) -> None:
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used check quick5")
    msg: str = update.message.text.split(" ")[-1]
    if len(msg) == 1:
        try:
            quick5_code: str = quick5[str(msg[-1])]
            倉頡碼: str = ''.join([倉頡碼表[x] for x in quick5_code])
            quick5_msg: str = f"{msg[-1]} 的倉頡碼為 {quick5_code} 「{倉頡碼}」"
        except KeyError:
            quick5_msg: str = f"找不到 {msg[-1]} 的倉頡碼"
        try:
            jyutping: str = char_df.loc[char_df['char'] == msg[-1]]['jyutping'].values[0]
            if len(jyutping) == 0:
                raise KeyError
            jyutping_msg: str = f"{msg[-1]} 的粵拼為 {jyutping}"
        except Exception:
            jyutping_msg: str = f"找不到 {msg[-1]} 的粵拼"
        try:
            sample_list: List[str] = word_df.loc[word_df['char'].str.contains(msg[-1])]['char'].values.tolist()
            if len(sample_list) == 0:
                raise KeyError
            sample_words: List[str] = random.sample(sample_list, len(sample_list) if len(sample_list) < 5 else 5)
            sample_5words: str = ', '.join(sample_words)
            sample_words_msg: str = f"{msg[-1]} 的例詞為 {sample_5words}"
        except KeyError:
            sample_words_msg: str = f"找不到 {msg[-1]} 的例詞"
        try:
            phrases: List[str] = phrase_fragment_df.loc[phrase_fragment_df['char'].str.contains(msg[-1])][
                'char'].values.tolist()
            if len(phrases) == 0:
                raise KeyError
            phrases_list: List[str] = random.sample(phrases, len(phrases) if len(phrases) < 3 else 3)
            phrases_5fragment: str = '\n - '.join(phrases_list)
            phrases_msg: str = f"{msg[-1]} 的片語為\n - {phrases_5fragment}"
        except KeyError:
            phrases_msg: str = f"找不到 {msg[-1]} 的片語"
        msg_to_send: str = f"{quick5_msg}\n\n{jyutping_msg}\n\n{sample_words_msg}\n\n{phrases_msg}"
    else:
        msg_to_send: str = "請輸入 /char [字(冇s)]"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg_to_send,
                                   reply_to_message_id=update.message.message_id)


async def chatgpt(update: Update, context: CallbackContext) -> None:
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used chatgpt")
    message: str = update.message.text.replace('/ask', '')
    if message == '':
        await context.bot.send_message(chat_id=update.effective_chat.id, text="請輸入 /ask [訊息]",
                                       reply_to_message_id=update.message.message_id)
        return
    else:
        try:
            try:
                reply_id = update.message.reply_to_message.message_id
            except:
                reply_id = -1
            gpt.insert_one({'chat_id': update.effective_chat.id, 'message_id': update.message.message_id,
                            'user_id': update.effective_user.id,
                            'message': message,
                            'reply_id': reply_id})
        except Exception as e:
            logger.error(e)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="發生錯誤，請稍後再試",
                                           reply_to_message_id=update.message.message_id)
            return

    if len(''.join(re.findall(r'[\u4e00-\u9fff]+', message))) > 2:
        prompt: str = '你是一個專為回答問題而設計的AI，請用繁體中文回答以下問題。'
    else:
        prompt = 'You are an AI designed to answer any questions, please answer the following questions in the ' \
                 'corresponding language'
    msg: list = [{"role": "system", "content": f"{prompt}"}]
    msg_stack: list = []
    if update.message.reply_to_message is not None:
        if update.message.reply_to_message.from_user.id != 1973202635:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You must reply to my message")
            return
        conversation: Any = gpt.find_one(
            {'chat_id': update.effective_chat.id, 'message_id': update.message.reply_to_message.message_id})
        while conversation is not None:
            msg_stack.append(conversation)
            if conversation['reply_id'] == -1:
                break
            conversation = gpt.find_one({'chat_id': update.effective_chat.id, 'message_id': conversation['reply_id']})
        m: Any = msg_stack.pop()
        while m is not None:
            if m['user_id'] == 1973202635:
                msg.append({"role": "system", "content": f"{m['message']}"})
            else:
                msg.append({"role": "user", "content": f"{m['message']}"})
            m = msg_stack.pop() if len(msg_stack) > 0 else None
    message = update.message.text.replace('/ask', '').replace('--debug', '')
    msg.append({"role": "user", "content": f"{message}"})

    try:
        if abs(cooldown_chat_gpt[str(update.effective_chat.id)] - int(time.time())) < 10:
            diff: int = abs(cooldown_chat_gpt[str(update.effective_chat.id)] - int(time.time()))
            te: str = f"請等待10秒 ({diff}秒 remaining)"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=te,
                                           reply_to_message_id=update.message.message_id)
            return
        else:
            cooldown_chat_gpt[str(update.effective_chat.id)] = int(time.time())
    except:
        cooldown_chat_gpt[str(update.effective_chat.id)] = int(time.time())

    res = await context.bot.send_message(chat_id=update.effective_chat.id, text="Generating...",
                                         reply_to_message_id=update.message.message_id,
                                         parse_mode='HTML', disable_web_page_preview=True)
    try:
        result = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=msg,
            user=str(update.effective_user.id),
            timeout=30,

        )
    except Exception as e:
        logger.error(e)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Error, it might be caused by exceeding the tokens limit",
                                       reply_to_message_id=update.message.message_id)
        return
    content: str = result['choices'][0]['message']['content']
    if '--debug' in update.message.text:
        content: str = content + '\n\n\n```' + pprint.pformat(msg,
                                                              indent=4) + '```'

    gpt.insert_one(
        {'chat_id': update.effective_chat.id, 'message_id': res.message_id, 'message': content,
         'user_id': 1973202635, 'reply_id': update.message.message_id})
    content += "\n\n<a href='https://carousell.app.link/EtxvM2gpgyb'>代購ChatGPT Plus</a>"
    try:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=res.message_id, text=content,
                                            parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        # wontfix
        logger.error(e)
        try:
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=res.message_id,
                                                text=content,
                                                parse_mode=ParseMode.MARKDOWN_V2,
                                                disable_web_page_preview=True)
        except Exception as e:
            logger.error(e)
            try:
                await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=res.message_id,
                                                    text=content,
                                                    disable_web_page_preview=True)
            except Exception as e:
                logger.error(e)
                tmp = tempfile.NamedTemporaryFile()

                # Open the file for writing.
                with open(tmp.name, 'w') as f:
                    f.write(content)  # where `stuff` is, y'know... stuff to write (a string)
                # Open the file for reading.
                with open(tmp.name, 'r') as f:
                    file = f.read()
                await context.bot.send_document(chat_id=update.effective_chat.id,
                                                document=io.BytesIO(file.encode('utf-8')),
                                                filename='output.txt',
                                                reply_to_message_id=update.message.message_id)


async def purge_data(update: Update, context: CallbackContext):
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used purge_data")
    message: str = "Warning: This will delete all chat record related to the message in the database, " \
                   "are you sure you want to continue?" \
                   "\n\n" \
                   "警告: 這會刪除所有與該訊息有關的聊天記錄，你確定要繼續嗎？"
    markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Yes", callback_data='yes'), InlineKeyboardButton("No", callback_data='no')]])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, reply_markup=markup)


async def callback_purge_data_handler(update: Update, context: CallbackContext) -> None:
    callback_data: str = update.callback_query.data
    if callback_data == 'yes':
        reply_id: int = update.callback_query.message.reply_to_message.message_id
        while reply_id != -1:
            reply_id: int = update.callback_query.message.reply_to_message.message_id
            db_reply_id: Any = gpt.find_one({'chat_id': update.effective_chat.id, 'message_id': reply_id})['reply_id']
            gpt.delete_one({'chat_id': update.effective_chat.id, 'message_id': reply_id})
            reply_id = db_reply_id
    elif callback_data == 'no':
        pass


async def log_chat_id(update: Update, context: CallbackContext) -> None:
    chat_ids.update_one({'chat_id': update.effective_chat.id}, {'$set': {'chat_id': update.effective_chat.id}},
                        upsert=True)


async def broadcast(update: Update, context: CallbackContext) -> None:
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used broadcast")
    if update.effective_user.id != 110054652:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="你唔係主人，唔可以用呢個指令")
        return
    message: str = update.message.text.replace('/broadcast ', '')
    if message == '':
        await context.bot.send_message(chat_id=update.effective_chat.id, text="請輸入 /broadcast [訊息]")
        return
    else:
        for chat_id in chat_ids.find({}):
            try:
                await context.bot.send_message(chat_id=chat_id['chat_id'], text=message)
            except Exception as e:
                logger.error(e)
                pass


async def toggle_chat_command(update: Update, context: CallbackContext):
    logger.info(f"{update.effective_user.first_name}({update.effective_user.id}) used toggle_chat_command")

    if update.effective_user.id != 110054652:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="你唔係主人，唔可以用呢個指令")
        return


start_handler: CommandHandler = CommandHandler('start', start)
froze_handler: CommandHandler = CommandHandler('froze', froze)
gpa_god_handler: CommandHandler = CommandHandler('gpagod', gpa_god)
what_to_eat_handler: CommandHandler = CommandHandler('whattoeat', what_to_eat)
capoo_handler: CommandHandler = CommandHandler('capoo', capoo)
cityu_info_handler: CommandHandler = CommandHandler('cityuinfo', cityu_info)
translate_handler: CommandHandler = CommandHandler('t', translate)
check_university_handler: CommandHandler = CommandHandler('checkuniversity', check_university)
check_quick5_handler: CommandHandler = CommandHandler('ch', check_quick5)
check_quick5_handler_char: CommandHandler = CommandHandler('char', check_quick5)
chatgpt_handler: CommandHandler = CommandHandler('ask', chatgpt)
broadcast_handler: CommandHandler = CommandHandler('broadcast', broadcast)
purge_data_handler: CommandHandler = CommandHandler('purgedata', purge_data)

rich_handler: MessageHandler = MessageHandler(filters.Regex(r'rich'), rich)
rich_handler2: MessageHandler = MessageHandler(filters.Regex(r'Rich'), rich)
delete_gpa_bot_handler: MessageHandler = MessageHandler(filters.Regex(r'你GPA係: \d.\d\d'), delete_gpa_bot)
log_chat_id_handler: MessageHandler = MessageHandler(filters.ALL, log_chat_id)

application.add_handler(start_handler)
application.add_handler(froze_handler)
application.add_handler(gpa_god_handler)
application.add_handler(what_to_eat_handler)
application.add_handler(capoo_handler)
application.add_handler(cityu_info_handler)
application.add_handler(translate_handler)
application.add_handler(delete_gpa_bot_handler)
application.add_handler(rich_handler)
application.add_handler(rich_handler2)
application.add_handler(check_university_handler)
application.add_handler(check_quick5_handler)
application.add_handler(check_quick5_handler_char)
application.add_handler(chatgpt_handler)
application.add_handler(broadcast_handler)
application.add_handler(purge_data_handler)
application.add_handler(CallbackQueryHandler(callback_purge_data_handler))

application.add_handler(log_chat_id_handler)

try:
    application.run_polling()
except KeyboardInterrupt:
    # updater.stop()
    logger.info("Bot stopped")
    # not actually stop lol
except Exception as e:
    logger.error(e)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
