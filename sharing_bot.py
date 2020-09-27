# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 13:10:53 2020

@author: skjerns
"""
import os
from telepot.loop import MessageLoop
import telepot
from pprint import pprint as print, pformat
import time
import json
import shelve
from sqlitedict import SqliteDict

token = 'xxxxxxx'

bot = telepot.Bot(token)


def get_user(user_id):
    
        
def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(msg)
    # if content_type=='new_chat_member':
        
    bot.sendMessage(chat_id, f'type: {content_type}')
    bot.sendMessage(chat_id, f'chat: {chat_type}')
    bot.sendMessage(chat_id, f'```\n{pformat(msg)}\n```', 
                    parse_mode='MarkdownV2')
    time.sleep(10)
    with SqliteDict('./my_db.json', encode=json.dumps, decode=json.loads) as db:
        db['test']    = 'test'     

    
MessageLoop(bot, handle).run_as_thread()