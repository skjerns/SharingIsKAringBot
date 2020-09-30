# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 13:10:53 2020

TODO: argparse input stuff

@author: skjerns
"""
import os
from telepot.loop import MessageLoop
import telepot
import time
from pprint import pprint as pprint, pformat
import json
import urllib

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

token = ''

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

    def send_message(self, msg, bot):
        pass

    def __eq__(self, other):
        return self.id==other.id


class Bot(telepot.Bot):
    def forward_new_user_messages(self, msg):
        from_member = Member(msg['from'])
        chat_name = msg['chat'].get('username')
        for new_member in map(Member, msg['new_chat_members']):
            if from_member==new_member:
                message = f'<a href="tg://user?id={new_member.id}">{new_member.first} {new_member.last}</a> joined {chat_name}'
            else:
                message = f'<a href="tg://user?id={from_member.id}">{from_member.first} {from_member.last}</a> added '\
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


    def log(self):
        pass

    def send_message(self, chat_id,  message, disable_notification=False,
                        parse_mode='MarkdownV2'):
        if parse_mode.lower()=='markdownv2':
            reserved = "#'_*[]()~`#+-|{}.!>"
        else:
            reserved = ''
        for char in reserved:
            message = message.replace(char, f'\\{char}')
        self.sendMessage(chat_id, message, disable_notification=disable_notification,
                         parse_mode=parse_mode)

    def hdl(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        msg_id = telepot.message_identifier(msg)

        try:
            if chat_type=='private' and ('text' in msg):
                self.send_message(debug_chat_id, f'type: {content_type}\nchat: {chat_type}\n```\n{pformat(msg)}\n```',
                            parse_mode='MarkdownV2', disable_notification=True)
                self.send_message(chat_id, f'Hi, I\'m a bot. Please see my source code at https://github.com/skjerns/SharingIsKAringBot.\n'\
                                           f'You sent me "{msg["text"]}", but I have no idea what that means.', parse_mode='MarkdownV2')
            elif chat_type=='supergroup' and (('text' in msg) or ('photo' in msg)):
                pass
            elif content_type=='new_chat_member':
                self.deleteMessage(msg_id)
                self.forward_new_user_messages(msg)
            elif content_type=='left_chat_member':
                self.deleteMessage(msg_id)
                self.forward_user_left_messages(msg)
            else:
                self.send_message(debug_chat_id, f'type: {content_type}\nchat: {chat_type}\n```\n{pformat(msg)}\n```',
                            parse_mode='MarkdownV2', disable_notification=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_message(debug_chat_id, f"ERROR: {e} {repr(e)}", disable_notification=True)
            pprint(f'ERROR, wait 2 sec :{pformat(str(e)), pformat(repr(e))}')
            time.sleep(2)
        print('-'*10)
        pprint(msg)


bot = Bot(token)
MessageLoop(bot, bot.hdl).run_as_thread()

print("Bot running...")

while True:
    try:
        time.sleep(5)
        print('.', end='', flush=True)
    except Exception as e:
        bot.send_message(debug_chat_id, f'Script ended: {time.ctime()}')
        bot.send_message(debug_chat_id, f'{str(e)} {repr(e)}')
