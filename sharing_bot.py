# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 13:10:53 2020

TODO: argparse input stuff

@author: skjerns
"""
from threading import Thread, Event
import os
from telepot.loop import MessageLoop
import telepot
import time
from pprint import pprint as pprint, pformat
import json
import requests
from requests.exceptions import ProxyError, ConnectionError, Timeout
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    print('Testing connection...')
    requests.get('http://api.telegram.org/')
    print('Success.')

except (ConnectionError, Timeout):
    try:
        print('Trying again with proxy...')
        proxies = {'http': 'http:proxy.server:3128'}
        requests.get('http://api.telegram.org/', proxies=proxies)
        telepot.api.set_proxy('http://proxy.server:3128')
        print('Success with proxy.')
    except ProxyError:
        print('Cannot connect to proxy.')


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


def check_namechange(bot=None, chat_id=None, delay=None, member=None):
    print(f"sending reminder in {delay}")
    Event().wait(delay)
    curr_member = Member(bot.getChatMember(group_chat_id, member.id).get('user'))
    prevname = str(member.first) + str(member.last)
    currname =  (str(curr_member.first) + str(curr_member.last))
    print(f"{prevname} == {currname} ? {prevname==currname}")
    if prevname != currname and not member.id in bot.warned_users:
        message = f'Changed name from <a href="tg://user?id={member.id}">{prevname}</a> to <a href="tg://user?id={member.id}">{currname}</a>, {delay//3600} hours after joining. Usually bots do this.'
        bot.send_message(admin_chat_id, message, disable_notification=True, parse_mode = 'html')
        bot.warned_users.append(member.id)
        

class Bot(telepot.Bot):

    warned_users = []

    def forward_new_user_messages(self, msg):
        from_member = Member(msg['from'])
        chat_name = msg['chat'].get('username')
        new_members = map(Member, msg['new_chat_members'])
        for new_member in new_members:
            if from_member==new_member:
                message = f'<a href="tg://user?id={new_member.id}">{new_member.first} {new_member.last}</a> joined {chat_name}'
            else:
                message = f'<a href="tg://user?id={from_member.id}">{from_member.first} {from_member.last}</a> added '\
                          f'<a href="tg://user?id={new_member.id}">{new_member.first} {new_member.last}</a> to {chat_name}'
            bot.send_message(admin_chat_id, message, disable_notification=True,
                            parse_mode = 'html')

            for i in [0.1] + list(range(1, 12, 2)):
                delay = i * 3600.0 # 6 hours afterwards
                wait_thread = Thread(target=check_namechange,
                       kwargs={'bot':bot,
                               'chat_id': admin_chat_id,
                               'delay': delay,
                               'member': new_member})
                wait_thread.start()


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
        text = 'Du hast gerade in der SharingIsKAring-Gruppe auf eine Nachricht geantwortet. ' \
               'Bitte benutze die Antworten-Funktion nur in Ausnahmefällen und schreibe sonst alles mit der Person in einem <b>privaten Chat</b>\n' \
               'Dies gilt insbesondere für <i>"Ich habe Interesse", "Danke"</i>, etc.\n\n' \
               'Bitte lösche deine Nachricht wieder und sende sie als <b>private Nachricht</b> (außer du denkst, sie ist wirklich für alle 500+ Leute relevant.). Piep-boop, ich bin ein Bot🤖.'
        self.send_message(from_member, text, parse_mode='html')


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

            elif chat_type=='supergroup' and  str(chat_id)==str(group_chat_id):

                if ('text' in msg) or ('photo' in msg):
                    pass

                elif content_type=='new_chat_member':
                    # remove new chat member message and forward to admin chat
                    self.deleteMessage(msg_id)
                    self.forward_new_user_messages(msg)

                elif content_type=='left_chat_member':
                    # remove chat member deleted message and forward to admin chat
                    self.deleteMessage(msg_id)
                    self.forward_user_left_messages(msg)

                elif content_type=='text' and ('reply_to_message' in msg):
                    # remind users not to answer in group
                    self.send_not_answer_reminder(msg)

            else:
                # if none of the above: send debug message.
                self.send_message(debug_chat_id, f'No action taken.\ntype: {content_type}\nchat: {chat_type}\n```\n{pformat(msg)}\n```',
                            parse_mode='MarkdownV2', disable_notification=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_message(debug_chat_id, f"ERROR: {e} {repr(e)}", disable_notification=True)
            pprint(f'ERROR, wait 2 sec :{pformat(str(e)), pformat(repr(e))}')
            time.sleep(2)
        print('-'*10)
        try:
            pprint(msg)
        except:
            print(msg)

#%%
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
