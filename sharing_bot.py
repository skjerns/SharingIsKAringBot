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
    admin_chat_id = settings['admin_chat_id']
    group_chat_id = settings['group_chat_id']


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
        for new_member in map(Member, msg['new_chat_members']):
            if from_member==new_member:
                message = f'[{new_member.first} {new_member.last}](tg://user?id={new_member.id}) joined'
            else:
                message = f'[{from_member.first} {from_member.last}](tg://user?id={from_member.id}) invited '\
                          f'[{new_member.first} {new_member.last}](tg://user?id={new_member.id})'
            bot.sendMessage(admin_chat_id, message, disable_notification=True,
                            parse_mode = 'MarkdownV2')

    def forward_user_left_messages(self, msg):
        from_member = Member(msg['from'])
        old_member = Member(msg['left_chat_member'])
        if from_member==old_member:
            message = f'[{old_member.first} {old_member.last}](tg://user?id={old_member.id}) left'
        else:
            message = f'[{from_member.first} {from_member.last}](tg://user?id={from_member.id}) removed '\
                      f'[{old_member.first} {old_member.last}](tg://user?id={old_member.id})'
        bot.sendMessage(admin_chat_id, message, disable_notification=True,
                        parse_mode = 'MarkdownV2')


    def log(self):
        pass

    def hdl(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        msg_id = telepot.message_identifier(msg)

        try:
            if content_type=='new_chat_member':
                self.deleteMessage(msg_id)
                self.forward_new_user_messages(msg)
            elif content_type=='left_chat_member':
                self.deleteMessage(msg_id)
                self.forward_user_left_messages(msg)
            else:
                self.sendMessage(admin_chat_id, f'type: {content_type}\nchat: {chat_type}\n```\n{pformat(msg)}\n```',
                            parse_mode='MarkdownV2', disable_notification=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            pprint(f'ERROR, wait 2 sec :{pformat(str(e)), pformat(repr(e))}')
            time.sleep(2)
        pprint('-'*10 + '\n' + pformat(msg))


bot = Bot(token)
MessageLoop(bot, bot.hdl).run_as_thread()

print("Bot running...")

while True:
    time.sleep(5)
    print('.', end='', flush=True)
