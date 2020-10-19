# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 13:10:53 2020

TODO: argparse input stuff

@author: skjerns
"""
import os
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import KeyboardButton, ReplyKeyboardMarkup, ForceReply
import time
from pprint import pprint as pprint, pformat
import json
import urllib
import datetime
import traceback

try:
    print('Testing connection')
    urllib.request.urlopen('http://api.telegram.org/')
    print('Success.')
except:
    try:
        print('Trying again with proxy')
        telepot.api.set_proxy('http://proxy.server:3128')
        print('Success with proxy.')
    except:
        raise


settings_file = os.path.expanduser('~/.sharingiskaringbot')

with open(settings_file) as f:
    settings = json.load(f)
    token = settings['token']
    group_chat_id = settings['group_chat_id']
    admin_chat_id = settings['admin_chat_id']
    debug_chat_id = settings.get('debug_chat_id', admin_chat_id)


class Member():
    def __init__(self, member):
        self.id = member.get('id')
        self.first = member.get('first_name', '')
        self.last = member.get('last_name', '')
        self.is_bot = member.get('is_bot', False)
        self.username = member.get('username', '')

    def send_message(self, msg, bot):
        pass

    def __eq__(self, other):
        return self.id==other.id


class Bot(telepot.Bot):

    def __init__(self, token):
        super(Bot, self).__init__(token)
        self.offset = None

    def run(self):
        print('Bot running.')
        while True:
            try:

                updates = self.getUpdates(self.offset)
                for update in updates:
                    self.offset = update['update_id'] + 1
                    message = update['message']
                    self.process(message)
                print('.' if len(updates)==0 else '!'*len(updates), end='')

            except KeyboardInterrupt:
                raise

            except telepot.exception.BadHTTPResponse as e:
                traceback.print_exc()

                # Servers probably down. Wait longer.
                if e.status == 502:
                    print('Server down? wait 30 seconds')
                    time.sleep(30)

            except:
                traceback.print_exc()

            finally:
                time.sleep(0.3)

    def forward_new_user_messages(self, msg):
        from_member = Member(msg['from'])
        chat_name = msg['chat'].get('username')
        for new_member in map(Member, msg['new_chat_members']):
            if from_member==new_member:
                message = f'<a href="tg://user?id={new_member.id}">{new_member.first} {new_member.last} ({new_member.username})</a> joined {chat_name}'
            else:
                message = f'<a href="tg://user?id={from_member.id}">{from_member.first} {from_member.last} ({new_member.username})</a> added '\
                          f'<a href="tg://user?id={new_member.id}">{new_member.first} {new_member.last}</a> to {chat_name}'
            bot.send_message(admin_chat_id, message, disable_notification=True,
                            parse_mode = 'html')

    def forward_user_left_messages(self, msg):
        from_member = Member(msg['from'])
        old_member = Member(msg['left_chat_member'])
        chat_name = msg['chat'].get('username')
        if from_member==old_member:
            message = f'<a href="tg://user?id={old_member.id}">{old_member.first} {old_member.last}</a> left {chat_name}'
        else:
            message = f'<a href="tg://user?id={from_member.id}">{from_member.first} {from_member.last}</a> removed '\
                      f'<a href="tg://user?id={old_member.id}">{old_member.first} {old_member.last}</a> to {chat_name}'
        bot.send_message(admin_chat_id, message, disable_notification=True,
                        parse_mode = 'html')

    def send_not_answer_reminder(self, msg):
        from_member = Member(msg['from'])
        message_id = msg['message_id']
        chat_id = msg['chat']['id']
        text = 'Du hast gerade in der SharingIsKAring-Gruppe auf eine Nachricht geantwortet. ' \
               'Bitte benutze die Antworten-Funktion nur in Ausnahmefällen und schreibe sonst alles mit der Person in einem <b>privaten Chat</b>\n' \
               'Dies gilt insbesondere für <i>"Ich habe Interesse", "Danke"</i>, etc.\n\n' \
               'Bitte lösche deine Nachricht wieder und sende sie als <b>private Nachricht</b> (außer du denkst, sie ist wirklich für alle 500+ Leute relevant.). Beep-boop, ich bin ein Bot🤖.'

        keyboard = ReplyKeyboardMarkup(keyboard=[
                   [InlineKeyboardButton(text='Ja', switch_inline_query=''),
                    InlineKeyboardButton(text='Nein', switch_inline_query_current_chat='@SharingIsKAringBot no-inline')],
                   ], selective=True, one_time_keyboard=True, resize_keyboard=False)

        self.send_message(chat_id, '/deleteme', parse_mode='html', reply_markup=ForceReply(),
                          reply_to_message_id=message_id, disable_notification=True)


    def log(self, msg):
        now = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
        with open('./bot.log', 'w') as f:
            f.write(f'{now} {msg}\n')

    def send_message(self, chat_id,  message, disable_notification=False,
                        parse_mode='html', **kwargs):
        if parse_mode.lower()=='markdownv2':
            reserved = "#'_*[]()~`#+-|{}.!>"
        else:
            reserved = ''
        for char in reserved:
            message = message.replace(char, f'\\{char}')
        self.sendMessage(chat_id, message, disable_notification=disable_notification,
                         parse_mode=parse_mode, **kwargs)

    def process(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        msg_id = telepot.message_identifier(msg)

        try:
            if chat_type=='private' and ('text' in msg):
                self.send_message(debug_chat_id, f'type: {content_type}\nchat: {chat_type}\n```\n{pformat(msg)}\n```',
                            parse_mode='MarkdownV2', disable_notification=True)
                self.send_message(chat_id, f'Hi, I\'m a bot. Please see my source code at https://github.com/skjerns/SharingIsKAringBot.\n'\
                                           f'You sent me "{msg["text"]}", but I have no idea what that means.', parse_mode='MarkdownV2')
            elif chat_type=='supergroup' and  str(chat_id)==str(group_chat_id):
                print(f'its a group message: {content_type}')

                if content_type=='new_chat_member':
                    # remove new chat member message and forward to admin chat
                    self.deleteMessage(msg_id)
                    self.forward_new_user_messages(msg)

                elif content_type=='left_chat_member':
                    # remove chat member deleted message and forward to admin chat
                    self.deleteMessage(msg_id)
                    self.forward_user_left_messages(msg)

                elif content_type=='text' and ('reply_to_message' in msg) and \
                     not msg['reply_to_message']['from']['is_bot']:
                    # remind users not to answer in group
                    print('reminding')
                    self.send_not_answer_reminder(msg)

            else:
                # if none of the above: send debug message.
                self.send_message(debug_chat_id,
                            f'No action taken.\ntype: {content_type}\nchat: {chat_type}\n```\n{pformat(msg)}\n```',
                            parse_mode='html', disable_notification=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_message(debug_chat_id, f"ERROR: {e} {repr(e)}", disable_notification=True)
            pprint(f'ERROR, wait 2 sec :{pformat(str(e)), pformat(repr(e))}')
            time.sleep(2)
        print('-'*10)
        pprint(msg)

bot = Bot(token)
bot.run()


