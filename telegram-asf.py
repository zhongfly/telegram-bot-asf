# encoding:UTF-8
# python3.6
from telegram.utils.helpers import escape_markdown
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from functools import wraps
import logging
import re
import requests
from urllib.parse import urljoin
import toml
import sys
import os
from json import dumps

if len(sys.argv) < 2:
    print('使用默认路径载入配置文件')
    conf = 'tgbot.toml'
    if not os.path.exists(conf):
        print('未找到配置文件')
        sys.exit(1)
else:
    conf = sys.argv[1]
    print('使用指定路径{}载入配置文件'.format(conf))

with open(conf, encoding="utf-8") as f:
    dict_conf = toml.load(f)
token = dict_conf['telegram']['token']
admin = dict_conf['telegram']['admin']
proxy = dict_conf['telegram']['proxy']
ipc_address = dict_conf['ipc']['address']
ipc_password = dict_conf['ipc']['password']

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
pattern_2fa_command = re.compile(r'.?2fa( |$)',re.I)
pattern_key = re.compile(r'([0-9,A-Z]{5}-){2,4}[0-9,A-Z]{5}')
pattern_id = re.compile(r'([0-9]{3,10})')
if proxy != '':
    updater = Updater(token, request_kwargs={'proxy_url': proxy}, use_context=True)
else:
    updater = Updater(token, use_context=True)

cmd_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='redeem', callback_data='redeem'),
     InlineKeyboardButton(text='addlicense sub',
                          callback_data='addlicense sub'),
     InlineKeyboardButton(text='addlicense app', callback_data='addlicense app')],
    [InlineKeyboardButton(text='start', callback_data='start'),
     InlineKeyboardButton(text='stop', callback_data='stop'),
     InlineKeyboardButton(text='pause', callback_data='pause'),
     InlineKeyboardButton(text='resume', callback_data='resume')],
    [InlineKeyboardButton(text='2fa', callback_data='2fa'),
     InlineKeyboardButton(text='2faok', callback_data='2faok'),
     InlineKeyboardButton(text='version', callback_data='version'),
     InlineKeyboardButton(text='status', callback_data='status ASF')],
    [InlineKeyboardButton(text='取消', callback_data='cancel')]
])

type1 = ['addlicense sub', 'addlicense app', 'redeem']
type2 = ['start', 'stop', 'pause', 'resume', '2fa', '2faok']


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in admin:
            update.message.reply_text('你没有操作BOT的权限', quote=True)
            return -1
        return func(update, context, *args, **kwargs)

    return wrapped


class IPC(object):
    def __init__(self, ipc='http://127.0.0.1:1242/', password='', timeout=20):
        self.ipc = ipc
        self.password = password
        self.timeout = timeout
        self.headers = dict()
        if password:
            self.headers['Authentication'] = password

    def get_bot(self):
        url = urljoin(ipc_address, 'Api/Bot/ASF')
        try:
            resp = requests.get(url, headers=self.headers,
                                timeout=self.timeout)
        except requests.exceptions.ConnectionError as e:
            raise e
        return self.asf_response(resp)

    def command(self, cmd):
        url = urljoin(ipc_address, 'Api/Command')
        try:
            body = dumps({"Command": cmd})
            headers = self.headers
            headers['Content-Type'] = 'application/json'
            resp = requests.post(url, headers=headers,
                                 timeout=self.timeout, data=body)
        except requests.exceptions.ConnectionError as e:
            raise e
        return self.asf_response(resp)

    def asf_response(self, resp):
        code = resp.status_code
        if code == 200:
            return resp.json()['Result']
        elif code == 400:
            return resp.json()['Message']
        elif code == 401:
            return 'IPC密码错误'
        elif code == 403:
            return 'IPC密码错误,由于错误次数过多，请1小时后重试'


asf = IPC(ipc=ipc_address, password=ipc_password)


def send(cmd):
    try:
        res = asf.command(cmd)
    except Exception as e:
        if hasattr(e, 'message'):
            res = e.message
        else:
            res = e.__class__.__name__
    if not isinstance(res, str):
        res = str(res)
    logger.info("执行命令：{}\n结果为：{}".format(cmd, res))
    return res


def bots_menu(header=True, n_cols=4):
    bots = asf.get_bot()
    if len(bots) == 1:
        key = list(bots.keys())[0]
        return bots[key]['BotName']
    else:
        buttons = []
        for i in bots.values():
            buttons.append(InlineKeyboardButton(
                text=i['BotName'], callback_data=i['BotName']))
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        header_button = [InlineKeyboardButton(
            text='ASF（即所有bot）', callback_data='asf'), ]
        if header:
            menu.insert(0, header_button)
        footer_button = [InlineKeyboardButton(
            text='返回', callback_data='back'), ]
        menu.append(footer_button)
        reply_markup = InlineKeyboardMarkup(menu)
        return reply_markup


TYPE, BOTNAME, OTHERS = range(3)


def deljob(context):
    if 'job' in context.chat_data:
        job = context.chat_data['job']
        job.schedule_removal()
        del context.chat_data['job']


def timeout(context):
    job = context.job
    context.bot.editMessageText(
        chat_id=job.context[0], message_id=job.context[1], text='2min无回应\n已结束等待')
    return -1


@restricted
def start(update, context):
    logger.info("%s 开始会话。", update.message.from_user.first_name)
    chat_id = update.message.chat_id
    msg = context.bot.sendMessage(text='请选择命令\n发送 /cancel 退出',
                                  chat_id=chat_id, reply_markup=cmd_menu)
    job = context.job_queue.run_once(timeout, 120, context=(chat_id, msg.message_id))
    context.chat_data['msg'] = msg.message_id
    context.chat_data['job'] = job
    return TYPE


def mfa_timeout(context):
    job = context.job
    context.bot.editMessageText(
        chat_id=job.context[0], message_id=job.context[1], text='[2FA Deleted]')


def cmdtype(update, context):
    bot = context.bot
    chat_data = context.chat_data
    query = update.callback_query
    chat_id = query.message.chat_id
    deljob(context)
    cmd_type = query.data
    if query.data == 'cancel':
        bot.editMessageText(
            chat_id=chat_id, message_id=chat_data['msg'], text='已取消')
        logger.info("取消操作，结束会话。")
        return ConversationHandler.END
    context.chat_data['type'] = query.data
    if cmd_type in type1 or cmd_type in type2:
        if cmd_type == 'redeem':
            reply_markup = bots_menu(header=False)
        else:
            reply_markup = bots_menu()
        chat_data['botname_markup'] = reply_markup
        if isinstance(reply_markup, str):
            chat_data['bot'] = reply_markup
            return deal_command(context, chat_id)
        else:
            bot.editMessageText(
                chat_id=chat_id, message_id=chat_data['msg'], text='请选择BOT\n发送 /cancel 退出', reply_markup=reply_markup)
            #        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=chat_data['msg'],reply_markup=reply_markup)
            job = context.job_queue.run_once(
                timeout, 120, context=(chat_id, chat_data['msg']))
            chat_data['job'] = job
            return BOTNAME
    else:
        res = send(cmd_type)
        bot.editMessageText(
            chat_id=chat_id, message_id=chat_data['msg'], text=res)
        return ConversationHandler.END


def botname(update, context):
    bot = context.bot
    chat_data = context.chat_data
    query = update.callback_query
    chat_id = query.message.chat_id
    deljob(context)
    if query.data == 'back':
        bot.editMessageText(
            chat_id=chat_id, message_id=chat_data['msg'], text='请选择命令\n发送 /cancel 退出', reply_markup=cmd_menu)
        job = context.job_queue.run_once(
            timeout, 120, context=(chat_id, chat_data['msg']))
        chat_data['job'] = job
        return TYPE
    chat_data['bot'] = query.data
    return deal_command(context, chat_id)


def deal_command(context, chat_id):
    bot = context.bot
    chat_data = context.chat_data
    if chat_data['type'] in type1:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text='返回', callback_data='back'), ], ])
        if chat_data['type'] == 'redeem':
            text = '当前操作的BOT为: ' + chat_data['bot'] + \
                   ',\n请输入KEY!\n发送 /cancel 退出'
        elif chat_data['type'] == 'addlicense sub':
            text = '请输入subID !\n发送 /cancel 退出'
        elif chat_data['type'] == 'addlicense app':
            text = '请输入appID !\n发送 /cancel 退出'
        bot.editMessageText(
            chat_id=chat_id, message_id=chat_data['msg'], text=text, reply_markup=reply_markup)
        job = context.job_queue.run_once(
            timeout, 120, context=(chat_id, chat_data['msg']))
        chat_data['job'] = job
        return OTHERS
    else:
        command = chat_data['type'] + ' ' + chat_data['bot']
        res = send(command)
        if pattern_2fa_command.match(command):
            res = re.sub(r'([A-Z0-9]{5}$)',r'`\1`', escape_markdown(res, version=2))
            bot.editMessageText(
                chat_id=chat_id, message_id=chat_data['msg'], text=res, parse_mode='MarkdownV2')     
            context.job_queue.run_once(mfa_timeout, 30, context=(
                chat_id, chat_data['msg']))
        else:
            bot.editMessageText(
                chat_id=chat_id, message_id=chat_data['msg'], text=res)            
        return ConversationHandler.END


def back2botname(update, context):
    bot = context.bot
    chat_data = context.chat_data
    deljob(context)
    query = update.callback_query
    chat_id = query.message.chat_id
    reply_markup = chat_data['botname_markup']
    if isinstance(reply_markup, str):
        bot.editMessageText(text='请选择命令\n发送 /cancel 退出',
                            chat_id=chat_id, message_id=chat_data['msg'], reply_markup=cmd_menu)
        job = context.job_queue.run_once(
            timeout, 120, context=(chat_id, chat_data['msg']))
        chat_data['job'] = job
        return TYPE
    else:
        bot.editMessageText(
            chat_id=chat_id, message_id=chat_data['msg'], text='请选择BOT\n发送 /cancel 退出', reply_markup=reply_markup)
        #    bot.editMessageReplyMarkup(chat_id=chat_id, message_id=chat_data['msg'], reply_markup=reply_markup)
        job = context.job_queue.run_once(
            timeout, 120, context=(chat_id, chat_data['msg']))
        chat_data['job'] = job
        return BOTNAME


def others(update, context):
    bot = context.bot
    chat_data = context.chat_data
    deljob(context)
    chat_id = update.message.chat_id
    args = update.message.text
    if 'msg' in chat_data:
        msg = chat_data['msg']
        bot.editMessageText(chat_id=chat_id, message_id=msg,
                            text='已输入\n发送 /cancel 退出')
        del chat_data['msg']

    if chat_data['type'] == 'redeem':
        if pattern_key.match(args) is None:
            update.message.reply_text(text='KEY输入错误，请重新输入', quote=True)
            return OTHERS
    elif chat_data['type'] == 'addlicense sub' or chat_data['type'] == 'addlicense app':
        if pattern_id.match(args) is None:
            update.message.reply_text(
                text='appID 或者 subID输入错误，请重新输入', quote=True)
            return OTHERS
        if chat_data['type'] == 'addlicense app':
            args = "app/" + args
        else:
            args = "sub/" + args
        chat_data['type'] = "addlicense"
    command = chat_data['type'] + ' ' + chat_data['bot'] + ' ' + args
    res = send(command)
    update.message.reply_text(text=res, quote=True)
    return ConversationHandler.END


def cancel(update, context):
    deljob(context.chat_data)
    logger.info("%s 取消操作，结束会话。", update.message.from_user.first_name)
    update.message.reply_text('已取消', quote=True)
    return ConversationHandler.END


start_handler = ConversationHandler(
    entry_points=[CommandHandler(
        'start', start)],

    states={
        TYPE: [CallbackQueryHandler(cmdtype)],

        BOTNAME: [CallbackQueryHandler(botname)],

        OTHERS: [MessageHandler(Filters.text, others),
                 CallbackQueryHandler(back2botname)],
    },

    fallbacks=[CommandHandler('cancel', cancel)],

    allow_reentry=True,

    conversation_timeout=120,
)


@restricted
def reply(update, context):
    chat_id = update.message.chat_id
    command = update.message.text
    res = send(command)
    if pattern_2fa_command.match(command):
        res = re.sub(r'([A-Z0-9]{5}$)',r'`\1`', escape_markdown(res, version=2))
        msg = update.message.reply_text(text=res, quote=True, parse_mode='MarkdownV2')
        context.job_queue.run_once(mfa_timeout, 30, context=(chat_id, msg.message_id))
    else:
        msg = update.message.reply_text(text=res, quote=True)


def error(update, context):
    logger.warning('Update "%s" caused error "%s"' % (update, context.error))


updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(MessageHandler(
    Filters.text, reply))
updater.dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()
